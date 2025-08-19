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
from app.database import db, init_db, create_build, get_build, update_build_status, list_builds_by_project, list_all_builds, count_builds
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

# Note: Builds maintenant stockés dans PostgreSQL (plus de stockage en mémoire)

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
        # Démarrer le build en arrière-plan avec callback pour update de la DB
        async def update_build_status_callback(build_status: BuildStatusResponse):
            # Mettre à jour dans la database au lieu du storage en mémoire
            await update_build_status(
                build_status.build_id,
                build_status.status,
                completed_at=build_status.completed_at,
                error_message=build_status.error_message
            )
            
        build_id = await github_builder.start_build(build_request, update_build_status_callback, x_user)
        
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
        
        # Stocker le build dans la database
        await create_build({
            'build_id': build_id,
            'project_id': build_request.project_id,
            'username': x_user,
            'service_name': build_request.service_name,
            'image_name': build_request.image_name,
            'image_full_name': image_full_name,
            'status': BuildStatus.BUILDING,
            'created_at': datetime.now(),
            'started_at': datetime.now(),
            'estimated_duration': 300
        })
        
        return build_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start build: {str(e)}")

@app.get("/builds/{build_id}", response_model=BuildStatusResponse)
async def get_build_status(
    build_id: str,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Récupérer le statut d'un build"""
    
    build_data = await get_build(build_id)
    if not build_data:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    return BuildStatusResponse(**build_data)

@app.delete("/builds/{build_id}")
async def cancel_build(
    build_id: str,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Annuler un build en cours"""
    
    build_data = await get_build(build_id)
    if not build_data:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    success = await github_builder.cancel_build(build_id)
    
    if success:
        await update_build_status(build_id, BuildStatus.CANCELLED, completed_at=datetime.now())
        return {"message": f"Build {build_id} cancelled successfully"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot cancel build {build_id}")

@app.get("/builds/{build_id}/logs")
async def get_build_logs(
    build_id: str,
    x_user: str = Header(..., description="Utilisateur authentifié via Gateway")
):
    """Stream des logs d'un build en temps réel"""
    
    build_data = await get_build(build_id)
    if not build_data:
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
    
    # Récupérer les builds depuis la DB
    builds_data = await list_builds_by_project(project_id, limit, offset)
    
    # Compter le total pour ce projet
    conn = await db.get_connection()
    try:
        total = await conn.fetchval("SELECT COUNT(*) FROM builds WHERE project_id = $1", project_id)
    finally:
        await db.release_connection(conn)
    
    # Convertir en BuildStatusResponse
    builds = [BuildStatusResponse(**build_data) for build_data in builds_data]
    
    return BuildListResponse(
        builds=builds,
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
    
    # Récupérer depuis la DB avec filtrage optionnel
    status_str = status.value if status else None
    builds_data = await list_all_builds(limit, offset, status_str)
    
    # Compter le total
    total = await count_builds()
    if status:
        # Compter avec filtre de statut
        conn = await db.get_connection()
        try:
            total = await conn.fetchval("SELECT COUNT(*) FROM builds WHERE status = $1", status_str)
        finally:
            await db.release_connection(conn)
    
    # Convertir en BuildStatusResponse
    builds = [BuildStatusResponse(**build_data) for build_data in builds_data]
    
    return {
        "builds": builds,
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
        "total_builds": await count_builds(),
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