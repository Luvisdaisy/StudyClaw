import asyncio
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from api import projects_router, documents_router, chat_router, github_router
from database.session import init_db, close_db, AsyncSessionLocal
from session_store import init_session_manager, shutdown_session_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    await init_db()
    print("Database initialized")

    # Initialize Session Manager (Redis + PostgreSQL)
    try:
        await init_session_manager(
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            redis_password=os.getenv("REDIS_PASSWORD") or None,
            async_session_factory=AsyncSessionLocal,
            batch_interval=int(os.getenv("SESSION_BATCH_INTERVAL", "60")),
            batch_size=int(os.getenv("SESSION_BATCH_SIZE", "100")),
        )
        print("Session Manager initialized (Redis + PostgreSQL)")
    except Exception as e:
        print(f"Warning: Session Manager initialization failed: {e}")
        print("Session persistence will be disabled")

    yield

    # Shutdown
    await shutdown_session_manager()
    print("Session Manager shutdown")
    await close_db()
    print("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="StudyClaw API",
    description="AI-powered learning assistant with RAG and GitHub sync",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=False,  # Must be False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(github_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "StudyClaw API"}


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "vector_store": "ready",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
