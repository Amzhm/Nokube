from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class BuildStatus(str, Enum):
    PENDING = "pending"
    BUILDING = "building"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Input schemas
class BuildRequest(BaseModel):
    """Requête de build avec repo GitHub et Dockerfile"""
    project_id: int
    repository_url: HttpUrl
    branch: Optional[str] = "main"
    
    # Gestion Dockerfile
    has_dockerfile: bool = False  # True si Dockerfile existe dans le repo user
    dockerfile_path: Optional[str] = "Dockerfile"  # Chemin dans le repo user
    dockerfile_content: Optional[str] = None  # Contenu si pas de Dockerfile existant
    
    image_name: str  # Nom final de l'image (ex: "my-app")
    image_tag: Optional[str] = "latest"
    service_name: str  # Nom du service (ex: "frontend", "backend")
    build_args: Optional[Dict[str, str]] = {}  # Arguments Docker build
    
class BuildCancel(BaseModel):
    """Annuler un build en cours"""
    build_id: str
    reason: Optional[str] = "Cancelled by user"

# Output schemas
class BuildResponse(BaseModel):
    """Réponse après soumission d'un build"""
    build_id: str
    project_id: int
    status: BuildStatus
    image_full_name: str  # ghcr.io/amzhm/nokube/my-app:latest
    created_at: datetime
    estimated_duration: Optional[int] = None  # en secondes
    
class BuildStatusResponse(BaseModel):
    """Status d'un build en cours ou terminé"""
    build_id: str
    project_id: int
    service_name: Optional[str] = None  # Nom du service
    status: BuildStatus
    image_full_name: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None  # en secondes
    logs: Optional[str] = None
    error_message: Optional[str] = None
    
class BuildLogResponse(BaseModel):
    """Logs en temps réel d'un build"""
    build_id: str
    logs: str
    timestamp: datetime
    is_complete: bool

class BuildListResponse(BaseModel):
    """Liste des builds d'un projet"""
    builds: list[BuildStatusResponse]
    total: int
    limit: int
    offset: int

# Health check schemas
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    github_status: Optional[str] = None
    
class ReadyResponse(BaseModel):
    status: str
    github_available: bool
    github_configured: bool