from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum

class DeploymentStatus(str, Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"

class ServiceType(str, Enum):
    WEB = "web"           # Applications web exposées (avec Ingress)
    API = "api"           # Services API internes (ClusterIP seulement)
    WORKER = "worker"     # Workers/jobs sans réseau

class ExposureType(str, Enum):
    NONE = "none"         # Pas d'exposition (workers)
    INTERNAL = "internal" # Seulement dans le cluster
    EXTERNAL = "external" # Exposé via Ingress sur Internet

# Input schemas
class DeployRequest(BaseModel):
    """Requête de déploiement avec configuration complète utilisateur"""
    
    # Informations projet et utilisateur
    project_id: int
    project_name: str            # Nom du projet (choix utilisateur, ex: "ecommerce-app")
    username: str                # Nom utilisateur (ex: "testuser2")
    service_name: str            # Nom du service dans ce projet (ex: "frontend")
    display_name: str            # Nom affiché (ex: "Frontend React")
    description: Optional[str] = None
    image_name: str              # ghcr.io/amzhm/user-project-service:tag
    
    # Configuration du service (requis - frontend doit fournir)
    service_type: ServiceType
    exposure_type: ExposureType
    
    # Configuration ports (requis)
    container_port: int                    # Port d'écoute dans le container
    service_port: int                      # Port du service K8s
    
    # Configuration des ressources (requis)
    replicas: int
    cpu_request: str                       # Ex: "100m", "0.5", "1"
    cpu_limit: str                         # Ex: "500m", "1", "2"
    memory_request: str                    # Ex: "128Mi", "256Mi", "1Gi"
    memory_limit: str                      # Ex: "512Mi", "1Gi", "2Gi"
    
    # Configuration réseau (optionnel)
    custom_domain: Optional[str] = None
    custom_path: Optional[str] = None
    enable_https: bool = False
    
    # Variables d'environnement (optionnel)
    env_vars: Optional[Dict[str, str]] = None
    secrets: Optional[Dict[str, str]] = None
    
    # Configuration santé (requis)
    health_check_enabled: bool
    liveness_check_path: Optional[str] = None
    readiness_check_path: Optional[str] = None
    health_check_port: Optional[int] = None
    liveness_initial_delay: Optional[int] = None
    readiness_initial_delay: Optional[int] = None
    health_check_period: Optional[int] = None
    health_check_timeout: Optional[int] = None
    health_check_failure_threshold: Optional[int] = None
    
    # Stockage persistant (optionnel)
    storage_size: Optional[str] = None
    storage_path: Optional[str] = None
    
    # Auto-scaling (optionnel)
    enable_autoscaling: bool = False
    min_replicas: Optional[int] = None
    max_replicas: Optional[int] = None
    target_cpu_percent: Optional[int] = None

class DeployResponse(BaseModel):
    """Réponse après déploiement"""
    deployment_id: str
    project_id: int
    service_name: str
    status: DeploymentStatus
    image_name: str
    created_at: datetime
    manifests_generated: List[str]  # Liste des types de manifests générés
    access_url: Optional[str] = None  # URL d'accès si web service

class DeploymentStatusResponse(BaseModel):
    """Status d'un déploiement"""
    deployment_id: str
    project_id: int
    service_name: str
    status: DeploymentStatus
    image_name: str
    replicas_ready: int
    replicas_total: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    access_url: Optional[str] = None
    
class ManifestResponse(BaseModel):
    """Manifests générés"""
    deployment_id: str
    manifests: Dict[str, str]  # type -> yaml content

# Health check schemas
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    kubernetes_connected: bool
    
class ReadyResponse(BaseModel):
    status: str
    kubernetes_available: bool
    namespace_accessible: bool