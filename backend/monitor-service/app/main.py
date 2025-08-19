from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from datetime import datetime
from typing import List, Optional, Dict
import asyncio
import uuid

from app.config import settings
from app.schemas import (
    DeployRequest, DeployResponse, DeploymentStatusResponse,
    DeploymentStatus, ManifestResponse,
    HealthResponse, ReadyResponse
)
from app.manifest_generator import manifest_generator
from app.kubernetes_client import k8s_client
from app.database import (
    db, init_db, create_deployment, get_deployment, update_deployment_status,
    list_deployments_by_project, count_deployments, count_deployments_by_status
)
from app.middleware import LoggingMiddleware
from fastapi.middleware.cors import CORSMiddleware

# Création de l'application FastAPI
app = FastAPI(
    title=settings.TITLE,
    description=settings.DESCRIPTION,
    version=settings.VERSION
)

# Ajout des middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Events de cycle de vie
@app.on_event("startup")
async def startup():
    """Initialiser la connexion DB au démarrage"""
    await db.connect()
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    """Fermer la connexion DB à l'arrêt"""
    await db.disconnect()

# Note: Déploiements maintenant stockés dans PostgreSQL (plus de stockage en mémoire)
manifests_storage: Dict[str, Dict[str, str]] = {}  # deployment_id -> manifests

