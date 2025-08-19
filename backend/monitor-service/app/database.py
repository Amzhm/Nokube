import asyncpg
from app.config import settings

class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Create connection pool to PostgreSQL"""
        self.pool = await asyncpg.create_pool(
            host=settings.db_host,
            port=int(settings.db_port),
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            min_size=5,
            max_size=20,
        )
        print("Monitor Service: Database connection pool created")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("Monitor Service: Database connection pool closed")
    
    async def get_connection(self):
        """Get connection from pool"""
        return await self.pool.acquire()
    
    async def release_connection(self, connection):
        """Release connection back to pool"""
        await self.pool.release(connection)

# Global database instance
db = Database()

# Initialize database tables
async def init_db():
    """Create deployments table if it doesn't exist (shared DB with users/projects/builds tables)"""
    conn = await db.get_connection()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                deployment_id VARCHAR(255) PRIMARY KEY,
                project_id INTEGER NOT NULL,
                user_id INTEGER,
                username VARCHAR(255) NOT NULL,
                service_name VARCHAR(255) NOT NULL,
                display_name VARCHAR(255) NOT NULL,
                description TEXT,
                image_name VARCHAR(255) NOT NULL,
                image_full_name VARCHAR(500),
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                replicas_ready INTEGER DEFAULT 0,
                replicas_total INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                access_url VARCHAR(500),
                namespace_name VARCHAR(255),
                manifests_generated TEXT[], -- Array of manifest types generated
                health_check_enabled BOOLEAN DEFAULT true,
                liveness_check_path VARCHAR(255),
                readiness_check_path VARCHAR(255)
            );
            
            CREATE INDEX IF NOT EXISTS idx_deployments_project_id ON deployments(project_id);
            CREATE INDEX IF NOT EXISTS idx_deployments_username ON deployments(username);
            CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);
            CREATE INDEX IF NOT EXISTS idx_deployments_created_at ON deployments(created_at);
            CREATE INDEX IF NOT EXISTS idx_deployments_namespace ON deployments(namespace_name);
        """)
        print("Monitor Service: deployments table initialized in shared NoKube_db")
    finally:
        await db.release_connection(conn)

# Helper functions for deployments table operations
async def create_deployment(deployment_data: dict) -> str:
    """Créer un nouveau déploiement dans la DB"""
    conn = await db.get_connection()
    try:
        await conn.execute("""
            INSERT INTO deployments (
                deployment_id, project_id, username, service_name, display_name, 
                description, image_name, image_full_name, status, replicas_total, 
                created_at, access_url, namespace_name, manifests_generated,
                health_check_enabled, liveness_check_path, readiness_check_path
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
        """, 
            deployment_data['deployment_id'],
            deployment_data['project_id'], 
            deployment_data['username'],
            deployment_data['service_name'],
            deployment_data.get('display_name', ''),
            deployment_data.get('description'),
            deployment_data['image_name'],
            deployment_data.get('image_full_name'),
            deployment_data['status'],
            deployment_data.get('replicas_total', 1),
            deployment_data['created_at'],
            deployment_data.get('access_url'),
            deployment_data.get('namespace_name'),
            deployment_data.get('manifests_generated', []),
            deployment_data.get('health_check_enabled', True),
            deployment_data.get('liveness_check_path'),
            deployment_data.get('readiness_check_path')
        )
        print(f"Deployment {deployment_data['deployment_id']} created in database")
        return deployment_data['deployment_id']
    finally:
        await db.release_connection(conn)

async def get_deployment(deployment_id: str) -> dict:
    """Récupérer un déploiement par son ID"""
    conn = await db.get_connection()
    try:
        row = await conn.fetchrow("""
            SELECT deployment_id, project_id, username, service_name, display_name,
                   description, image_name, image_full_name, status, replicas_ready,
                   replicas_total, created_at, updated_at, completed_at, error_message,
                   access_url, namespace_name, manifests_generated, health_check_enabled,
                   liveness_check_path, readiness_check_path
            FROM deployments WHERE deployment_id = $1
        """, deployment_id)
        return dict(row) if row else None
    finally:
        await db.release_connection(conn)

async def update_deployment_status(deployment_id: str, status: str, **kwargs):
    """Mettre à jour le statut d'un déploiement"""
    conn = await db.get_connection()
    try:
        # Construction dynamique de la requête UPDATE
        set_clauses = ["status = $2", "updated_at = CURRENT_TIMESTAMP"]
        params = [deployment_id, status]
        param_count = 3
        
        for key, value in kwargs.items():
            if value is not None:
                set_clauses.append(f"{key} = ${param_count}")
                params.append(value)
                param_count += 1
        
        query = f"""
            UPDATE deployments 
            SET {', '.join(set_clauses)}
            WHERE deployment_id = $1
        """
        
        await conn.execute(query, *params)
        print(f"Deployment {deployment_id} updated: status={status}")
    finally:
        await db.release_connection(conn)

async def list_deployments_by_project(project_id: int, limit: int = 50, offset: int = 0) -> list:
    """Lister les déploiements d'un projet"""
    conn = await db.get_connection()
    try:
        rows = await conn.fetch("""
            SELECT deployment_id, project_id, username, service_name, display_name,
                   description, image_name, image_full_name, status, replicas_ready,
                   replicas_total, created_at, updated_at, completed_at, error_message,
                   access_url, namespace_name, manifests_generated
            FROM deployments 
            WHERE project_id = $1 
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """, project_id, limit, offset)
        return [dict(row) for row in rows]
    finally:
        await db.release_connection(conn)

async def count_deployments() -> int:
    """Compter le total des déploiements"""
    conn = await db.get_connection()
    try:
        return await conn.fetchval("SELECT COUNT(*) FROM deployments")
    finally:
        await db.release_connection(conn)

async def count_deployments_by_status() -> dict:
    """Compter les déploiements par statut"""
    conn = await db.get_connection()
    try:
        rows = await conn.fetch("SELECT status, COUNT(*) as count FROM deployments GROUP BY status")
        return {row['status']: row['count'] for row in rows}
    finally:
        await db.release_connection(conn)