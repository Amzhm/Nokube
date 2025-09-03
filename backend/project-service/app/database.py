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
        print("Project Service: Database connection pool created")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("Project Service: Database connection pool closed")
    
    async def get_connection(self):
        """Get connection from pool"""
        return await self.pool.acquire()
    
    async def release_connection(self, connection):
        """Release connection back to pool"""
        await self.pool.release(connection)

# Global database instance
db = Database()

# Helper functions for database operations
async def get_project_with_services_count(project_id: int, owner: str):
    """Get project with services count"""
    conn = await db.get_connection()
    try:
        project = await conn.fetchrow("""
            SELECT p.*, 
                   (SELECT COUNT(*) FROM services s WHERE s.project_id = p.id) as services_count
            FROM projects p
            WHERE p.id = $1 AND p.owner = $2
        """, project_id, owner)
        return dict(project) if project else None
    finally:
        await db.release_connection(conn)

async def list_projects_with_services_count(owner: str, limit: int = 50, offset: int = 0):
    """List projects with services count"""
    conn = await db.get_connection()
    try:
        projects = await conn.fetch("""
            SELECT p.*, 
                   (SELECT COUNT(*) FROM services s WHERE s.project_id = p.id) as services_count
            FROM projects p
            WHERE p.owner = $1
            ORDER BY p.created_at DESC
            LIMIT $2 OFFSET $3
        """, owner, limit, offset)
        return [dict(project) for project in projects]
    finally:
        await db.release_connection(conn)

# Service helper functions
async def get_service(service_id: int, project_owner: str):
    """Get service ensuring project ownership"""
    conn = await db.get_connection()
    try:
        service = await conn.fetchrow("""
            SELECT s.* FROM services s
            JOIN projects p ON s.project_id = p.id
            WHERE s.id = $1 AND p.owner = $2
        """, service_id, project_owner)
        return dict(service) if service else None
    finally:
        await db.release_connection(conn)

async def list_services_by_project(project_id: int, project_owner: str, limit: int = 50, offset: int = 0):
    """List services by project ensuring ownership"""
    conn = await db.get_connection()
    try:
        services = await conn.fetch("""
            SELECT s.* FROM services s
            JOIN projects p ON s.project_id = p.id
            WHERE s.project_id = $1 AND p.owner = $2
            ORDER BY s.created_at DESC
            LIMIT $3 OFFSET $4
        """, project_id, project_owner, limit, offset)
        return [dict(service) for service in services]
    finally:
        await db.release_connection(conn)

# Database initialization and migration
async def init_db():
    """Create projects and services tables - clean and minimal structure"""
    conn = await db.get_connection()
    try:
        # Table PROJECTS - Container logique simple
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,                    -- Nom unique du projet
                display_name VARCHAR(150),                     -- Nom affiché (optionnel)
                description TEXT,
                repository_url VARCHAR(500) NOT NULL,          -- URL du repo principal
                
                -- Ownership
                owner VARCHAR(100) NOT NULL,
                
                -- Status global
                status VARCHAR(20) DEFAULT 'created',
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraint: un owner ne peut pas avoir 2 projets avec le même nom
                UNIQUE(owner, name)
            );
            
            -- Table SERVICES - Microservices dans un projet
            CREATE TABLE IF NOT EXISTS services (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                
                -- Identification basique
                name VARCHAR(100) NOT NULL,                   -- Nom technique (frontend, api, worker)
                display_name VARCHAR(150),                    -- Nom affiché (optionnel)
                description TEXT,
                
                -- Type de service
                service_type VARCHAR(20) DEFAULT 'web',       -- web, api, worker
                
                -- Status
                status VARCHAR(20) DEFAULT 'created',
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraint: un projet ne peut pas avoir 2 services avec le même nom
                UNIQUE(project_id, name)
            );
            
            -- Indexes essentiels
            CREATE INDEX IF NOT EXISTS idx_project_owner ON projects(owner);
            CREATE INDEX IF NOT EXISTS idx_project_name ON projects(name);
            CREATE INDEX IF NOT EXISTS idx_service_project_id ON services(project_id);
            CREATE INDEX IF NOT EXISTS idx_service_name ON services(name);
        """)
        
        print("Project Service: Clean projects & services tables initialized")
        
        # Run migration if needed
        await migrate_existing_data(conn)
        
    finally:
        await db.release_connection(conn)


async def migrate_existing_data(conn):
    """Migrate existing project data to new structure"""
    try:
        # Check if old columns exist (repository_url, framework)
        old_columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'projects' AND column_name IN ('framework', 'repository_url')
        """)
        
        if len(old_columns) == 2:
            print("Migrating existing project data to new structure...")
            
            # 1. Add new columns if they don't exist
            try:
                await conn.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS display_name VARCHAR(150)")
                await conn.execute("ALTER TABLE projects DROP COLUMN IF EXISTS framework")
                print("Migration: Updated projects table structure")
            except Exception as e:
                print(f"Migration warning: {e}")
            
            # 2. Update constraints if needed
            try:
                await conn.execute("ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_name_key")
                await conn.execute("ALTER TABLE projects ADD CONSTRAINT projects_owner_name_key UNIQUE (owner, name)")
                print("Migration: Updated constraints")
            except Exception as e:
                print(f"Migration warning: {e}")
                
            print("Migration completed successfully")
        else:
            print("No migration needed - schema is up to date")
            
    except Exception as e:
        print(f"Migration error: {e} - continuing with current schema")