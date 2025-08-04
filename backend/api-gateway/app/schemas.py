from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    
class ReadyResponse(BaseModel):
    status: str
    services: Dict[str, str]  # Status de chaque service backend
    
class GatewayError(BaseModel):
    error: str
    service: str
    timestamp: datetime
    details: Optional[str] = None
    
class ServiceStatus(BaseModel):
    service: str
    url: str
    status: str  # "healthy", "unhealthy", "timeout"
    response_time_ms: Optional[float] = None