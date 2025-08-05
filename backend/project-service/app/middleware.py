import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logger les requêtes"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Logger la requête entrante
        logger.info(f"Incoming request: {request.method} {request.url}")
        
        # Traiter la requête
        response = await call_next(request)
        
        # Calculer le temps de traitement
        process_time = time.time() - start_time
        
        # Logger la réponse
        logger.info(
            f"Request processed: {request.method} {request.url} "
            f"- Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        # Ajouter le temps de traitement dans les headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

class CORSMiddleware(BaseHTTPMiddleware):
    """Middleware CORS simple pour le développement"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Ajouter les headers CORS
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return response