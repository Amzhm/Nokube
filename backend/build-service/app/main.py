from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import List, Optional
import asyncio

from app.config import settings
from app.schemas import (
    BuildRequest, BuildResponse, BuildStatusResponse, 
    BuildCancel, BuildLogResponse, BuildListResponse,
    HealthResponse, ReadyResponse, BuildStatus
)
from app.github_builder import github_builder
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

# Stockage temporaire des builds (en production, utiliser une DB)
builds_storage: dict[str, BuildStatusResponse] = {}

@app.get("/")
async def root(x_user: str = Header(...)):
    """Endpoint racine du Build Service"""
    return {
        "service": "NoKube Build Service",
        "version": settings.VERSION,
        "status": "running",
        "timestamp": datetime.now(),
        "endpoints": {
            "health": "/health",
            "builds": "/builds",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check du Build Service"""
    github_status = "unknown"
    try:
        github_builder.repo.get_contents("README.md")  # Test simple d'accès
        github_status = "connected"
    except Exception:
        github_status = "disconnected"
    
    return HealthResponse(
        status="healthy",
        service="build-service",
        timestamp=datetime.now(),
        github_status=github_status
    )

@app.get("/ready", response_model=ReadyResponse)
async def ready_check():
    """Readiness check du Build Service"""
    github_available = False
    github_configured = bool(settings.GITHUB_TOKEN and settings.GITHUB_BUILD_REPO)
    
    try:
        github_builder.repo.get_contents("README.md")
        github_available = True
    except Exception:
        pass
    
    status = "ready" if (github_available and github_configured) else "not_ready"
    
    return ReadyResponse(
        status=status,
        github_available=github_available,
        github_configured=github_configured
    )

@app.post("/builds", response_model=BuildResponse)
async def create_build(
    build_request: BuildRequest,
    background_tasks: BackgroundTasks,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Démarrer un nouveau build d'image Docker"""
    
    try:
        # Démarrer le build en arrière-plan avec callback pour update du storage
        def update_build_status(build_status: BuildStatusResponse):
            builds_storage[build_status.build_id] = build_status
            
        build_id = await github_builder.start_build(build_request, update_build_status, x_user)
        
        # Générer nom image format: user-project-service
        project_name = build_request.image_name.split('-')[0] if '-' in build_request.image_name else build_request.image_name
        generated_image_name = f"{x_user}-{project_name}-{build_request.service_name}"
        
        # Image complète
        image_full_name = f"{settings.DOCKER_REGISTRY}/{settings.DOCKER_NAMESPACE}/{generated_image_name}:{build_request.image_tag}"
        
        # Créer la réponse initiale
        build_response = BuildResponse(
            build_id=build_id,
            project_id=build_request.project_id,
            status=BuildStatus.BUILDING,
            image_full_name=image_full_name,
            created_at=datetime.now(),
            estimated_duration=300  # 5 minutes estimation
        )
        
        # Stocker le build
        builds_storage[build_id] = BuildStatusResponse(
            build_id=build_id,
            project_id=build_request.project_id,
            service_name=build_request.service_name,
            status=BuildStatus.BUILDING,
            image_full_name=image_full_name,
            created_at=datetime.now(),
            started_at=datetime.now()
        )
        
        return build_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start build: {str(e)}")

@app.get("/builds/{build_id}", response_model=BuildStatusResponse)
async def get_build_status(
    build_id: str,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Récupérer le statut d'un build"""
    
    if build_id not in builds_storage:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    return builds_storage[build_id]

@app.delete("/builds/{build_id}")
async def cancel_build(
    build_id: str,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Annuler un build en cours"""
    
    if build_id not in builds_storage:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    success = await github_builder.cancel_build(build_id)
    
    if success:
        builds_storage[build_id].status = BuildStatus.CANCELLED
        builds_storage[build_id].completed_at = datetime.now()
        return {"message": f"Build {build_id} cancelled successfully"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot cancel build {build_id}")

@app.get("/builds/{build_id}/logs")
async def get_build_logs(
    build_id: str,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Stream des logs d'un build en temps réel"""
    
    if build_id not in builds_storage:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    async def log_generator():
        async for log_line in github_builder.get_build_logs(build_id):
            yield f"data: {log_line}\n\n"
    
    return StreamingResponse(
        log_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )

@app.get("/projects/{project_id}/builds", response_model=BuildListResponse)
async def list_project_builds(
    project_id: int,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Lister tous les builds d'un projet"""
    
    # Filtrer les builds par project_id
    project_builds = [
        build for build in builds_storage.values()
        if build.project_id == project_id
    ]
    
    # Pagination
    total = len(project_builds)
    paginated_builds = project_builds[offset:offset + limit]
    
    return BuildListResponse(
        builds=paginated_builds,
        total=total,
        limit=limit,
        offset=offset
    )

@app.get("/builds")
async def list_all_builds(
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    status: Optional[BuildStatus] = None,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Lister tous les builds avec filtres optionnels"""
    
    all_builds = list(builds_storage.values())
    
    # Filtrer par statut si spécifié
    if status:
        all_builds = [build for build in all_builds if build.status == status]
    
    # Trier par date de création (plus récent en premier)
    all_builds.sort(key=lambda x: x.created_at, reverse=True)
    
    # Pagination
    total = len(all_builds)
    paginated_builds = all_builds[offset:offset + limit]
    
    return {
        "builds": paginated_builds,
        "total": total,
        "limit": limit,
        "offset": offset,
        "active_builds": github_builder.get_active_builds()
    }

@app.get("/status")
async def service_status():
    """Status global du Build Service"""
    
    return {
        "service": "build-service",
        "status": "running",
        "github_configured": bool(settings.GITHUB_TOKEN and settings.GITHUB_BUILD_REPO),
        "ghcr_configured": bool(settings.GHCR_TOKEN and settings.GHCR_USERNAME),
        "active_builds_count": len(github_builder.active_builds),
        "total_builds": len(builds_storage),
        "settings": {
            "max_concurrent_builds": settings.MAX_CONCURRENT_BUILDS,
            "build_timeout": settings.BUILD_TIMEOUT,
            "docker_registry": settings.DOCKER_REGISTRY,
            "docker_namespace": settings.DOCKER_NAMESPACE
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
            "/builds",
            "/builds/{build_id}",
            "/builds/{build_id}/logs",
            "/projects/{project_id}/builds"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)