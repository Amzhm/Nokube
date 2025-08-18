from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum

class DeploymentStatus(str, Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"

class ServiceType(str, Enum):
    WEB = "web"           # Applications web exposées (avec Ingress)
    API = "api"           # Services API internes (ClusterIP seulement)
    WORKER = "worker"     # Workers/jobs sans réseau

class ExposureType(str, Enum):
    NONE = "none"         # Pas d'exposition (workers)
    INTERNAL = "internal" # Seulement dans le cluster
    EXTERNAL = "external" # Exposé via Ingress sur Internet

# Input schemas
class DeployRequest(BaseModel):
    """Requête de déploiement avec configuration complète utilisateur"""
    
    # Informations projet et utilisateur
    project_id: int
    project_name: str            # Nom du projet (choix utilisateur, ex: "ecommerce-app")
    username: str                # Nom utilisateur (ex: "testuser2")
    service_name: str            # Nom du service dans ce projet (ex: "frontend")
    display_name: str            # Nom affiché (ex: "Frontend React")
    description: Optional[str] = None
    image_name: str              # ghcr.io/amzhm/user-project-service:tag
    
    # Configuration du service
    service_type: ServiceType = ServiceType.WEB
    exposure_type: ExposureType = ExposureType.EXTERNAL
    
    # Configuration ports (FLUX: Internet:80 → Ingress → Service:8000 → Container:container_port)
    container_port: int = 3000         # Port d'écoute dans le container (choix utilisateur)
    service_port: int = 8000          # Port du service K8s (standardisé NoKube)
    
    # Configuration des ressources (choix utilisateur)
    replicas: int = 2
    cpu_request: str = "100m"         # CPU demandé (ex: 100m, 0.5, 1)
    cpu_limit: str = "500m"           # CPU limite
    memory_request: str = "128Mi"     # RAM demandée (ex: 128Mi, 1Gi)
    memory_limit: str = "512Mi"       # RAM limite
    
    # Configuration réseau (si exposé)
    custom_domain: Optional[str] = None    # Domaine personnalisé
    custom_path: Optional[str] = None      # Chemin personnalisé (ex: /api, /app)
    enable_https: bool = False             # Certificat SSL automatique
    
    # Variables d'environnement
    env_vars: Dict[str, str] = {}          # Variables publiques
    secrets: Dict[str, str] = {}           # Variables sensibles (base64)
    
    # Configuration santé (configurables par utilisateur via frontend)
    health_check_enabled: bool = True                      # Activer/désactiver tous les health checks
    liveness_check_path: Optional[str] = "/health"         # Endpoint liveness ou None pour désactiver
    readiness_check_path: Optional[str] = "/ready"         # Endpoint readiness ou None pour désactiver
    health_check_port: Optional[int] = None                # Port health check (défaut: container_port)
    liveness_initial_delay: int = 30                       # Délai avant premier liveness check (secondes)
    readiness_initial_delay: int = 5                       # Délai avant premier readiness check (secondes)
    health_check_period: int = 10                          # Fréquence des checks (secondes)
    health_check_timeout: int = 5                          # Timeout par check (secondes)
    health_check_failure_threshold: int = 3                # Nombre d'échecs avant restart/not ready
    
    # Stockage persistant (optionnel)
    storage_size: Optional[str] = None     # Ex: "1Gi", "500Mi"
    storage_path: Optional[str] = None     # Point de montage (ex: /data, /uploads)
    
    # Auto-scaling (optionnel)
    enable_autoscaling: bool = False
    min_replicas: Optional[int] = 1
    max_replicas: Optional[int] = 10
    target_cpu_percent: Optional[int] = 70

class DeployResponse(BaseModel):
    """Réponse après déploiement"""
    deployment_id: str
    project_id: int
    service_name: str
    status: DeploymentStatus
    image_name: str
    created_at: datetime
    manifests_generated: List[str]  # Liste des types de manifests générés
    access_url: Optional[str] = None  # URL d'accès si web service

class DeploymentStatusResponse(BaseModel):
    """Status d'un déploiement"""
    deployment_id: str
    project_id: int
    service_name: str
    status: DeploymentStatus
    image_name: str
    replicas_ready: int
    replicas_total: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    access_url: Optional[str] = None
    
class ManifestResponse(BaseModel):
    """Manifests générés"""
    deployment_id: str
    manifests: Dict[str, str]  # type -> yaml content

# Health check schemas
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    kubernetes_connected: bool
    
class ReadyResponse(BaseModel):
    status: str
    kubernetes_available: bool
    namespace_accessible: bool