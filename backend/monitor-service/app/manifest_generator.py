import yaml
import re
from jinja2 import Template
from typing import Dict, List, Optional
from app.schemas import DeployRequest, ServiceType, ExposureType
from app.config import settings

class KubernetesManifestGenerator:
    """Générateur de manifests Kubernetes avec namespace par projet et DNS path-based"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def generate_manifests(self, deploy_request: DeployRequest, deployment_id: str) -> Dict[str, str]:
        """Génère tous les manifests nécessaires avec isolation par namespace projet"""
        
        manifests = {}
        
        # Variables communes pour tous les templates
        template_vars = self._prepare_template_vars(deploy_request, deployment_id)
        
        # 0. Namespace (toujours généré en premier)
        manifests["namespace"] = self._generate_namespace(template_vars)
        
        # 1. Deployment (toujours requis)
        manifests["deployment"] = self._generate_deployment(template_vars)
        
        # 2. Service (sauf pour WORKER sans réseau)
        if deploy_request.exposure_type != ExposureType.NONE:
            manifests["service"] = self._generate_service(template_vars)
        
        # 3. Ingress (seulement si exposé externellement)
        if deploy_request.exposure_type == ExposureType.EXTERNAL:
            manifests["ingress"] = self._generate_ingress(template_vars)
        
        # 4. ConfigMap (si variables d'environnement publiques)
        if deploy_request.env_vars:
            manifests["configmap"] = self._generate_configmap(template_vars)
        
        # 5. Secret (si variables sensibles)
        if deploy_request.secrets:
            manifests["secret"] = self._generate_secret(template_vars)
        
        # 6. PersistentVolumeClaim (si stockage demandé)
        if deploy_request.storage_size:
            manifests["pvc"] = self._generate_pvc(template_vars)
        
        # 7. HorizontalPodAutoscaler (si autoscaling activé)
        if deploy_request.enable_autoscaling:
            manifests["hpa"] = self._generate_hpa(template_vars)
        
        return manifests
    
    def _generate_namespace_name(self, username: str, project_name: str) -> str:
        """Génère le nom du namespace : username-project-name (compatible DNS K8s)"""
        # Normaliser pour être compatible DNS K8s (minuscules, - autorisés)
        safe_username = re.sub(r'[^a-zA-Z0-9-]', '', username.lower())
        safe_project = re.sub(r'[^a-zA-Z0-9-]', '', project_name.lower())
        namespace = f"{safe_username}-{safe_project}"
        
        # Limitation longueur K8s (63 caractères max)
        if len(namespace) > 63:
            namespace = namespace[:63].rstrip('-')
            
        return namespace
    
    def _prepare_template_vars(self, deploy_request: DeployRequest, deployment_id: str) -> Dict:
        """Prépare les variables pour les templates avec DNS path-based"""
        
        # Génération du namespace projet isolé
        namespace = self._generate_namespace_name(deploy_request.username, deploy_request.project_name)
        
        # Génération du nom de l'app (service dans le namespace)
        app_name = deploy_request.service_name.lower()
        
        # URL externe (path-based) : nokube.com/user/projet/service
        access_url = None
        if deploy_request.exposure_type == ExposureType.EXTERNAL:
            domain = deploy_request.custom_domain or settings.DEFAULT_HOST
            if deploy_request.custom_path:
                path = deploy_request.custom_path
            else:
                # Path standard : /username/project-name/service-name
                path = f"/{deploy_request.username}/{deploy_request.project_name}/{deploy_request.service_name}"
            
            protocol = "https" if deploy_request.enable_https else "http"
            access_url = f"{protocol}://{domain}{path}"
        
        # URL interne cluster (DNS Kubernetes) : service-name-service:8000
        internal_service_url = f"http://{app_name}-service:{deploy_request.service_port}"
        
        return {
            # Métadonnées projet
            "deployment_id": deployment_id,
            "namespace": namespace,
            "project_id": deploy_request.project_id,
            "project_name": deploy_request.project_name,
            "username": deploy_request.username,
            
            # Service
            "app_name": app_name,
            "service_name": deploy_request.service_name,
            "display_name": deploy_request.display_name,
            "description": deploy_request.description or f"{deploy_request.service_name} service",
            
            # Image et déploiement
            "image_name": deploy_request.image_name,
            "replicas": deploy_request.replicas,
            
            # Configuration ports - FLUX: nokube.com:80 → Ingress → Service:8000 → Container:container_port
            "container_port": deploy_request.container_port,
            "service_port": deploy_request.service_port,
            "health_check_port": deploy_request.health_check_port or deploy_request.container_port,
            
            # Configuration ressources
            "cpu_request": deploy_request.cpu_request,
            "cpu_limit": deploy_request.cpu_limit,
            "memory_request": deploy_request.memory_request,
            "memory_limit": deploy_request.memory_limit,
            
            # Configuration réseau
            "service_type": deploy_request.service_type,
            "exposure_type": deploy_request.exposure_type,
            "domain": deploy_request.custom_domain or settings.DEFAULT_HOST,
            "path": deploy_request.custom_path or f"/{deploy_request.username}/{deploy_request.project_name}/{deploy_request.service_name}",
            "enable_https": deploy_request.enable_https,
            "ingress_class": settings.DEFAULT_INGRESS_CLASS,
            "access_url": access_url,
            "internal_service_url": internal_service_url,
            
            # Health checks (nouveaux paramètres configurables)
            "health_check_enabled": deploy_request.health_check_enabled,
            "liveness_check_path": deploy_request.liveness_check_path,
            "readiness_check_path": deploy_request.readiness_check_path,
            "health_check_port": deploy_request.health_check_port or deploy_request.container_port,
            "liveness_initial_delay": deploy_request.liveness_initial_delay,
            "readiness_initial_delay": deploy_request.readiness_initial_delay,
            "health_check_period": deploy_request.health_check_period,
            "health_check_timeout": deploy_request.health_check_timeout,
            "health_check_failure_threshold": deploy_request.health_check_failure_threshold,
            
            # Variables et secrets
            "env_vars": deploy_request.env_vars,
            "secrets": deploy_request.secrets,
            "has_env_vars": bool(deploy_request.env_vars),
            "has_secrets": bool(deploy_request.secrets),
            
            # Stockage
            "storage_size": deploy_request.storage_size,
            "storage_path": deploy_request.storage_path,
            "has_storage": bool(deploy_request.storage_size),
            
            # Autoscaling
            "enable_autoscaling": deploy_request.enable_autoscaling,
            "min_replicas": deploy_request.min_replicas or 1,
            "max_replicas": deploy_request.max_replicas or 10,
            "target_cpu_percent": deploy_request.target_cpu_percent or 70,
        }
    
    def _generate_namespace(self, vars: Dict) -> str:
        """Génère le manifest Namespace"""
        template = self.templates["namespace"]
        return template.render(**vars)
    
    def _generate_deployment(self, vars: Dict) -> str:
        """Génère le manifest Deployment"""
        template = self.templates["deployment"]
        return template.render(**vars)
    
    def _generate_service(self, vars: Dict) -> str:
        """Génère le manifest Service"""
        template = self.templates["service"]
        return template.render(**vars)
    
    def _generate_ingress(self, vars: Dict) -> str:
        """Génère le manifest Ingress"""
        template = self.templates["ingress"]
        return template.render(**vars)
    
    def _generate_configmap(self, vars: Dict) -> str:
        """Génère le manifest ConfigMap"""
        template = self.templates["configmap"]
        return template.render(**vars)
    
    def _generate_secret(self, vars: Dict) -> str:
        """Génère le manifest Secret"""
        template = self.templates["secret"]
        return template.render(**vars)
    
    def _generate_pvc(self, vars: Dict) -> str:
        """Génère le manifest PersistentVolumeClaim"""
        template = self.templates["pvc"]
        return template.render(**vars)
    
    def _generate_hpa(self, vars: Dict) -> str:
        """Génère le manifest HorizontalPodAutoscaler"""
        template = self.templates["hpa"]
        return template.render(**vars)
    
    def _load_templates(self) -> Dict[str, Template]:
        """Charge les templates Jinja2 avec DNS path-based"""
        
        # Template Namespace - Créé automatiquement pour chaque projet
        namespace_template = Template("""
