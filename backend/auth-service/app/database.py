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
        print("Database connection pool created")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("Database connection pool closed")
    
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
    """Create tables if they don't exist"""
    conn = await db.get_connection()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_email ON users(email);
        """)
        print("Database tables initialized")
    finally:
        await db.release_connection(conn)