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
        print("Build Service: Database connection pool created")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("Build Service: Database connection pool closed")
    
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
    """Create builds table if it doesn't exist (shared DB with users/projects tables)"""
    conn = await db.get_connection()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS builds (
                build_id VARCHAR(255) PRIMARY KEY,
                project_id INTEGER NOT NULL,
                user_id INTEGER,
                username VARCHAR(255) NOT NULL,
                service_name VARCHAR(255) NOT NULL,
                image_name VARCHAR(255) NOT NULL,
                image_full_name VARCHAR(500) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'building',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                build_logs TEXT,
                github_workflow_id VARCHAR(255),
                estimated_duration INTEGER DEFAULT 300
            );
            
            CREATE INDEX IF NOT EXISTS idx_builds_project_id ON builds(project_id);
            CREATE INDEX IF NOT EXISTS idx_builds_username ON builds(username);
            CREATE INDEX IF NOT EXISTS idx_builds_status ON builds(status);
            CREATE INDEX IF NOT EXISTS idx_builds_created_at ON builds(created_at);
        """)
        print("Build Service: builds table initialized in shared NoKube_db")
    finally:
        await db.release_connection(conn)

# Helper functions for builds table operations
async def create_build(build_data: dict) -> str:
    """Créer un nouveau build dans la DB"""
    conn = await db.get_connection()
    try:
        await conn.execute("""
            INSERT INTO builds (
                build_id, project_id, username, service_name, image_name, 
                image_full_name, status, created_at, started_at, estimated_duration
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, 
            build_data['build_id'],
            build_data['project_id'], 
            build_data['username'],
            build_data['service_name'],
            build_data['image_name'],
            build_data['image_full_name'],
            build_data['status'],
            build_data['created_at'],
            build_data.get('started_at'),
            build_data.get('estimated_duration', 300)
        )
        print(f"Build {build_data['build_id']} created in database")
        return build_data['build_id']
    finally:
        await db.release_connection(conn)

async def get_build(build_id: str) -> dict:
    """Récupérer un build par son ID"""
    conn = await db.get_connection()
    try:
        row = await conn.fetchrow("""
            SELECT build_id, project_id, username, service_name, image_name, 
                   image_full_name, status, created_at, started_at, completed_at,
                   error_message, estimated_duration
            FROM builds WHERE build_id = $1
        """, build_id)
        return dict(row) if row else None
    finally:
        await db.release_connection(conn)

async def update_build_status(build_id: str, status: str, **kwargs):
    """Mettre à jour le statut d'un build"""
    conn = await db.get_connection()
    try:
        # Construction dynamique de la requête UPDATE
        set_clauses = ["status = $2"]
        params = [build_id, status]
        param_count = 3
        
        for key, value in kwargs.items():
            if value is not None:
                set_clauses.append(f"{key} = ${param_count}")
                params.append(value)
                param_count += 1
        
        query = f"""
            UPDATE builds 
            SET {', '.join(set_clauses)}
            WHERE build_id = $1
        """
        
        await conn.execute(query, *params)
        print(f"Build {build_id} updated: status={status}")
    finally:
        await db.release_connection(conn)

async def list_builds_by_project(project_id: int, limit: int = 50, offset: int = 0) -> list:
    """Lister les builds d'un projet"""
    conn = await db.get_connection()
    try:
        rows = await conn.fetch("""
            SELECT build_id, project_id, username, service_name, image_name, 
                   image_full_name, status, created_at, started_at, completed_at,
                   error_message, estimated_duration
            FROM builds 
            WHERE project_id = $1 
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """, project_id, limit, offset)
        return [dict(row) for row in rows]
    finally:
        await db.release_connection(conn)

async def list_all_builds(limit: int = 50, offset: int = 0, status: str = None) -> list:
    """Lister tous les builds avec filtres"""
    conn = await db.get_connection()
    try:
        if status:
            rows = await conn.fetch("""
                SELECT build_id, project_id, username, service_name, image_name, 
                       image_full_name, status, created_at, started_at, completed_at,
                       error_message, estimated_duration
                FROM builds 
                WHERE status = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """, status, limit, offset)
        else:
            rows = await conn.fetch("""
                SELECT build_id, project_id, username, service_name, image_name, 
                       image_full_name, status, created_at, started_at, completed_at,
                       error_message, estimated_duration
                FROM builds 
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """, limit, offset)
        return [dict(row) for row in rows]
    finally:
        await db.release_connection(conn)

async def count_builds() -> int:
    """Compter le total des builds"""
    conn = await db.get_connection()
    try:
        return await conn.fetchval("SELECT COUNT(*) FROM builds")
    finally:
        await db.release_connection(conn)