from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# Input schemas (what we receive)
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# Output schemas (what we return)
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class LoginResponse(BaseModel):
    message: str
    user: UserResponse
    token: Token

class RegisterResponse(BaseModel):
    message: str
    user: UserResponse
    token: Token

# Health check schemas
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime

class ReadyResponse(BaseModel):
    status: str
    database: str