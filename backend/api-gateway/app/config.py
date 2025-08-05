import os
from typing import Dict

class Settings:
    # Service discovery - URLs des microservices
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
    PROJECT_SERVICE_URL: str = os.getenv("PROJECT_SERVICE_URL", "http://project-service:8000") 
    BUILD_SERVICE_URL: str = os.getenv("BUILD_SERVICE_URL", "http://build-service:8000")
    MONITOR_SERVICE_URL: str = os.getenv("MONITOR_SERVICE_URL", "http://monitor-service:8000")
    
    # Configuration générale
    API_V1_PREFIX: str = "/api/v1"
    TITLE: str = "NoKube API Gateway"
    DESCRIPTION: str = "Central API Gateway for NoKube platform"
    VERSION: str = "1.0.0"
    
    # Timeout pour les requêtes vers les microservices (en secondes)
    SERVICE_TIMEOUT: int = int(os.getenv("SERVICE_TIMEOUT", "30"))
    
    # JWT configuration - pour l'authentification centralisée
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    
    # Configuration des routes - mapping des services
    SERVICE_ROUTES: Dict[str, str] = {
        "auth": AUTH_SERVICE_URL,
        "projects": PROJECT_SERVICE_URL,
        "builds": BUILD_SERVICE_URL,
        "monitor": MONITOR_SERVICE_URL
    }

settings = Settings()