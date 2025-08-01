from fastapi import FastAPI, HTTPException, Header
from datetime import datetime
import asyncpg
from app.database import db, init_db
from app.schemas import (
    UserRegister, UserLogin, UserResponse, LoginResponse, 
    RegisterResponse, HealthResponse, ReadyResponse, Token
)
from app.auth import hash_password, verify_password, create_access_token, verify_token, get_token_from_header

app = FastAPI(
    title="NoKube Auth Service",
    description="Authentication microservice for NoKube platform",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    """Initialize database connection and tables"""
    await db.connect()
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    """Close database connection"""
    await db.disconnect()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="auth-service",
        timestamp=datetime.now()
    )

@app.get("/ready", response_model=ReadyResponse)
async def readiness_check():
    """Readiness check - verify database connection"""
    try:
        conn = await db.get_connection()
        await conn.fetchval("SELECT 1")
        await db.release_connection(conn)
        
        return ReadyResponse(status="ready", database="connected")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database not ready: {str(e)}")

@app.post("/register", response_model=RegisterResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    conn = await db.get_connection()
    try:
        # Check if user already exists
        existing_user = await conn.fetchrow(
            "SELECT id FROM users WHERE username = $1 OR email = $2",
            user_data.username, user_data.email
        )
        
        if existing_user:
            raise HTTPException(status_code=409, detail="Username or email already exists")
        
        # Hash password and create user
        password_hash = hash_password(user_data.password)
        
        user_record = await conn.fetchrow("""
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            RETURNING id, username, email, is_active, created_at
        """, user_data.username, user_data.email, password_hash)
        
        # Create user response
        user = UserResponse(**user_record)
        
        # Generate JWT token
        token = create_access_token({
            "sub": user.username,
            "user_id": user.id
        })
        
        return RegisterResponse(
            message="User registered successfully",
            user=user,
            token=Token(access_token=token)
        )
        
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail="Username or email already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    finally:
        await db.release_connection(conn)

@app.post("/login", response_model=LoginResponse)
async def login(user_data: UserLogin):
    """Authenticate user and return JWT token"""
    conn = await db.get_connection()
    try:
        # Get user from database
        user_record = await conn.fetchrow(
            "SELECT id, username, email, password_hash, is_active, created_at, last_login FROM users WHERE username = $1",
            user_data.username
        )
        
        if not user_record:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(user_data.password, user_record['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user_record['is_active']:
            raise HTTPException(status_code=401, detail="Account is disabled")
        
        # Update last login
        await conn.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
            user_record['id']
        )
        
        # Create user response (exclude password_hash)
        user = UserResponse(
            id=user_record['id'],
            username=user_record['username'],
            email=user_record['email'],
            is_active=user_record['is_active'],
            created_at=user_record['created_at'],
            last_login=datetime.now()
        )
        
        # Generate JWT token
        token = create_access_token({
            "sub": user.username,
            "user_id": user.id
        })
        
        return LoginResponse(
            message="Login successful",
            user=user,
            token=Token(access_token=token)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    finally:
        await db.release_connection(conn)

@app.get("/verify", response_model=UserResponse)
async def verify_token_endpoint(authorization: str = Header(None)):
    """Verify JWT token and return user info"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        # Extract token from header
        token = get_token_from_header(authorization)
        
        # Verify token
        token_data = verify_token(token)
        
        # Get user from database
        conn = await db.get_connection()
        try:
            user_record = await conn.fetchrow(
                "SELECT id, username, email, is_active, created_at, last_login FROM users WHERE id = $1",
                token_data.user_id
            )
            
            if not user_record:
                raise HTTPException(status_code=401, detail="User not found")
            
            if not user_record['is_active']:
                raise HTTPException(status_code=401, detail="Account is disabled")
            
            return UserResponse(**user_record)
            
        finally:
            await db.release_connection(conn)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)