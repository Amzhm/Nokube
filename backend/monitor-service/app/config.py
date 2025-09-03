import os

class Settings:
    # Configuration générale
    TITLE: str = "NoKube Monitor Service"
    DESCRIPTION: str = "Service de monitoring et déploiement Kubernetes"
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
    
    # Configuration Kubernetes
    KUBECONFIG: str = os.getenv("KUBECONFIG", "~/.kube/config")
    
    # Configuration Ingress (valeurs globales NoKube)
    DEFAULT_INGRESS_CLASS: str = os.getenv("INGRESS_CLASS", "nginx")
    DEFAULT_HOST: str = os.getenv("DEFAULT_HOST", "localhost")

settings = Settings()