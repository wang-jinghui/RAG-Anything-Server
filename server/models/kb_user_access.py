"""
Knowledge Base User Access model for collaboration.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from server.models.database import Base


class KBUserAccess(Base):
    """
    Knowledge Base User Access model for managing collaboration.
    
    Allows knowledge base owners to grant access to other users
    with different permission levels (owner, editor, viewer).
    """
    __tablename__ = "kb_user_access"
    
    kb_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    access_level = Column(String(50), nullable=False)  # owner, editor, viewer
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="user_access")
    user = relationship("User", back_populates="kb_access")
    granter = relationship("User", foreign_keys=[granted_by])
    
    __table_args__ = (
        PrimaryKeyConstraint("kb_id", "user_id"),
    )
    
    def __repr__(self) -> str:
        return f"<KBUserAccess(kb_id={self.kb_id}, user_id={self.user_id}, access_level={self.access_level})>"
