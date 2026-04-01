"""
FastAPI application entry point.
"""
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from server.config import settings
from server.models.database import init_db, close_db, get_db_session
from server.routers.auth import router as auth_router
from server.routers.knowledge_bases import router as kb_router
from server.routers.documents import router as documents_router
from server.routers.query import router as query_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup: Initialize database
    await init_db()
    print(f"✅ Database initialized")
    
    yield
    
    # Shutdown: Close database connections
    await close_db()
    print(f"🔒 Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="RAG-Anything Server",
    description="Multi-Tenant Knowledge Base API with RAG Capabilities",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Note: Database session is now added via dependency injection in each route
# instead of using middleware to avoid event loop issues in tests.
# The get_db_session dependency should be used directly in routes.


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__
        }
    )


# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(kb_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(query_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Check API health status."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": time.time()
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RAG-Anything Server",
        "version": "0.1.0",
        "description": "Multi-Tenant Knowledge Base API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
