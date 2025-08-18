import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logger les requêtes et performances"""
    
    async def dispatch(self, request: Request, call_next):
        # Démarrer le timer
        start_time = time.time()
        
        # Logger la requête entrante
        logger.info(f"Incoming request: {request.method} {request.url}")
        
        # Exécuter la requête
        response = await call_next(request)
        
        # Calculer le temps de traitement
        process_time = time.time() - start_time
        
        # Logger la réponse
        logger.info(
            f"Request processed: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        # Ajouter le temps de traitement dans les headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response