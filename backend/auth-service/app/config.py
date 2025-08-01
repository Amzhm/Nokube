import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database configuration - MUST come from environment variables
    db_host: str = os.getenv('DB_HOST', 'postgresql-service.nokube-system.svc.cluster.local')
    db_port: str = os.getenv('DB_PORT', '5432')
    db_name: str = os.getenv('DB_NAME')
    db_user: str = os.getenv('DB_USER') 
    db_password: str = os.getenv('DB_PASSWORD')
    
    # JWT configuration - MUST come from environment variables
    jwt_secret: str = os.getenv('JWT_SECRET')
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings()