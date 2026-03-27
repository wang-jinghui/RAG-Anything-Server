"""
KnowledgeBase model for metadata management.
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from server.models.database import Base


class KnowledgeBase(Base):
    """
    Knowledge Base metadata model.
    
    Each knowledge base is isolated by namespace prefix in LightRAG storage.
    Multiple users can have access to the same KB through KBUserAccess.
    """
    __tablename__ = "knowledge_bases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lightrag_namespace_prefix = Column(String(100), unique=True, nullable=False, index=True)
    vector_storage_config = Column(JSONB, nullable=False, default=lambda: {"type": "pgvector"})
    graph_storage_config = Column(JSONB, nullable=False, default=lambda: {"type": "neo4j"})
    status = Column(String(50), default="active", nullable=False)  # active, archived, deleted
    document_count = Column(Integer, default=0, nullable=False)
    total_tokens = Column(String(20), default="0", nullable=False)  # Use string for big integers
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="owned_knowledge_bases", foreign_keys=[owner_id])
    
    user_access = relationship(
        "KBUserAccess",
        back_populates="knowledge_base",
        cascade="all, delete-orphan"
    )
    
    documents = relationship(
        "KBDocument",
        back_populates="knowledge_base",
        cascade="all, delete-orphan"
    )
    
    api_keys = relationship(
        "APIKey",
        back_populates="knowledge_base",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_owner_kb_name"),
    )
    
    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, name={self.name}, owner_id={self.owner_id})>"
    
    @property
    def namespaced_storages(self) -> dict:
        """
        Get LightRAG storage configuration with namespace isolation.
        
        Returns namespace-prefixed storage names for LightRAG initialization.
        """
        prefix = self.lightrag_namespace_prefix
        return {
            "chunks_vdb": f"{prefix}_chunks",
            "entities_vdb": f"{prefix}_entities",
            "relationships_vdb": f"{prefix}_relationships",
            "text_chunks": f"{prefix}_text_chunks",
            "doc_status": f"{prefix}_doc_status",
            "graph": f"{prefix}_graph",
        }
