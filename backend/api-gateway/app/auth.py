from fastapi import HTTPException, status
from typing import Optional
import jwt
from app.config import settings

def verify_jwt_token(authorization: Optional[str]) -> str:
    """
    Vérifier le JWT token et extraire le username
    
    Args:
        authorization: Header Authorization (Bearer token)
        
    Returns:
        str: Username de l'utilisateur authentifié
        
    Raises:
        HTTPException: Si le token est invalide ou manquant
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    
    try:
        # Décoder le JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extraire le username du payload
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return username
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def is_public_endpoint(path: str) -> bool:
    """
    Vérifier si l'endpoint est public (pas d'auth requise)
    
    Args:
        path: Le chemin de l'endpoint
        
    Returns:
        bool: True si l'endpoint est public
    """
    public_endpoints = [
        "/auth/login",
        "/auth/register", 
        "/auth/health",
        "/health",
        "/ready",
        "/services/status"
    ]
    
    # Vérifier les patterns exacts
    for public_path in public_endpoints:
        if path == public_path or path.startswith(public_path + "/"):
            return True
    
    return False