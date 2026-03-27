"""
RAG configuration for document processing and querying.
"""
import os
from typing import Optional, Dict, Any, Callable
from pydantic import BaseModel, Field
from dataclasses import dataclass, field


@dataclass
class EmbeddingFunc:
    """Embedding function configuration."""
    embedding_dim: int = Field(default=768)
    max_token_size: int = Field(default=8192)
    func: Optional[Callable] = None
    
    def __post_init__(self):
        if self.embedding_dim is None or self.max_token_size is None:
            raise ValueError("embedding_dim and max_token_size must be provided")


@dataclass
class LLMConfig:
    """LLM configuration supporting multiple providers."""
    
    # Provider selection
    provider: str = "openai"  # openai, azure, vllm, lmstudio, ollama
    
    # OpenAI-compatible settings
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    
    # Azure-specific (optional)
    azure_deployment: Optional[str] = None
    azure_api_version: Optional[str] = None
    
    # Generation parameters
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    
    # Timeout and retry
    timeout: int = 120
    max_retries: int = 3


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""
    
    # Provider selection
    provider: str = "openai"  # openai, azure, vllm, ollama, huggingface
    
    # Model settings
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"))
    
    # Dimensions
    embedding_dim: int = 3072  # Adjust based on model
    
    # Batch processing
    batch_size: int = 32
    max_async: int = 16


@dataclass
class RankConfig:
    """Ranking model configuration (for re-ranking retrieved results)."""
    
    # Enable/disable reranking
    enabled: bool = False
    
    # Provider (currently only supports BGE-M3 via FlagEmbedding)
    model_name: str = "BAAI/bge-m3"
    
    # Parameters
    top_k: int = 10
    batch_size: int = 32


@dataclass
class VectorStorageConfig:
    """Vector storage backend configuration."""
    
    # Storage type
    storage_type: str = "pgvector"  # pgvector, milvus, qdrant, chroma
    
    # PostgreSQL/PGVector settings
    postgres_user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    postgres_password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "postgres"))
    postgres_host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    postgres_port: int = 5432
    postgres_database: str = "raganything"
    
    # Milvus settings (if using Milvus)
    milvus_uri: str = "./milvus_local.db"
    
    # Qdrant settings (if using Qdrant)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    
    # Chroma settings (if using Chroma)
    chroma_path: str = "./chroma_db"


@dataclass
class GraphStorageConfig:
    """Graph storage backend configuration (for knowledge graph)."""
    
    # Storage type
    storage_type: str = "neo4j"  # neo4j, age
    
    # Neo4j settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Apache AGE settings (if using AGE)
    age_postgres_uri: Optional[str] = None


