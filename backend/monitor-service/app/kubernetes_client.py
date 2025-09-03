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
    
    async def _create_namespace(self, namespace: str, labels: Dict[str, str] = None, annotations: Dict[str, str] = None) -> bool:
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
        """Appliquer les manifests K8s via kubectl apply - approche unifiée"""
        results = {}
        
        # Ordre d'application des manifests (dépendances K8s)
        apply_order = ["namespace", "configmap", "secret", "pvc", "deployment", "service", "ingress", "hpa"]
        
        for manifest_type in apply_order:
            if manifest_type in manifests:
                print(f"Applying {manifest_type}...")
                try:
                    success = await self._apply_manifest_yaml(manifests[manifest_type])
                    results[manifest_type] = success
                    
                    if success:
                        print(f"{manifest_type} applied successfully")
                    else:
                        print(f"{manifest_type} failed")
                        
                except Exception as e:
                    print(f"Error applying {manifest_type}: {e}")
                    results[manifest_type] = False
        
        return results
    
    async def _apply_manifest_yaml(self, manifest_yaml: str) -> bool:
        """Méthode générique pour appliquer n'importe quel manifest K8s via kubectl"""
        try:
            # Écrire le manifest dans un fichier temporaire
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(manifest_yaml)
                temp_file = f.name
            
            try:
                # Appliquer via kubectl (plus robuste que l'API directe)
                result = subprocess.run(
                    ['kubectl', 'apply', '-f', temp_file],
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                print(f"kubectl output: {result.stdout.strip()}")
                return True
                
            except subprocess.CalledProcessError as e:
                print(f"kubectl apply failed: {e.stderr}")
                return False
            
        except Exception as e:
            print(f"Error in _apply_manifest_yaml: {e}")
            return False
        
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.unlink(temp_file)
            except:
                pass
    
    
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
    
    async def _delete_resource(self, resource_type: str, name: str, namespace: str) -> bool:
        """Méthode générique pour supprimer une ressource K8s via kubectl"""
        try:
            # Utiliser kubectl delete directement (plus fiable que l'API)
            result = subprocess.run([
                'kubectl', 'delete', resource_type, name, 
                '-n', namespace, '--ignore-not-found=true'
            ], capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                if result.stdout.strip():
                    print(f"kubectl delete output: {result.stdout.strip()}")
                return True
            else:
                print(f"kubectl delete failed for {resource_type} {name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error deleting {resource_type} {name}: {e}")
            return False
    
    async def delete_deployment_resources(self, service_name: str, namespace: str) -> Dict[str, bool]:
        """Supprimer toutes les ressources liées à un service par noms réels K8s"""
        results = {}
        
        # Convention de nommage NoKube basée sur service_name
        app_name = service_name.lower()
        
        # Liste des ressources potentiellement créées (ordre de suppression important)
        # Supprimer dans l'ordre inverse de création pour éviter les dépendances
        resource_names = [
            ("ingress", f"{app_name}-ingress"),
            ("hpa", f"{app_name}-hpa"),
            ("service", f"{app_name}-service"),
            ("deployment", app_name),
            ("configmap", f"{app_name}-config"),
            ("secret", f"{app_name}-secret"),
            ("pvc", f"{app_name}-pvc")
        ]
        
        print(f"Deleting resources for service '{service_name}' (app_name: {app_name}) in namespace {namespace}")
        
        # Supprimer chaque ressource par son nom réel
        successful_deletions = []
        failed_deletions = []
        
        for resource_type, resource_name in resource_names:
            print(f"Attempting to delete {resource_type}: {resource_name}")
            success = await self._delete_resource(resource_type, resource_name, namespace)
            results[f"{resource_type}/{resource_name}"] = success
            
            if success:
                successful_deletions.append(f"{resource_type}/{resource_name}")
                print(f"✅ Successfully deleted {resource_type}: {resource_name}")
            else:
                failed_deletions.append(f"{resource_type}/{resource_name}")
                print(f"❌ Failed to delete {resource_type}: {resource_name}")
        
        # Statistiques finales
        total_attempted = len(resource_names)
        total_successful = len(successful_deletions)
        
        print(f"Deletion summary: {total_successful}/{total_attempted} resources deleted successfully")
        if successful_deletions:
            print(f"Successful deletions: {successful_deletions}")
        if failed_deletions:
            print(f"Failed deletions: {failed_deletions}")
        
        # Ajouter des métadonnées au résultat
        results["_summary"] = {
            "total_attempted": total_attempted,
            "total_successful": total_successful,
            "total_failed": len(failed_deletions),
            "successful_deletions": successful_deletions,
            "failed_deletions": failed_deletions
        }
        
        return results
    

# Instance globale du client
k8s_client = KubernetesClient()