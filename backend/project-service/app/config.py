import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database configuration - PostgreSQL partagé
    db_host: str = os.getenv('DB_HOST', 'postgresql-service.nokube-system.svc.cluster.local')
    db_port: str = os.getenv('DB_PORT', '5432')
    db_name: str = os.getenv('DB_NAME')
    db_user: str = os.getenv('DB_USER') 
    db_password: str = os.getenv('DB_PASSWORD')
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # Configuration métier
    VERSION: str = "1.0.0"
    MAX_PROJECTS_PER_USER: int = int(os.getenv("MAX_PROJECTS_PER_USER", "10"))
    DEFAULT_PROJECT_STATUS: str = "created"
    DEFAULT_SERVICE_STATUS: str = "created"
    
settings = Settings()