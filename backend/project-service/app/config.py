import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Configuration générale
    TITLE: str = "NoKube Project Service"
    DESCRIPTION: str = "Project management service for NoKube platform"
    VERSION: str = "1.0.0"
    
    # Database configuration - PostgreSQL partagé comme Auth Service
    db_host: str = os.getenv('DB_HOST', 'postgresql-service.nokube-system.svc.cluster.local')
    db_port: str = os.getenv('DB_PORT', '5432')
    db_name: str = os.getenv('DB_NAME')
    db_user: str = os.getenv('DB_USER') 
    db_password: str = os.getenv('DB_PASSWORD')
    
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # Configuration des projets
    MAX_PROJECTS_PER_USER: int = int(os.getenv("MAX_PROJECTS_PER_USER", "10"))
    DEFAULT_PROJECT_STATUS: str = "created"
    
    # Intégrations avec autres services
    BUILD_SERVICE_URL: str = os.getenv("BUILD_SERVICE_URL", "http://build-service:8000")
    MONITOR_SERVICE_URL: str = os.getenv("MONITOR_SERVICE_URL", "http://monitor-service:8000")
    
    # Configuration Git
    DEFAULT_BRANCH: str = "main"
    SUPPORTED_GIT_PROVIDERS: list = [
        "github.com",
        "gitlab.com", 
        "bitbucket.org"
    ]
    
    # Configuration de déploiement - CHAQUE PROJET A SON PROPRE NAMESPACE
    PROJECT_NAMESPACE_PREFIX: str = os.getenv("PROJECT_NAMESPACE_PREFIX", "nokube-project-")
    DEFAULT_REPLICAS: int = int(os.getenv("DEFAULT_REPLICAS", "2"))
    
    # Limites de ressources par défaut pour les projets déployés
    DEFAULT_CPU_LIMIT: str = os.getenv("DEFAULT_CPU_LIMIT", "500m")
    DEFAULT_MEMORY_LIMIT: str = os.getenv("DEFAULT_MEMORY_LIMIT", "512Mi")
    DEFAULT_CPU_REQUEST: str = os.getenv("DEFAULT_CPU_REQUEST", "100m")
    DEFAULT_MEMORY_REQUEST: str = os.getenv("DEFAULT_MEMORY_REQUEST", "128Mi")
    
    def get_project_namespace(self, project_name: str) -> str:
        """Génère le namespace unique pour un projet"""
        # Nettoyer le nom du projet pour être compatible K8s
        clean_name = project_name.lower().replace("_", "-").replace(" ", "-")
        return f"{self.PROJECT_NAMESPACE_PREFIX}{clean_name}"

settings = Settings()