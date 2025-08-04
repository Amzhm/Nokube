from fastapi import FastAPI
from datetime import datetime
from app.config import settings
from app.schemas import HealthResponse, ReadyResponse, ServiceStatus
from app.client import service_client
from app.middleware import LoggingMiddleware, CORSMiddleware
from app.routes import services_router

# Création de l'application FastAPI
app = FastAPI(
    title=settings.TITLE,
    description=settings.DESCRIPTION,
    version=settings.VERSION
)

# Ajout des middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(CORSMiddleware)

# Inclusion des routes des services
app.include_router(services_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    """Endpoint racine de l'API Gateway"""
    return {
        "service": "NoKube API Gateway",
        "version": settings.VERSION,
        "status": "running",
        "timestamp": datetime.now(),
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs",
            "api": settings.API_V1_PREFIX
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check de l'API Gateway"""
    return HealthResponse(
        status="healthy",
        service="api-gateway",
        timestamp=datetime.now()
    )

@app.get("/ready", response_model=ReadyResponse)
async def readiness_check():
    """Readiness check - vérifie la disponibilité des services backend"""
    
    services_status = {}
    
    # Vérifier chaque service backend
    for service_name in settings.SERVICE_ROUTES.keys():
        try:
            service_status = await service_client.check_service_health(service_name)
            services_status[service_name] = service_status.status
        except Exception as e:
            services_status[service_name] = f"error: {str(e)}"
    
    return ReadyResponse(
        status="ready",
        services=services_status
    )

@app.get("/services/status")
async def services_status():
    """Endpoint pour obtenir le statut détaillé de tous les services"""
    
    services = []
    
    for service_name in settings.SERVICE_ROUTES.keys():
        try:
            service_status = await service_client.check_service_health(service_name)
            services.append(service_status.dict())
        except Exception as e:
            services.append({
                "service": service_name,
                "url": settings.SERVICE_ROUTES.get(service_name, "unknown"),
                "status": "error",
                "error": str(e)
            })
    
    return {
        "gateway": "api-gateway",
        "timestamp": datetime.now(),
        "services": services
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
            "/services/status",
            f"{settings.API_V1_PREFIX}/auth/*",
            f"{settings.API_V1_PREFIX}/projects/*",
            f"{settings.API_V1_PREFIX}/builds/*",
            f"{settings.API_V1_PREFIX}/monitor/*"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)