"""
Server configuration and settings.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class ServerSettings(BaseSettings):
    """Server configuration from environment variables."""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/raganything"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # API Key
    API_KEY_PREFIX: str = "rak_"  # RAG Anything Key
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: set[str] = {
        ".pdf", ".doc", ".docx", ".txt", ".md",
        ".png", ".jpg", ".jpeg", ".bmp", ".tiff",
        ".ppt", ".pptx", ".xls", ".xlsx"
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = ServerSettings()


def get_settings() -> ServerSettings:
    """Get server settings."""
    return settings