@dataclass
class RAGConfig:
    """
    Complete RAG configuration combining all components.
    
    Usage:
        config = RAGConfig(
            llm=LLMConfig(provider="openai", model="gpt-4o-mini"),
            embedding=EmbeddingConfig(provider="openai", model="text-embedding-3-large"),
            vector_storage=VectorStorageConfig(storage_type="pgvector"),
            graph_storage=GraphStorageConfig(storage_type="neo4j"),
        )
    """
    
    # Core components
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    rank: Optional[RankConfig] = None
    
    # Storage backends
    vector_storage: VectorStorageConfig = field(default_factory=VectorStorageConfig)
    graph_storage: GraphStorageConfig = field(default_factory=GraphStorageConfig)
    
    # Processing settings
    chunk_token_size: int = 1200
    chunk_overlap_token_size: int = 100
    max_gleanings: int = 1
    
    # Query settings
    default_query_mode: str = "hybrid"  # local, global, hybrid, naive, mix, bypass
    default_top_k: int = 10
    
    # Working directory for LightRAG
    working_dir: str = "./rag_storage"
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "RAGConfig":
        """
        Create RAGConfig from environment variables.
        
        Environment variables:
            LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL
            EMBEDDING_PROVIDER, EMBEDDING_MODEL
            VECTOR_STORAGE_TYPE, POSTGRES_*
            GRAPH_STORAGE_TYPE, NEO4J_*
            WORKING_DIR, CHUNK_TOKEN_SIZE, etc.
        """
        return cls(
            llm=LLMConfig(
                provider=os.getenv("LLM_PROVIDER", "openai"),
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY", ""),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            ),
            embedding=EmbeddingConfig(
                provider=os.getenv("EMBEDDING_PROVIDER", "openai"),
                model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"),
                api_key=os.getenv("OPENAI_API_KEY", ""),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                embedding_dim=int(os.getenv("EMBEDDING_DIM", "3072")),
            ),
            vector_storage=VectorStorageConfig(
                storage_type=os.getenv("VECTOR_STORAGE_TYPE", "pgvector"),
                postgres_user=os.getenv("POSTGRES_USER", "postgres"),
                postgres_password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
                postgres_database=os.getenv("POSTGRES_DATABASE", "raganything"),
            ),
            graph_storage=GraphStorageConfig(
                storage_type=os.getenv("GRAPH_STORAGE_TYPE", "neo4j"),
                neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
                neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
            ),
            working_dir=os.getenv("RAG_WORKING_DIR", "./rag_storage"),
            chunk_token_size=int(os.getenv("CHUNK_TOKEN_SIZE", "1200")),
        )
    
    def to_lightrag_kwargs(self) -> Dict[str, Any]:
        """
        Convert to LightRAG initialization kwargs.
        
        Returns dict compatible with LightRAG() constructor.
        """
        kwargs = {
            "working_dir": self.working_dir,
            "chunk_token_size": self.chunk_token_size,
            "chunk_overlap_token_size": self.chunk_overlap_token_size,
            "max_gleanings": self.max_gleanings,
            "log_level": self.log_level,
        }
        
        # Add storage configurations
        if self.vector_storage.storage_type == "pgvector":
            kwargs["vector_storage"] = "PGVectorStorage"
            kwargs["kv_storage"] = "PGKVStorage"
            kwargs["doc_status_storage"] = "PGDocStatusStorage"
        
        if self.graph_storage.storage_type == "neo4j":
            kwargs["graph_storage"] = "Neo4JStorage"
        
        # Add connection strings
        if self.vector_storage.storage_type == "pgvector":
            kwargs["vector_storage_kwargs"] = {
                "host": self.vector_storage.postgres_host,
                "port": self.vector_storage.postgres_port,
                "user": self.vector_storage.postgres_user,
                "password": self.vector_storage.postgres_password,
                "database": self.vector_storage.postgres_database,
            }
        
        if self.graph_storage.storage_type == "neo4j":
            kwargs["graph_storage_kwargs"] = {
                "uri": self.graph_storage.neo4j_uri,
                "user": self.graph_storage.neo4j_user,
                "password": self.graph_storage.neo4j_password,
            }
        
        return kwargs


# Example configurations for common setups
OPENAI_CONFIG = RAGConfig(
    llm=LLMConfig(provider="openai", model="gpt-4o-mini"),
    embedding=EmbeddingConfig(provider="openai", model="text-embedding-3-large"),
)

LOCAL_LMSTUDIO_CONFIG = RAGConfig(
    llm=LLMConfig(
        provider="lmstudio",
        base_url="http://localhost:1234/v1",
        model="local-model",
        api_key="not-needed",
    ),
    embedding=EmbeddingConfig(
        provider="ollama",
        base_url="http://localhost:11434/api",
        model="nomic-embed-text",
    ),
    vector_storage=VectorStorageConfig(storage_type="chroma"),
)

AZURE_CONFIG = RAGConfig(
    llm=LLMConfig(
        provider="azure",
        azure_deployment=os.getenv("AZURE_LLM_DEPLOYMENT", ""),
        azure_api_version=os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
    ),
    embedding=EmbeddingConfig(
        provider="azure",
        azure_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT", ""),
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
    ),
)
