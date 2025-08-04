import httpx
import time
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.config import settings
from app.schemas import ServiceStatus

class ServiceClient:
    """Client HTTP pour communiquer avec les microservices"""
    
    def __init__(self):
        self.timeout = settings.SERVICE_TIMEOUT
        
    async def forward_request(
        self, 
        service_name: str,
        path: str, 
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transmet une requête vers un microservice
        
        Args:
            service_name: Nom du service (auth, projects, builds, monitor)
            path: Chemin de l'endpoint (ex: /login, /health)
            method: Méthode HTTP (GET, POST, PUT, DELETE)
            headers: Headers HTTP à transmettre
            params: Paramètres de requête
            json_data: Données JSON pour POST/PUT
            
        Returns:
            Réponse du microservice
            
        Raises:
            HTTPException: Si le service est inaccessible ou retourne une erreur
        """
        
        # Récupérer l'URL du service
        service_url = settings.SERVICE_ROUTES.get(service_name)
        if not service_url:
            raise HTTPException(
                status_code=404, 
                detail=f"Service {service_name} not configured"
            )
        
        # Construire l'URL complète
        full_url = f"{service_url}{path}"
        
        # Préparer les headers
        request_headers = headers or {}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start_time = time.time()
                
                # Effectuer la requête selon la méthode
                if method.upper() == "GET":
                    response = await client.get(full_url, headers=request_headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(full_url, headers=request_headers, params=params, json=json_data)
                elif method.upper() == "PUT":
                    response = await client.put(full_url, headers=request_headers, params=params, json=json_data)
                elif method.upper() == "DELETE":
                    response = await client.delete(full_url, headers=request_headers, params=params)
                else:
                    raise HTTPException(status_code=405, detail=f"Method {method} not supported")
                
                response_time = (time.time() - start_time) * 1000  # en ms
                
                # Si le service retourne une erreur HTTP, on la propage
                if response.status_code >= 400:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=response.text or f"Error from {service_name} service"
                    )
                
                # Retourner la réponse JSON
                return response.json()
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail=f"Service {service_name} timeout"
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"Service {service_name} unavailable"
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=500,
                detail=f"Gateway error: {str(e)}"
            )
    
    async def check_service_health(self, service_name: str) -> ServiceStatus:
        """Vérifie la santé d'un microservice"""
        service_url = settings.SERVICE_ROUTES.get(service_name)
        if not service_url:
            return ServiceStatus(
                service=service_name,
                url="unknown",
                status="unconfigured"
            )
        
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{service_url}/health")
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    return ServiceStatus(
                        service=service_name,
                        url=service_url,
                        status="healthy",
                        response_time_ms=response_time
                    )
                else:
                    return ServiceStatus(
                        service=service_name,
                        url=service_url,
                        status="unhealthy"
                    )
                    
        except httpx.TimeoutException:
            return ServiceStatus(
                service=service_name,
                url=service_url,
                status="timeout"
            )
        except Exception:
            return ServiceStatus(
                service=service_name,
                url=service_url,
                status="unhealthy"
            )

# Instance globale du client
service_client = ServiceClient()