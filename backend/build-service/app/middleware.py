import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware de logging pour les requêtes HTTP"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Logs de la requête entrante
        logger.info(f"Incoming request: {request.method} {request.url}")
        
        # Traitement de la requête
        response = await call_next(request)
        
        # Calcul du temps de traitement
        process_time = time.time() - start_time
        
        # Logs de la réponse
        logger.info(
            f"Request processed: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        # Ajouter le temps de traitement dans les headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

# Configuration CORS pour le Build Service
def get_cors_middleware():
    return FastAPICORSMiddleware(
        allow_origins=["*"],  # En production, spécifier les domaines autorisés
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )