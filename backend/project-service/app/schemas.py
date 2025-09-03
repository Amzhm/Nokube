from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ProjectStatus(str, Enum):
    created = "created"
    active = "active"
    archived = "archived"

class ServiceStatus(str, Enum):
    created = "created"
    active = "active"
    building = "building"
    deployed = "deployed"
    failed = "failed"
    stopped = "stopped"

class ServiceType(str, Enum):
    web = "web"      # Applications web (avec UI)
    api = "api"      # APIs backend
    worker = "worker" # Background jobs, workers

# === PROJECT SCHEMAS ===

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Project name (unique per user)")
    display_name: Optional[str] = Field(None, max_length=150, description="Display name")
    description: Optional[str] = Field(None, max_length=500, description="Project description")
    repository_url: str = Field(..., description="Git repository URL")
    # owner automatiquement défini par JWT


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    display_name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    repository_url: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    display_name: Optional[str]
    description: Optional[str]
    repository_url: str
    status: str
    owner: str
    services_count: Optional[int] = 0  # Nombre de services dans ce projet
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    limit: int
    offset: int

# === SERVICE SCHEMAS ===

class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Service name (unique per project)")
    display_name: Optional[str] = Field(None, max_length=150, description="Service display name")
    description: Optional[str] = Field(None, max_length=500, description="Service description")
    service_type: ServiceType = Field(ServiceType.web, description="Type of service")


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    display_name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    service_type: Optional[ServiceType] = None
    status: Optional[ServiceStatus] = None

class ServiceResponse(BaseModel):
    id: int
    project_id: int
    name: str
    display_name: Optional[str]
    description: Optional[str]
    service_type: str
    status: str
    created_at: datetime
    updated_at: datetime


class ServiceListResponse(BaseModel):
    services: List[ServiceResponse]
    total: int
    limit: int
    offset: int
    project_id: int

# === SHARED SCHEMAS ===

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime

class ReadyResponse(BaseModel):
    status: str
    service: str
    database: str
    timestamp: datetime

class ProjectError(BaseModel):
    error: str
    project_id: Optional[int] = None
    service_id: Optional[int] = None
    timestamp: datetime
    details: Optional[str] = None