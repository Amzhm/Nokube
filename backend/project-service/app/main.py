from fastapi import FastAPI, HTTPException, Header
from datetime import datetime
from typing import List, Optional
from app.config import settings
from app.schemas import (
    ProjectCreate, ProjectResponse, ProjectUpdate, 
    HealthResponse, ProjectListResponse
)
from app.database import db, init_db
from app.middleware import LoggingMiddleware, CORSMiddleware

# Création de l'application FastAPI
app = FastAPI(
    title=settings.TITLE,
    description=settings.DESCRIPTION,
    version=settings.VERSION
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
            "projects": "/projects",
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

# CRUD Operations pour les projets

@app.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, x_user: str = Header(...)):
    """Créer un nouveau projet (authentification via Gateway)"""
    
    conn = await db.get_connection()
    try:
        # Vérifier si le nom du projet existe déjà
        existing = await conn.fetchrow(
            "SELECT id FROM projects WHERE name = $1", 
            project.name
        )
        if existing:
            raise HTTPException(
                status_code=409, 
                detail=f"Project with name '{project.name}' already exists"
            )
        
        # Créer le nouveau projet avec l'utilisateur du header X-User comme owner
        new_project = await conn.fetchrow("""
            INSERT INTO projects (name, description, repository_url, framework, owner)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, description, repository_url, framework, status, owner, created_at, updated_at
        """, project.name, project.description, project.repository_url, 
            project.framework, x_user)
        
        return ProjectResponse(**dict(new_project))
    
    finally:
        await db.release_connection(conn)

@app.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    x_user: str = Header(...),
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
):
    """Lister MES projets avec pagination (authentification via Gateway)"""
    
    conn = await db.get_connection()
    try:
        # Compter le total des projets de l'utilisateur
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM projects WHERE owner = $1", 
            x_user
        )
        
        # Récupérer les projets de l'utilisateur avec pagination
        projects = await conn.fetch("""
            SELECT id, name, description, repository_url, framework, status, owner, created_at, updated_at
            FROM projects 
            WHERE owner = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """, x_user, limit, offset)
        
        return ProjectListResponse(
            projects=[ProjectResponse(**dict(p)) for p in projects],
            total=total,
            limit=limit,
            offset=offset
        )
    
    finally:
        await db.release_connection(conn)

@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, x_user: str = Header(...)):
    """Récupérer MON projet par son ID (authentification via Gateway)"""
    
    conn = await db.get_connection()
    try:
        project = await conn.fetchrow("""
            SELECT id, name, description, repository_url, framework, status, owner, created_at, updated_at
            FROM projects 
            WHERE id = $1 AND owner = $2
        """, project_id, x_user)
        
        if not project:
            raise HTTPException(
                status_code=404, 
                detail=f"Project with id {project_id} not found"
            )
        
        return ProjectResponse(**dict(project))
    
    finally:
        await db.release_connection(conn)

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

@app.post("/projects/{project_id}/deploy")
async def deploy_project(project_id: int, x_user: str = Header(...)):
    """Déclencher le déploiement de MON projet (authentification requise)"""
    
    conn = await db.get_connection()
    try:
        # Vérifier si le projet existe ET appartient à l'utilisateur
        project = await conn.fetchrow("""
            SELECT id, name, status FROM projects WHERE id = $1 AND owner = $2
        """, project_id, x_user)
        
        if not project:
            raise HTTPException(
                status_code=404, 
                detail=f"Project with id {project_id} not found or access denied"
            )
        
        # Mettre à jour le statut du projet
        await conn.execute("""
            UPDATE projects 
            SET status = 'deploying', updated_at = $1 
            WHERE id = $2 AND owner = $3
        """, datetime.now(), project_id, x_user)
        
        return {
            "message": f"Deployment started for project '{project['name']}'",
            "project_id": project_id,
            "status": "deploying",
            "namespace": settings.get_project_namespace(project['name'])
        }
    
    finally:
        await db.release_connection(conn)

# Gestion des erreurs globales
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Endpoint not found",
        "message": f"The endpoint {request.url.path} does not exist",
        "available_endpoints": [
            "/health",
            "/projects",
            "/projects/{id}",
            "/projects/{id}/deploy"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)