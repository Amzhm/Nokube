import os

class Settings:
    # Configuration générale
    TITLE: str = "NoKube Build Service"
    DESCRIPTION: str = "Service de build d'images Docker avec GitHub Actions"
    VERSION: str = "1.0.0"
    
    # Database configuration - PostgreSQL partagé avec autres services
    db_host: str = os.getenv('DB_HOST', 'postgresql-service.nokube-system.svc.cluster.local')
    db_port: str = os.getenv('DB_PORT', '5432')
    db_name: str = os.getenv('DB_NAME')
    db_user: str = os.getenv('DB_USER') 
    db_password: str = os.getenv('DB_PASSWORD')
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # Configuration Docker
    DOCKER_REGISTRY: str = os.getenv("DOCKER_REGISTRY", "ghcr.io")
    DOCKER_NAMESPACE: str = os.getenv("DOCKER_NAMESPACE", "amzhm")
    
    # GitHub Configuration
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_BUILD_REPO: str = os.getenv("GITHUB_BUILD_REPO", "Amzhm/NoKube-build")
    
    # GitHub Container Registry - utilisé par GitHub Actions
    GHCR_TOKEN: str = os.getenv("GHCR_TOKEN", "")
    GHCR_USERNAME: str = os.getenv("GHCR_USERNAME", "")
    
    # Configuration build
    BUILD_TIMEOUT: int = int(os.getenv("BUILD_TIMEOUT", "600"))  # 10 minutes
    MAX_CONCURRENT_BUILDS: int = int(os.getenv("MAX_CONCURRENT_BUILDS", "3"))

settings = Settings()