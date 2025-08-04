from fastapi import APIRouter, Request, HTTPException, Header
from typing import Dict, Any, Optional
from app.client import service_client
from app.schemas import ServiceStatus
import json

# Router pour les routes des microservices
services_router = APIRouter()

@services_router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_auth(path: str, request: Request, authorization: Optional[str] = Header(None)):
    """Proxy vers le service d'authentification"""
    
    # Récupérer les données de la requête
    method = request.method
    params = dict(request.query_params)
    headers = {"Authorization": authorization} if authorization else {}
    
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
    """Proxy vers le service de gestion des projets"""
    
    method = request.method
    params = dict(request.query_params)
    headers = {"Authorization": authorization} if authorization else {}
    
    json_data = None
    if method in ["POST", "PUT"]:
        try:
            json_data = await request.json()
        except Exception:
            pass
    
    return await service_client.forward_request(
        service_name="projects",
        path=f"/{path}",
        method=method,
        headers=headers,
        params=params,
        json_data=json_data
    )

@services_router.api_route("/builds/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_builds(path: str, request: Request, authorization: Optional[str] = Header(None)):
    """Proxy vers le service de build"""
    
    method = request.method
    params = dict(request.query_params)
    headers = {"Authorization": authorization} if authorization else {}
    
    json_data = None
    if method in ["POST", "PUT"]:
        try:
            json_data = await request.json()
        except Exception:
            pass
    
    return await service_client.forward_request(
        service_name="builds",
        path=f"/{path}",
        method=method,
        headers=headers,
        params=params,
        json_data=json_data
    )

@services_router.api_route("/monitor/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_monitor(path: str, request: Request, authorization: Optional[str] = Header(None)):
    """Proxy vers le service de monitoring"""
    
    method = request.method
    params = dict(request.query_params)
    headers = {"Authorization": authorization} if authorization else {}
    
    json_data = None
    if method in ["POST", "PUT"]:
        try:
            json_data = await request.json()
        except Exception:
            pass
    
    return await service_client.forward_request(
        service_name="monitor",
        path=f"/{path}",
        method=method,
        headers=headers,
        params=params,
        json_data=json_data
    )