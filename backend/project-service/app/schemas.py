from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ProjectStatus(str, Enum):
    created = "created"
    building = "building"
    deploying = "deploying"
    deployed = "deployed"
    failed = "failed"
    stopped = "stopped"

class ProjectFramework(str, Enum):
    react = "react"
    vue = "vue"
    angular = "angular"
    nextjs = "nextjs"
    nodejs = "nodejs"
    python = "python"
    django = "django"
    fastapi = "fastapi"
    spring = "spring"
    dotnet = "dotnet"

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="Project name (unique)")
    description: Optional[str] = Field(None, max_length=500, description="Project description")
    repository_url: str = Field(..., description="Git repository URL")
    framework: ProjectFramework = Field(..., description="Project framework/technology")
    # owner automatiquement défini par JWT

    class Config:
        schema_extra = {
            "example": {
                "name": "my-awesome-app",
                "description": "A modern web application",
                "repository_url": "https://github.com/user/my-awesome-app.git",
                "framework": "react"
            }
        }

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    repository_url: Optional[str] = None
    framework: Optional[ProjectFramework] = None
    status: Optional[ProjectStatus] = None

    class Config:
        schema_extra = {
            "example": {
                "description": "Updated project description",
                "status": "deployed"
            }
        }

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    repository_url: str
    framework: str
    status: str
    owner: str
    created_at: datetime
    updated_at: datetime

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "my-awesome-app",
                "description": "A modern web application",
                "repository_url": "https://github.com/user/my-awesome-app.git",
                "framework": "react",
                "status": "deployed",
                "owner": "AmzianeHamrani",
                "created_at": "2025-08-04T10:30:00",
                "updated_at": "2025-08-04T10:30:00"
            }
        }

class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    limit: int
    offset: int

    class Config:
        schema_extra = {
            "example": {
                "projects": [
                    {
                        "id": 1,
                        "name": "my-awesome-app",
                        "description": "A modern web application",
                        "repository_url": "https://github.com/user/my-awesome-app.git",
                        "framework": "react",
                        "status": "deployed",
                        "owner": "AmzianeHamrani",
                        "created_at": "2025-08-04T10:30:00",
                        "updated_at": "2025-08-04T10:30:00"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime

class ProjectError(BaseModel):
    error: str
    project_id: Optional[int] = None
    timestamp: datetime
    details: Optional[str] = None