import asyncio
import yaml
import subprocess
from typing import Dict, List, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import tempfile
import os

class KubernetesClient:
    """Client Kubernetes pour déployer et gérer les manifests"""
    
    def __init__(self):
        """Initialiser le client Kubernetes"""
        try:
            # Mode test - ne pas initialiser K8s
            if os.getenv("TESTING") == "true":
                print("Running in TEST mode - K8s client disabled")
                self.v1 = None
                self.apps_v1 = None
                self.networking_v1 = None
                self.autoscaling_v2 = None
                return
                
            # Charger la config K8s (in-cluster ou locale)
            try:
                config.load_incluster_config()
                print("Loaded in-cluster Kubernetes config")
            except:
                config.load_kube_config()
                print("Loaded local Kubernetes config")
                
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            self.autoscaling_v2 = client.AutoscalingV2Api()
            
        except Exception as e:
            print(f"Failed to initialize Kubernetes client: {e}")
            raise e
    
    async def test_connection(self) -> bool:
        """Tester la connexion au cluster Kubernetes"""
        try:
            # Test simple : lister les nodes
            nodes = self.v1.list_node()
            print(f"Connected to K8s cluster with {len(nodes.items)} nodes")
            return True
        except Exception as e:
            print(f"Kubernetes connection test failed: {e}")
            return False
    
    async def namespace_exists(self, namespace: str) -> bool:
        """Vérifier si un namespace existe"""
        try:
            self.v1.read_namespace(name=namespace)
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            raise e
    
    async def create_namespace(self, namespace: str, labels: Dict[str, str] = None, annotations: Dict[str, str] = None) -> bool:
        """Créer un namespace avec labels et annotations"""
        try:
            if await self.namespace_exists(namespace):
                print(f"Namespace {namespace} already exists")
                return True
                
            ns_manifest = client.V1Namespace(
                metadata=client.V1ObjectMeta(
                    name=namespace,
                    labels=labels or {},
                    annotations=annotations or {}
                )
            )
            
            self.v1.create_namespace(body=ns_manifest)
            print(f"Created namespace: {namespace}")
            return True
            
        except ApiException as e:
            print(f"Failed to create namespace {namespace}: {e}")
            return False
    
    async def apply_manifests(self, manifests: Dict[str, str], namespace: str) -> Dict[str, bool]:
        """Appliquer les manifests K8s dans l'ordre correct"""
        results = {}
        
        # Ordre d'application des manifests
        apply_order = ["namespace", "configmap", "secret", "pvc", "deployment", "service", "ingress", "hpa"]
        
        for manifest_type in apply_order:
            if manifest_type in manifests:
                try:
                    success = await self._apply_single_manifest(
                        manifest_type, 
                        manifests[manifest_type], 
                        namespace
                    )
                    results[manifest_type] = success
                    
                    if success:
                        print(f"✅ Applied {manifest_type}")
                    else:
                        print(f"❌ Failed to apply {manifest_type}")
                        
                except Exception as e:
                    print(f"❌ Error applying {manifest_type}: {e}")
                    results[manifest_type] = False
        
        return results
    
    async def _apply_single_manifest(self, manifest_type: str, manifest_yaml: str, namespace: str) -> bool:
        """Appliquer un manifest individuel"""
        try:
            # Parser le YAML
            manifest_dict = yaml.safe_load(manifest_yaml)
            
            if manifest_type == "namespace":
                return await self._apply_namespace(manifest_dict)
            elif manifest_type == "configmap":
                return await self._apply_configmap(manifest_dict, namespace)
            elif manifest_type == "secret":
                return await self._apply_secret(manifest_dict, namespace)
            elif manifest_type == "pvc":
                return await self._apply_pvc(manifest_dict, namespace)
            elif manifest_type == "deployment":
                return await self._apply_deployment(manifest_dict, namespace)
            elif manifest_type == "service":
                return await self._apply_service(manifest_dict, namespace)
            elif manifest_type == "ingress":
                return await self._apply_ingress(manifest_dict, namespace)
            elif manifest_type == "hpa":
                return await self._apply_hpa(manifest_dict, namespace)
            else:
                print(f"Unknown manifest type: {manifest_type}")
                return False
                
        except Exception as e:
            print(f"Error applying {manifest_type}: {e}")
            return False
    
    async def _apply_namespace(self, manifest: dict) -> bool:
        """Appliquer un Namespace"""
        try:
            namespace_name = manifest['metadata']['name']
            labels = manifest['metadata'].get('labels', {})
            annotations = manifest['metadata'].get('annotations', {})
            
            return await self.create_namespace(namespace_name, labels, annotations)
        except Exception as e:
            print(f"Error creating namespace: {e}")
            return False
    
    async def _apply_configmap(self, manifest: dict, namespace: str) -> bool:
        """Appliquer un ConfigMap"""
        try:
            configmap = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(
                    name=manifest['metadata']['name'],
                    namespace=namespace,
                    labels=manifest['metadata'].get('labels', {}),
                    annotations=manifest['metadata'].get('annotations', {})
                ),
                data=manifest.get('data', {})
            )
            
            # Essayer de créer, si existe déjà, remplacer
            try:
                self.v1.create_namespaced_config_map(namespace=namespace, body=configmap)
            except ApiException as e:
                if e.status == 409:  # Already exists
                    self.v1.replace_namespaced_config_map(
                        name=manifest['metadata']['name'],
                        namespace=namespace, 
                        body=configmap
                    )
                else:
                    raise e
            
            return True
        except Exception as e:
            print(f"Error applying ConfigMap: {e}")
            return False
    
    async def _apply_secret(self, manifest: dict, namespace: str) -> bool:
        """Appliquer un Secret"""
        try:
            secret = client.V1Secret(
                metadata=client.V1ObjectMeta(
                    name=manifest['metadata']['name'],
                    namespace=namespace,
                    labels=manifest['metadata'].get('labels', {}),
                    annotations=manifest['metadata'].get('annotations', {})
                ),
                type=manifest.get('type', 'Opaque'),
                data=manifest.get('data', {})
            )
            
            try:
                self.v1.create_namespaced_secret(namespace=namespace, body=secret)
            except ApiException as e:
                if e.status == 409:  # Already exists
                    self.v1.replace_namespaced_secret(
                        name=manifest['metadata']['name'],
                        namespace=namespace,
                        body=secret
                    )
                else:
                    raise e
            
            return True
        except Exception as e:
            print(f"Error applying Secret: {e}")
            return False
    
    async def _apply_deployment(self, manifest: dict, namespace: str) -> bool:
        """Appliquer un Deployment"""
        try:
            # Utiliser kubectl apply pour les Deployments (plus robuste)
            return await self._kubectl_apply_manifest(manifest, namespace)
        except Exception as e:
            print(f"Error applying Deployment: {e}")
            return False
    
    async def _apply_service(self, manifest: dict, namespace: str) -> bool:
        """Appliquer un Service"""
        try:
            return await self._kubectl_apply_manifest(manifest, namespace)
        except Exception as e:
            print(f"Error applying Service: {e}")
            return False
    
    async def _apply_ingress(self, manifest: dict, namespace: str) -> bool:
        """Appliquer un Ingress"""
        try:
            return await self._kubectl_apply_manifest(manifest, namespace)
        except Exception as e:
            print(f"Error applying Ingress: {e}")
            return False
    
    async def _apply_pvc(self, manifest: dict, namespace: str) -> bool:
        """Appliquer un PVC"""
        try:
            return await self._kubectl_apply_manifest(manifest, namespace)
        except Exception as e:
            print(f"Error applying PVC: {e}")
            return False
    
    async def _apply_hpa(self, manifest: dict, namespace: str) -> bool:
        """Appliquer un HPA"""
        try:
            return await self._kubectl_apply_manifest(manifest, namespace)
        except Exception as e:
            print(f"Error applying HPA: {e}")
            return False
    
    async def _kubectl_apply_manifest(self, manifest: dict, namespace: str) -> bool:
        """Utiliser kubectl apply pour appliquer un manifest"""
        try:
            # Créer un fichier temporaire avec le manifest
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(manifest, f)
                temp_file = f.name
            
            # Appliquer avec kubectl
            cmd = ["kubectl", "apply", "-f", temp_file, "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Nettoyer le fichier temporaire
            os.unlink(temp_file)
            
            if result.returncode == 0:
                print(f"kubectl apply successful: {result.stdout.strip()}")
                return True
            else:
                print(f"kubectl apply failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error with kubectl apply: {e}")
            return False
    
    async def get_deployment_status(self, deployment_name: str, namespace: str) -> Dict:
        """Récupérer le statut d'un déploiement"""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace
            )
            
            return {
                "replicas_total": deployment.spec.replicas or 0,
                "replicas_ready": deployment.status.ready_replicas or 0,
                "replicas_available": deployment.status.available_replicas or 0,
                "conditions": [
                    {
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message
                    }
                    for condition in (deployment.status.conditions or [])
                ]
            }
            
        except ApiException as e:
            if e.status == 404:
                return {"error": "Deployment not found"}
            raise e
    
    async def delete_namespace(self, namespace: str) -> bool:
        """Supprimer un namespace complet (undeploy projet)"""
        try:
            self.v1.delete_namespace(name=namespace)
            print(f"Deleted namespace: {namespace}")
            return True
        except ApiException as e:
            if e.status == 404:
                print(f"Namespace {namespace} already deleted")
                return True
            print(f"Error deleting namespace {namespace}: {e}")
            return False

# Instance globale du client
k8s_client = KubernetesClient()