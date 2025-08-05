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

# Initialize database tables
async def init_db():
    """Create projects table if it doesn't exist (shared DB with users table)"""
    conn = await db.get_connection()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                repository_url VARCHAR(500) NOT NULL,
                framework VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'created',
                owner VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_project_name ON projects(name);
            CREATE INDEX IF NOT EXISTS idx_project_owner ON projects(owner);
            CREATE INDEX IF NOT EXISTS idx_project_status ON projects(status);
            CREATE INDEX IF NOT EXISTS idx_project_created_at ON projects(created_at);
        """)
        print("Project Service: projects table initialized in shared NoKube_db")
    finally:
        await db.release_connection(conn)