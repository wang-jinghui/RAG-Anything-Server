"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# Enums
class AccessLevel(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class KBStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class UploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class QueryMode(str, Enum):
    LOCAL = "local"
    GLOBAL = "global"
    HYBRID = "hybrid"
    NAIVE = "naive"
    MIX = "mix"
    BYPASS = "bypass"


# ============ User Schemas ============

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: str = Field(...)
    password: str = Field(...)


class UserResponse(BaseModel):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: str
    username: str
    is_super_admin: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Schema for refreshing access token."""
    refresh_token: str


# ============ Knowledge Base Schemas ============

class KnowledgeBaseCreate(BaseModel):
    """Schema for creating a knowledge base."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    vector_storage_config: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "pgvector"}
    )
    graph_storage_config: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "neo4j"}
    )


class KnowledgeBaseUpdate(BaseModel):
    """Schema for updating a knowledge base."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[KBStatus] = None


class KnowledgeBaseResponse(BaseModel):
    """Schema for knowledge base response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str]
    owner_id: UUID
    lightrag_namespace_prefix: str
    status: KBStatus
    created_at: datetime
    updated_at: datetime
    document_count: int
    total_tokens: str
    access_level: Optional[AccessLevel] = None  # Current user's access level


class GrantAccessRequest(BaseModel):
    """Schema for granting access to a user."""
    user_email: EmailStr
    access_level: AccessLevel


class RevokeAccessRequest(BaseModel):
    """Schema for revoking access from a user."""
    user_id: UUID


class KBUserResponse(BaseModel):
    """Schema for KB user access response."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID
    email: str
    username: str
    access_level: AccessLevel
    granted_at: datetime
    granted_by: Optional[UUID]


# ============ Document Schemas ============

class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    kb_id: UUID
    file_name: str
    file_size: Optional[int]
    mime_type: Optional[str]
    upload_status: UploadStatus
    uploaded_at: datetime
    processed_at: Optional[datetime]
    error_message: Optional[str]


class DocumentListResponse(BaseModel):
    """Schema for document list response."""
    documents: List[DocumentUploadResponse]
    total: int
    skip: int
    limit: int


# ============ API Key Schemas ============

class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: Optional[str] = Field(None, max_length=255)
    knowledge_base_id: Optional[UUID] = None
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """Schema for API key response (includes key only on creation)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    key: Optional[str] = None  # Only returned once on creation
    name: Optional[str]
    knowledge_base_id: Optional[UUID]
    expires_at: Optional[datetime]
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool


class APIKeyMetadataResponse(BaseModel):
    """Schema for API key metadata response (without actual key)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: Optional[str]
    knowledge_base_id: Optional[UUID]
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool


# ============ Query Schemas ============

class QueryRequest(BaseModel):
    """Schema for query request."""
    query: str = Field(..., min_length=1, max_length=10000)
    mode: QueryMode = Field(default=QueryMode.HYBRID)
    top_k: int = Field(default=10, ge=1, le=100)
    max_tokens: Optional[int] = Field(None, ge=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    vlm_enhanced: bool = True
    multimodal_content: Optional[List[Dict[str, Any]]] = None


class QuerySource(BaseModel):
    """Schema for query source (retrieved chunk)."""
    content: str
    score: float
    metadata: Dict[str, Any]
    kb_id: Optional[UUID] = None
    doc_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Schema for query response."""
    answer: str
    sources: List[QuerySource]
    query_mode: str
    processing_time_ms: float
    kb_ids: List[UUID]  # Which KBs were queried


# ============ Health Check ============

class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str
    version: str
    database: str
    timestamp: datetime
