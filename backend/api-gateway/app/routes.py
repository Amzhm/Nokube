from fastapi import APIRouter, Request, HTTPException, Header
from typing import Dict, Any, Optional
from app.client import service_client
from app.schemas import ServiceStatus
from app.auth import verify_jwt_token, is_public_endpoint
import json

# Router pour les routes des microservices
services_router = APIRouter()

@services_router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_auth(path: str, request: Request, authorization: Optional[str] = Header(None)):
    """Proxy vers le service d'authentification"""
    
    # Récupérer les données de la requête
    method = request.method
    params = dict(request.query_params)
    
    # Vérifier si l'endpoint nécessite une authentification
    full_path = f"/auth/{path}"
    headers = {}
    
    if not is_public_endpoint(full_path):
        # Endpoint protégé - vérifier JWT et ajouter X-User
        username = verify_jwt_token(authorization)
        headers["X-User"] = username
    
    # Pour POST/PUT, récupérer le body JSON
    json_data = None
    if method in ["POST", "PUT"]:
        try:
            json_data = await request.json()
        except Exception:
            pass  # Pas de JSON body
    
    # Transmettre la requête au service auth
    return await service_client.forward_request(
        service_name="auth",
        path=f"/{path}",
        method=method,
        headers=headers,
        params=params,
        json_data=json_data
    )

@services_router.api_route("/projects/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_projects(path: str, request: Request, authorization: Optional[str] = Header(None)):
    """Proxy vers le service de gestion des projets (authentification requise)"""
    
    # Tous les endpoints projects nécessitent une authentification
    username = verify_jwt_token(authorization)
    
    method = request.method
    params = dict(request.query_params)
    headers = {"X-User": username}  # Transmettre le username au service
    
    json_data = None
    if method in ["POST", "PUT"]:
        try:
            json_data = await request.json()
        except Exception:
            pass
    
    # Router directement le path vers le service (enlever le préfixe projects/)
    service_path = f"/" if not path else f"/{path}"
    
    return await service_client.forward_request(
        service_name="projects",
        path=service_path,
        method=method,
        headers=headers,
        params=params,
        json_data=json_data
    )

@services_router.api_route("/builds/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_builds(path: str, request: Request, authorization: Optional[str] = Header(None)):
    """Proxy vers le service de build (authentification requise)"""
    
    # Tous les endpoints builds nécessitent une authentification
    username = verify_jwt_token(authorization)
    
    method = request.method
    params = dict(request.query_params)
    headers = {"X-User": username}  # Transmettre le username au service
    
    json_data = None
    if method in ["POST", "PUT"]:
        try:
            json_data = await request.json()
        except Exception:
            pass
    
    # Router directement le path vers le service (enlever le préfixe builds/)
    service_path = f"/" if not path else f"/{path}"
    
    return await service_client.forward_request(
        service_name="builds",
        path=service_path,
        method=method,
        headers=headers,
        params=params,
        json_data=json_data
    )

@services_router.api_route("/monitor/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_monitor(path: str, request: Request, authorization: Optional[str] = Header(None)):
    """Proxy vers le service de monitoring (authentification requise)"""
    
    # Tous les endpoints monitor nécessitent une authentification
    username = verify_jwt_token(authorization)
    
    method = request.method
    params = dict(request.query_params)
    headers = {"X-User": username}  # Transmettre le username au service
    
    json_data = None
    if method in ["POST", "PUT"]:
        try:
            json_data = await request.json()
        except Exception:
            pass
    
    # Router directement le path vers le service (enlever le préfixe monitor/)
    service_path = f"/" if not path else f"/{path}"
    
    return await service_client.forward_request(
        service_name="monitor",
        path=service_path,
        method=method,
        headers=headers,
        params=params,
        json_data=json_data
    )