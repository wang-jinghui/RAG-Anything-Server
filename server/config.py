"""
Server configuration and settings.
"""
import os
from typing import Optional, List
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
    
    # RAG Processing Configuration
    RAG_WORKING_DIR: str = "./rag_storage"
    CHUNK_TOKEN_SIZE: int = 1200
    CHUNK_OVERLAP_TOKEN_SIZE: int = 100
    DEFAULT_QUERY_MODE: str = "hybrid"
    DEFAULT_TOP_K: int = 10
    
    # Document Parser Configuration
    PARSER_METHOD: str = "mineru"
    PARSER: str = "mineru"
    MINERU_MODE: str = "remote"
    MINERU_API_TOKEN: str = ""
    MINERU_API_BASE_URL: str = "https://mineru.net"
    MINERU_API_EXTRACT_ENDPOINT: str = "/api/v4/extract/task"
    MINERU_API_BATCH_ENDPOINT: str = "/api/v4/file-urls/batch"
    MINERU_MODEL_VERSION: str = "vlm"
    ENABLE_IMAGE_PROCESSING: bool = True
    ENABLE_OCR: bool = True
    
    # LLM Configuration (OpenAI-compatible)
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BINDING: str = "ollama"
    LLM_BINDING_HOST: str = "http://localhost:11434"
    LLM_BINDING_API_KEY: Optional[str] = None
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
    
    # Embedding Configuration
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_BINDING: str = "ollama"
    EMBEDDING_BINDING_HOST: str = "http://localhost:11434"
    EMBEDDING_BINDING_API_KEY: Optional[str] = None
    EMBEDDING_DIM: int = 3072
    
    # OpenAI Compatible API Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    # LightRAG Storage Selection
    LIGHTRAG_KV_STORAGE: str = "PGKVStorage"
    LIGHTRAG_DOC_STATUS_STORAGE: str = "PGDocStatusStorage"
    LIGHTRAG_VECTOR_STORAGE: str = "PGVectorStorage"
    LIGHTRAG_GRAPH_STORAGE: str = "Neo4JStorage"
    
    # PostgreSQL Configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DATABASE: str = "raganything"
    POSTGRES_MAX_CONNECTIONS: int = 25
    
    # PostgreSQL Vector Storage Configuration
    POSTGRES_VECTOR_INDEX_TYPE: str = "HNSW"
    POSTGRES_HNSW_M: int = 16
    POSTGRES_HNSW_EF: int = 200
    POSTGRES_IVFFLAT_LISTS: int = 100
    POSTGRES_VCHORDRQ_BUILD_OPTIONS: str = ""
    POSTGRES_VCHORDRQ_PROBES: str = ""
    POSTGRES_VCHORDRQ_EPSILON: float = 1.9
    
    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = 100
    NEO4J_CONNECTION_TIMEOUT: int = 30
    NEO4J_CONNECTION_ACQUISITION_TIMEOUT: int = 30
    NEO4J_MAX_TRANSACTION_RETRY_TIME: int = 30
    NEO4J_MAX_CONNECTION_LIFETIME: int = 300
    NEO4J_LIVENESS_CHECK_TIMEOUT: int = 30
    NEO4J_KEEP_ALIVE: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    RAG_LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'ignore'  # Ignore unknown environment variables


# Global settings instance
settings = ServerSettings()


def get_settings() -> ServerSettings:
    """Get server settings."""
    return settings