apiVersion: v1
kind: Namespace
metadata:
  name: {{ namespace }}
  labels:
    project-id: "{{ project_id }}"
    project-name: {{ project_name }}
    username: {{ username }}
    managed-by: nokube
  annotations:
    nokube.io/project-name: "{{ project_name }}"
    nokube.io/username: "{{ username }}"
    nokube.io/created-by: "monitor-service"
    nokube.io/access-pattern: "path-based"
""".strip())

        # Template Deployment
        deployment_template = Template("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ app_name }}
  namespace: {{ namespace }}
  labels:
    app: {{ app_name }}
    project-id: "{{ project_id }}"
    project-name: {{ project_name }}
    service: {{ service_name }}
    deployment-id: {{ deployment_id }}
    username: {{ username }}
  annotations:
    description: "{{ description }}"
    nokube.io/display-name: "{{ display_name }}"
    nokube.io/access-url: "{{ access_url or 'internal-only' }}"
    nokube.io/internal-url: "{{ internal_service_url }}"
spec:
  replicas: {{ replicas }}
  selector:
    matchLabels:
      app: {{ app_name }}
  template:
    metadata:
      labels:
        app: {{ app_name }}
        project-id: "{{ project_id }}"
        project-name: {{ project_name }}
        service: {{ service_name }}
        username: {{ username }}
    spec:
      imagePullSecrets:
      - name: ghcr-secret
      containers:
      - name: {{ service_name }}
        image: {{ image_name }}
        ports:
        - name: http
          containerPort: {{ container_port }}
          protocol: TCP
        resources:
          requests:
            cpu: {{ cpu_request }}
            memory: {{ memory_request }}
          limits:
            cpu: {{ cpu_limit }}
            memory: {{ memory_limit }}
        {% if health_check_enabled and liveness_check_path %}
        livenessProbe:
          httpGet:
            path: {{ liveness_check_path }}
            port: {{ health_check_port }}
          initialDelaySeconds: {{ liveness_initial_delay }}
          periodSeconds: {{ health_check_period }}
          timeoutSeconds: {{ health_check_timeout }}
          failureThreshold: {{ health_check_failure_threshold }}
        {% endif %}
        {% if health_check_enabled and readiness_check_path %}
        readinessProbe:
          httpGet:
            path: {{ readiness_check_path }}
            port: {{ health_check_port }}
          initialDelaySeconds: {{ readiness_initial_delay }}
          periodSeconds: {{ health_check_period }}
          timeoutSeconds: {{ health_check_timeout }}
          failureThreshold: {{ health_check_failure_threshold }}
        {% endif %}
        {% if has_env_vars or has_secrets %}
        env:
        {% if has_env_vars %}
        envFrom:
        - configMapRef:
            name: {{ app_name }}-config
        {% endif %}
        {% if has_secrets %}
        - secretRef:
            name: {{ app_name }}-secret
        {% endif %}
        {% endif %}
        {% if has_storage %}
        volumeMounts:
        - name: {{ app_name }}-storage
          mountPath: {{ storage_path }}
        {% endif %}
      {% if has_storage %}
      volumes:
      - name: {{ app_name }}-storage
        persistentVolumeClaim:
          claimName: {{ app_name }}-pvc
      {% endif %}
""".strip())

        # Template Service avec DNS interne
        service_template = Template("""
apiVersion: v1
kind: Service
metadata:
  name: {{ app_name }}-service
  namespace: {{ namespace }}
  labels:
    app: {{ app_name }}
    project-id: "{{ project_id }}"
    project-name: {{ project_name }}
    service: {{ service_name }}
    username: {{ username }}
  annotations:
    nokube.io/internal-url: "{{ internal_service_url }}"
    nokube.io/port-mapping: "service:{{ service_port }} -> container:{{ container_port }}"
spec:
  selector:
    app: {{ app_name }}
  ports:
  - name: http
    port: {{ service_port }}         # Port du service (standardisé 8000)
    targetPort: {{ container_port }} # Port du container (choix utilisateur)
    protocol: TCP
  type: ClusterIP
""".strip())

        # Template Ingress avec path-based routing
        ingress_template = Template("""
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ app_name }}-ingress
  namespace: {{ namespace }}
  labels:
    app: {{ app_name }}
    project-id: "{{ project_id }}"
    project-name: {{ project_name }}
    service: {{ service_name }}
    username: {{ username }}
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$1
    nginx.ingress.kubernetes.io/use-regex: "true"
    {% if enable_https %}
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    {% endif %}
    nokube.io/access-url: "{{ access_url }}"
    nokube.io/routing-pattern: "path-based"
spec:
  ingressClassName: {{ ingress_class }}
  {% if enable_https %}
  tls:
  - hosts:
    - {{ domain }}
    secretName: {{ app_name }}-tls
  {% endif %}
  rules:
  - host: {{ domain }}
    http:
      paths:
      - path: {% if path == "/" %}/(.*){%- else %}{{ path }}/(.*){% endif %}
        pathType: Prefix
        backend:
          service:
            name: {{ app_name }}-service
            port:
              number: {{ service_port }}  # Port du service (8000)
""".strip())

        # Template ConfigMap avec documentation DNS
        configmap_template = Template("""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ app_name }}-config
  namespace: {{ namespace }}
  labels:
    app: {{ app_name }}
    project-id: "{{ project_id }}"
    project-name: {{ project_name }}
    service: {{ service_name }}
    username: {{ username }}
  annotations:
    nokube.io/dns-info: "Internal services accessible via: <service-name>-service:{{ service_port }}"
data:
{% for key, value in env_vars.items() %}
  {{ key }}: "{{ value }}"
{% endfor %}
  # DNS Internal Services (auto-generated)
  INTERNAL_SERVICE_URL: "{{ internal_service_url }}"
  SERVICE_NAMESPACE: "{{ namespace }}"
""".strip())

        # Template Secret
        secret_template = Template("""
apiVersion: v1
kind: Secret
metadata:
  name: {{ app_name }}-secret
  namespace: {{ namespace }}
  labels:
    app: {{ app_name }}
    project-id: "{{ project_id }}"
    project-name: {{ project_name }}
    service: {{ service_name }}
    username: {{ username }}
type: Opaque
data:
{% for key, value in secrets.items() %}
  {{ key }}: {{ value }}  # Base64 encoded by user
{% endfor %}
""".strip())

        # Template PVC
        pvc_template = Template("""
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ app_name }}-pvc
  namespace: {{ namespace }}
  labels:
    app: {{ app_name }}
    project-id: "{{ project_id }}"
    project-name: {{ project_name }}
    service: {{ service_name }}
    username: {{ username }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ storage_size }}
  storageClassName: local-path
""".strip())

        # Template HPA
        hpa_template = Template("""
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ app_name }}-hpa
  namespace: {{ namespace }}
  labels:
    app: {{ app_name }}
    project-id: "{{ project_id }}"
    project-name: {{ project_name }}
    service: {{ service_name }}
    username: {{ username }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ app_name }}
  minReplicas: {{ min_replicas }}
  maxReplicas: {{ max_replicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ target_cpu_percent }}
""".strip())

        return {
            "namespace": namespace_template,
            "deployment": deployment_template,
            "service": service_template,
            "ingress": ingress_template,
            "configmap": configmap_template,
            "secret": secret_template,
            "pvc": pvc_template,
            "hpa": hpa_template
        }

# Instance globale du générateur
manifest_generator = KubernetesManifestGenerator()