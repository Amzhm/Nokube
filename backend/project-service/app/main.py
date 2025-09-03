from fastapi import FastAPI, HTTPException, Header
from datetime import datetime
from typing import List, Optional
from app.schemas import (
    ProjectCreate, ProjectResponse, ProjectUpdate, ProjectListResponse,
    ServiceCreate, ServiceResponse, ServiceUpdate, ServiceListResponse,
    HealthResponse, ReadyResponse
)
from app.database import (
    db, init_db, get_project_with_services_count, list_projects_with_services_count,
    get_service, list_services_by_project
)
from app.middleware import LoggingMiddleware, CORSMiddleware
from app.config import settings

# Création de l'application FastAPI
app = FastAPI(
    title="NoKube Project Service",
    description="Project and service management for NoKube platform",
    version="1.0.0"
)

# Ajout des middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(CORSMiddleware)

# Events de cycle de vie
@app.on_event("startup")
async def startup():
    """Initialiser la connexion DB au démarrage"""
    await db.connect()
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    """Fermer la connexion DB à l'arrêt"""
    await db.disconnect()

@app.get("/")
async def root(x_user: str = Header(...)):
    """Endpoint racine du Project Service"""
    return {
        "service": "NoKube Project Service",
        "version": settings.VERSION,
        "status": "running",
        "timestamp": datetime.now(),
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "projects": "/projects",
            "services": "/projects/{id}/services",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check du Project Service"""
    return HealthResponse(
        status="healthy",
        service="project-service",
        timestamp=datetime.now()
    )

@app.get("/ready", response_model=ReadyResponse)
async def readiness_check():
    """Readiness check - vérifier la connexion à la base de données"""
    try:
        conn = await db.get_connection()
        await conn.fetchval("SELECT 1")
        await db.release_connection(conn)
        
        return ReadyResponse(
            status="ready",
            service="project-service", 
            database="connected",
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Database not ready: {str(e)}"
        )

# CRUD Operations pour les projets

@app.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, x_user: str = Header(...)):
    """Créer un nouveau projet (authentification via Gateway)"""
    
    conn = await db.get_connection()
    try:
        # Vérifier si le nom du projet existe déjà pour cet utilisateur
        existing = await conn.fetchrow(
            "SELECT id FROM projects WHERE owner = $1 AND name = $2", 
            x_user, project.name
        )
        if existing:
            raise HTTPException(
                status_code=409, 
                detail=f"You already have a project named '{project.name}'"
            )
        
        # Créer le nouveau projet avec l'utilisateur du header X-User comme owner
        new_project = await conn.fetchrow("""
            INSERT INTO projects (name, display_name, description, repository_url, owner)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, display_name, description, repository_url, status, owner, created_at, updated_at
        """, project.name, project.display_name, project.description, 
            project.repository_url, x_user)
        
        # Ajouter services_count = 0 pour nouveau projet
        project_dict = dict(new_project)
        project_dict['services_count'] = 0
        
        return ProjectResponse(**project_dict)
    
    finally:
        await db.release_connection(conn)

@app.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    x_user: str = Header(...),
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
):
    """Lister MES projets avec pagination et comptage des services"""
    
    conn = await db.get_connection()
    try:
        # Compter le total des projets de l'utilisateur
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM projects WHERE owner = $1", 
            x_user
        )
        
        # Récupérer les projets avec le nombre de services
        projects_data = await list_projects_with_services_count(x_user, limit, offset)
        
        return ProjectListResponse(
            projects=[ProjectResponse(**project) for project in projects_data],
            total=total,
            limit=limit,
            offset=offset
        )
    
    finally:
        await db.release_connection(conn)

@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, x_user: str = Header(...)):
    """Récupérer MON projet par son ID avec comptage des services"""
    
    project_data = await get_project_with_services_count(project_id, x_user)
    
    if not project_data:
        raise HTTPException(
            status_code=404, 
            detail=f"Project with id {project_id} not found"
        )
    
    return ProjectResponse(**project_data)

@app.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project_update: ProjectUpdate, x_user: str = Header(...)):
    """Mettre à jour MON projet existant (authentification via Gateway)"""
    
    conn = await db.get_connection()
    try:
        # Vérifier si le projet existe ET appartient à l'utilisateur
        existing = await conn.fetchrow(
            "SELECT id FROM projects WHERE id = $1 AND owner = $2", 
            project_id, x_user
        )
        if not existing:
            raise HTTPException(
                status_code=404, 
                detail=f"Project with id {project_id} not found or access denied"
            )
        
        # Construire la requête UPDATE dynamiquement
        update_data = project_update.dict(exclude_unset=True)
        if not update_data:
            # Aucune donnée à mettre à jour, retourner le projet actuel
            project = await conn.fetchrow("""
                SELECT id, name, description, repository_url, framework, status, owner, created_at, updated_at
                FROM projects WHERE id = $1
            """, project_id)
            return ProjectResponse(**dict(project))
        
        # Construire les clauses SET
        set_clauses = []
        params = []
        param_count = 1
        
        for field, value in update_data.items():
            set_clauses.append(f"{field} = ${param_count}")
            params.append(value)
            param_count += 1
        
        # Ajouter updated_at
        set_clauses.append(f"updated_at = ${param_count}")
        params.append(datetime.now())
        param_count += 1
        
        # Ajouter project_id pour WHERE
        params.append(project_id)
        
        query = f"""
            UPDATE projects 
            SET {', '.join(set_clauses)}
            WHERE id = ${param_count}
            RETURNING id, name, description, repository_url, framework, status, owner, created_at, updated_at
        """
        
        updated_project = await conn.fetchrow(query, *params)
        return ProjectResponse(**dict(updated_project))
    
    finally:
        await db.release_connection(conn)

@app.delete("/projects/{project_id}")
async def delete_project(project_id: int, x_user: str = Header(...)):
    """Supprimer MON projet (authentification via Gateway)"""
    
    conn = await db.get_connection()
    try:
        # Récupérer le projet avant suppression (vérifier propriété)
        project = await conn.fetchrow("""
            SELECT id, name FROM projects WHERE id = $1 AND owner = $2
        """, project_id, x_user)
        
        if not project:
            raise HTTPException(
                status_code=404, 
                detail=f"Project with id {project_id} not found or access denied"
            )
        
        # Supprimer le projet
        await conn.execute("DELETE FROM projects WHERE id = $1 AND owner = $2", project_id, x_user)
        
        return {
            "message": f"Project '{project['name']}' deleted successfully",
            "deleted_project_id": project_id
        }
    
    finally:
        await db.release_connection(conn)


# === SERVICES ENDPOINTS ===

@app.post("/projects/{project_id}/services", response_model=ServiceResponse)
async def create_service(
    project_id: int, 
    service: ServiceCreate, 
    x_user: str = Header(...)
):
    """Créer un nouveau service dans MON projet"""
    
    conn = await db.get_connection()
    try:
        # Vérifier que le projet existe et appartient à l'utilisateur
        project = await conn.fetchrow(
            "SELECT id FROM projects WHERE id = $1 AND owner = $2",
            project_id, x_user
        )
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found or access denied"
            )
        
        # Vérifier que le nom du service n'existe pas déjà dans ce projet
        existing = await conn.fetchrow(
            "SELECT id FROM services WHERE project_id = $1 AND name = $2",
            project_id, service.name
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Service '{service.name}' already exists in this project"
            )
        
        # Créer le nouveau service
        new_service = await conn.fetchrow("""
            INSERT INTO services (project_id, name, display_name, description, service_type)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, project_id, name, display_name, description, service_type, status, created_at, updated_at
        """, project_id, service.name, service.display_name, 
            service.description, service.service_type.value)
        
        return ServiceResponse(**dict(new_service))
    
    finally:
        await db.release_connection(conn)

@app.get("/projects/{project_id}/services", response_model=ServiceListResponse)
async def list_project_services(
    project_id: int,
    x_user: str = Header(...),
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
):
    """Lister tous les services de MON projet"""
    
    # Vérifier que le projet existe et appartient à l'utilisateur
    conn = await db.get_connection()
    try:
        project = await conn.fetchrow(
            "SELECT id FROM projects WHERE id = $1 AND owner = $2",
            project_id, x_user
        )
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found or access denied"
            )
        
        # Compter le total des services
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM services WHERE project_id = $1",
            project_id
        )
        
        # Récupérer les services
        services_data = await list_services_by_project(project_id, x_user, limit, offset)
        
        return ServiceListResponse(
            services=[ServiceResponse(**service) for service in services_data],
            total=total,
            limit=limit,
            offset=offset,
            project_id=project_id
        )
    
    finally:
        await db.release_connection(conn)

@app.get("/projects/{project_id}/services/{service_id}", response_model=ServiceResponse)
async def get_service_detail(
    project_id: int,
    service_id: int, 
    x_user: str = Header(...)
):
    """Récupérer un service spécifique de MON projet"""
    
    service_data = await get_service(service_id, x_user)
    
    if not service_data or service_data['project_id'] != project_id:
        raise HTTPException(
            status_code=404,
            detail=f"Service {service_id} not found in project {project_id}"
        )
    
    return ServiceResponse(**service_data)

@app.put("/projects/{project_id}/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    project_id: int,
    service_id: int,
    service_update: ServiceUpdate,
    x_user: str = Header(...)
):
    """Mettre à jour un service de MON projet"""
    
    conn = await db.get_connection()
    try:
        # Vérifier que le service existe et appartient à l'utilisateur
        existing = await conn.fetchrow("""
            SELECT s.id FROM services s
            JOIN projects p ON s.project_id = p.id
            WHERE s.id = $1 AND s.project_id = $2 AND p.owner = $3
        """, service_id, project_id, x_user)
        
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Service {service_id} not found in project {project_id}"
            )
        
        # Construire la requête UPDATE dynamiquement
        update_data = service_update.dict(exclude_unset=True)
        if not update_data:
            # Aucune donnée à mettre à jour
            service_data = await get_service(service_id, x_user)
            return ServiceResponse(**service_data)
        
        # Construire les clauses SET
        set_clauses = []
        params = []
        param_count = 1
        
        for field, value in update_data.items():
            if field == 'service_type' and hasattr(value, 'value'):
                value = value.value  # Enum to string
            set_clauses.append(f"{field} = ${param_count}")
            params.append(value)
            param_count += 1
        
        # Ajouter updated_at
        set_clauses.append(f"updated_at = ${param_count}")
        params.append(datetime.now())
        param_count += 1
        
        # Ajouter service_id pour WHERE
        params.append(service_id)
        
        query = f"""
            UPDATE services 
            SET {', '.join(set_clauses)}
            WHERE id = ${param_count}
            RETURNING id, project_id, name, display_name, description, service_type, status, created_at, updated_at
        """
        
        updated_service = await conn.fetchrow(query, *params)
        return ServiceResponse(**dict(updated_service))
    
    finally:
        await db.release_connection(conn)

@app.delete("/projects/{project_id}/services/{service_id}")
async def delete_service(
    project_id: int,
    service_id: int,
    x_user: str = Header(...)
):
    """Supprimer un service de MON projet"""
    
    conn = await db.get_connection()
    try:
        # Récupérer le service avant suppression (vérifier propriété)
        service = await conn.fetchrow("""
            SELECT s.id, s.name FROM services s
            JOIN projects p ON s.project_id = p.id
            WHERE s.id = $1 AND s.project_id = $2 AND p.owner = $3
        """, service_id, project_id, x_user)
        
        if not service:
            raise HTTPException(
                status_code=404,
                detail=f"Service {service_id} not found in project {project_id}"
            )
        
        # Supprimer le service
        await conn.execute(
            "DELETE FROM services WHERE id = $1", 
            service_id
        )
        
        return {
            "message": f"Service '{service['name']}' deleted successfully",
            "deleted_service_id": service_id,
            "project_id": project_id
        }
    
    finally:
        await db.release_connection(conn)

# Endpoint /deploy supprimé - Le déploiement se fait maintenant via Monitor Service

# Gestion des erreurs globales
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Endpoint not found",
        "message": f"The endpoint {request.url.path} does not exist",
        "available_endpoints": [
            "/health",
            "/ready", 
            "/projects",
            "/projects/{id}",
            "/projects/{id}/services",
            "/projects/{id}/services/{service_id}"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)