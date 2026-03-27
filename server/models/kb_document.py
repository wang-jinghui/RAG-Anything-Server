"""
Knowledge Base Document tracking model.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from server.models.database import Base


class KBDocument(Base):
    """
    Document tracking model for knowledge base.
    
    Tracks documents uploaded to knowledge bases and their processing status.
    Links to LightRAG's internal document storage via lightrag_doc_id.
    """
    __tablename__ = "kb_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)  # Original file path or S3 key
    lightrag_doc_id = Column(String(255), nullable=False, index=True)  # Doc ID in LightRAG storage
    file_size = Column(Integer, nullable=True)  # File size in bytes
    mime_type = Column(String(100), nullable=True)
    upload_status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    
    def __repr__(self) -> str:
        return f"<KBDocument(id={self.id}, kb_id={self.knowledge_base_id}, file_name={self.file_name})>"