@app.get("/")
async def root(x_user: str = Header(...)):
    """Endpoint racine du Monitor Service"""
    return {
        "service": "NoKube Monitor Service",
        "version": settings.VERSION,
        "status": "running",
        "timestamp": datetime.now(),
        "features": [
            "Kubernetes manifest generation",
            "Path-based DNS routing", 
            "Namespace isolation per project",
            "Auto-scaling support",
            "Persistent storage management"
        ],
        "endpoints": {
            "health": "/health",
            "deploy": "/deploy", 
            "manifests": "/manifests/{deployment_id}",
            "status": "/deployments/{deployment_id}",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check du Monitor Service"""
    kubernetes_connected = await k8s_client.test_connection()
    
    return HealthResponse(
        status="healthy" if kubernetes_connected else "unhealthy",
        service="monitor-service",
        timestamp=datetime.now(),
        kubernetes_connected=kubernetes_connected
    )

@app.get("/ready", response_model=ReadyResponse)
async def ready_check():
    """Readiness check du Monitor Service"""
    kubernetes_available = await k8s_client.test_connection()
    
    # Test création namespace temporaire pour vérifier permissions
    namespace_accessible = True
    try:
        test_ns = "nokube-readiness-test"
        await k8s_client.create_namespace(test_ns, {"test": "readiness"})
        await k8s_client.delete_namespace(test_ns)
    except Exception:
        namespace_accessible = False
    
    status = "ready" if (kubernetes_available and namespace_accessible) else "not_ready"
    
    return ReadyResponse(
        status=status,
        kubernetes_available=kubernetes_available,
        namespace_accessible=namespace_accessible
    )

@app.post("/deploy", response_model=DeployResponse)
async def deploy_service(
    deploy_request: DeployRequest,
    background_tasks: BackgroundTasks,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Déployer un service avec génération et application des manifests K8s"""
    
    try:
        # Générer un ID unique pour ce déploiement
        deployment_id = str(uuid.uuid4())
        
        # Vérifier cohérence utilisateur (sécurité)
        if deploy_request.username != x_user:
            raise HTTPException(
                status_code=403, 
                detail=f"Username mismatch: {deploy_request.username} != {x_user}"
            )
        
        # Générer les manifests K8s
        print(f"Generating manifests for {deploy_request.username}/{deploy_request.project_name}/{deploy_request.service_name}")
        manifests = manifest_generator.generate_manifests(deploy_request, deployment_id)
        
        # Stocker les manifests pour récupération ultérieure
        manifests_storage[deployment_id] = manifests
        
        print(f"Generated {len(manifests)} manifests for deployment {deployment_id}")
        for manifest_type in manifests.keys():
            print(f"  - {manifest_type}")
        
        # Déterminer URL d'accès
        access_url = None
        if deploy_request.exposure_type.value == "external":
            domain = deploy_request.custom_domain or settings.DEFAULT_HOST
            path = deploy_request.custom_path or f"/{deploy_request.username}/{deploy_request.project_name}/{deploy_request.service_name}"
            protocol = "https" if deploy_request.enable_https else "http"
            access_url = f"{protocol}://{domain}{path}"
        
        # Créer la réponse initiale
        deploy_response = DeployResponse(
            deployment_id=deployment_id,
            project_id=deploy_request.project_id,
            service_name=deploy_request.service_name,
            status=DeploymentStatus.PENDING,
            image_name=deploy_request.image_name,
            created_at=datetime.now(),
            manifests_generated=list(manifests.keys()),
            access_url=access_url
        )
        
        # Stocker le déploiement dans la database
        namespace_name = manifest_generator._generate_namespace_name(
            deploy_request.username, 
            deploy_request.project_name
        )
        
        await create_deployment({
            'deployment_id': deployment_id,
            'project_id': deploy_request.project_id,
            'username': deploy_request.username,
            'service_name': deploy_request.service_name,
            'display_name': deploy_request.display_name,
            'description': deploy_request.description,
            'image_name': deploy_request.image_name,
            'status': DeploymentStatus.PENDING,
            'replicas_total': deploy_request.replicas,
            'created_at': datetime.now(),
            'access_url': access_url,
            'namespace_name': namespace_name,
            'manifests_generated': list(manifests.keys()),
            'health_check_enabled': deploy_request.health_check_enabled,
            'liveness_check_path': deploy_request.liveness_check_path,
            'readiness_check_path': deploy_request.readiness_check_path
        })
        
        # Démarrer le déploiement en arrière-plan
        background_tasks.add_task(
            deploy_manifests_background,
            deployment_id,
            manifests,
            deploy_request
        )
        
        print(f"Deployment {deployment_id} initiated, processing in background")
        return deploy_response
        
    except Exception as e:
        print(f"Deploy error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to deploy service: {str(e)}")

async def deploy_manifests_background(
    deployment_id: str, 
    manifests: Dict[str, str], 
    deploy_request: DeployRequest
):
    """Déploie les manifests en arrière-plan avec Kubernetes"""
    
    try:
        print(f"Starting background deployment {deployment_id}")
        
        # Marquer comme en cours de déploiement dans la DB
        await update_deployment_status(deployment_id, DeploymentStatus.DEPLOYING)
        
        # Générer le namespace
        namespace = manifest_generator._generate_namespace_name(
            deploy_request.username, 
            deploy_request.project_name
        )
        
        # Appliquer les manifests
        print(f"Applying manifests to namespace: {namespace}")
        results = await k8s_client.apply_manifests(manifests, namespace)
        
        # Vérifier que les manifests critiques ont été appliqués
        critical_manifests = ["namespace", "deployment"]
        failed_critical = [m for m in critical_manifests if m in results and not results[m]]
        
        if failed_critical:
            raise Exception(f"Critical manifests failed: {failed_critical}")
        
        # Attendre que le déploiement soit prêt
        if "deployment" in manifests:
            deployment_name = deploy_request.service_name.lower()
            await wait_for_deployment_ready(deployment_name, namespace, timeout=300)
        
        # Récupérer le statut final du déploiement et mettre à jour la DB
        if "deployment" in manifests:
            status = await k8s_client.get_deployment_status(
                deploy_request.service_name.lower(), 
                namespace
            )
            
            await update_deployment_status(
                deployment_id,
                DeploymentStatus.RUNNING,
                replicas_ready=status.get("replicas_ready", 0),
                replicas_total=status.get("replicas_total", deploy_request.replicas)
            )
        
        print(f"✅ Deployment {deployment_id} completed successfully")
        
    except Exception as e:
        print(f"❌ Background deployment error: {str(e)}")
        
        # Marquer comme échoué dans la DB
        await update_deployment_status(
            deployment_id, 
            DeploymentStatus.FAILED,
            error_message=str(e)
        )

async def wait_for_deployment_ready(deployment_name: str, namespace: str, timeout: int = 300):
    """Attendre que le déploiement soit prêt"""
    start_time = datetime.now()
    
    while (datetime.now() - start_time).total_seconds() < timeout:
        try:
            status = await k8s_client.get_deployment_status(deployment_name, namespace)
            
            if "error" not in status:
                replicas_ready = status.get("replicas_ready", 0)
                replicas_total = status.get("replicas_total", 0)
                
                if replicas_ready > 0 and replicas_ready == replicas_total:
                    print(f"Deployment {deployment_name} is ready ({replicas_ready}/{replicas_total})")
                    return
                else:
                    print(f"Waiting for deployment {deployment_name}: {replicas_ready}/{replicas_total} ready")
            
        except Exception as e:
            print(f"Error checking deployment status: {e}")
        
        await asyncio.sleep(10)  # Vérifier toutes les 10 secondes
    
    raise Exception(f"Deployment {deployment_name} not ready after {timeout}s timeout")

@app.get("/deployments/{deployment_id}", response_model=DeploymentStatusResponse)
async def get_deployment_status(
    deployment_id: str,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Récupérer le statut d'un déploiement"""
    
    deployment_data = await get_deployment(deployment_id)
    if not deployment_data:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
    
    # Convertir les données DB en DeploymentStatusResponse
    return DeploymentStatusResponse(**deployment_data)

@app.get("/manifests/{deployment_id}", response_model=ManifestResponse)
async def get_deployment_manifests(
    deployment_id: str,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Récupérer les manifests générés pour un déploiement"""
    
    deployment_data = await get_deployment(deployment_id)
    if not deployment_data:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
    
    if deployment_id not in manifests_storage:
        raise HTTPException(status_code=404, detail=f"Manifests for deployment {deployment_id} not found")
    
    return ManifestResponse(
        deployment_id=deployment_id,
        manifests=manifests_storage[deployment_id]
    )

@app.get("/projects/{project_id}/deployments")
async def list_project_deployments(
    project_id: int,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Lister tous les déploiements d'un projet"""
    
    # Récupérer depuis la DB avec pagination
    deployments_data = await list_deployments_by_project(project_id, limit, offset)
    
    # Compter le total pour ce projet
    conn = await db.get_connection()
    try:
        total = await conn.fetchval("SELECT COUNT(*) FROM deployments WHERE project_id = $1", project_id)
    finally:
        await db.release_connection(conn)
    
    # Convertir en DeploymentStatusResponse
    deployments = [DeploymentStatusResponse(**deployment_data) for deployment_data in deployments_data]
    
    return {
        "deployments": deployments,
        "total": total,
        "limit": limit,
        "offset": offset,
        "project_id": project_id
    }

@app.delete("/deployments/{deployment_id}")
async def delete_deployment(
    deployment_id: str,
    force: bool = False,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Supprimer un déploiement (undeploy)"""
    
    deployment_data = await get_deployment(deployment_id)
    if not deployment_data:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
    
    try:
        if force:
            # Suppression complète du namespace (tous les services du projet)
            # Récupérer le namespace depuis le deployment
            # TODO: Calculer le namespace depuis les infos du deployment
            print(f"Force deletion of deployment {deployment_id} initiated")
        else:
            # Suppression seulement de ce service
            # TODO: Implémenter suppression sélective des ressources
            print(f"Selective deletion of deployment {deployment_id} initiated")
        
        # Marquer comme supprimé dans la DB
        await update_deployment_status(deployment_id, DeploymentStatus.STOPPED)
        
        return {"message": f"Deployment {deployment_id} deletion initiated", "force": force}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete deployment: {str(e)}")

@app.get("/status")
async def service_status():
    """Status global du Monitor Service"""
    
    kubernetes_connected = await k8s_client.test_connection()
    
    # Récupérer les statistiques depuis la DB
    total_deployments = await count_deployments()
    deployment_stats = await count_deployments_by_status()
    
    # Calculer les déploiements actifs
    active_count = deployment_stats.get(DeploymentStatus.DEPLOYING, 0) + deployment_stats.get(DeploymentStatus.RUNNING, 0)
    
    return {
        "service": "monitor-service",
        "status": "running",
        "kubernetes_connected": kubernetes_connected,
        "active_deployments_count": active_count,
        "total_deployments": total_deployments,
        "deployment_stats": {
            "pending": deployment_stats.get(DeploymentStatus.PENDING, 0),
            "deploying": deployment_stats.get(DeploymentStatus.DEPLOYING, 0),
            "running": deployment_stats.get(DeploymentStatus.RUNNING, 0),
            "failed": deployment_stats.get(DeploymentStatus.FAILED, 0),
            "stopped": deployment_stats.get(DeploymentStatus.STOPPED, 0)
        },
        "settings": {
            "default_replicas": settings.DEFAULT_REPLICAS,
            "default_host": settings.DEFAULT_HOST,
            "ingress_class": settings.DEFAULT_INGRESS_CLASS
        }
    }

# Gestion des erreurs globales
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Endpoint not found",
        "message": f"The endpoint {request.url.path} does not exist",
        "available_endpoints": [
            "/health",
            "/ready",
            "/deploy",
            "/deployments/{deployment_id}",
            "/manifests/{deployment_id}",
            "/projects/{project_id}/deployments",
            "/status"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)