"""
User model for authentication and authorization.
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from server.models.database import Base


class User(Base):
    """
    User model for authentication and tenant isolation.
    
    In our user-as-tenant model, each user is their own tenant,
    but can share access to knowledge bases with other users.
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_super_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    owned_knowledge_bases = relationship(
        "KnowledgeBase",
        back_populates="owner",
        foreign_keys="KnowledgeBase.owner_id",
        cascade="all, delete-orphan"
    )
    
    kb_access = relationship(
        "KBUserAccess",
        back_populates="user",
        foreign_keys="KBUserAccess.user_id",
        cascade="all, delete-orphan"
    )
    
    api_keys = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
    
    def is_owner(self, kb_id: uuid.UUID) -> bool:
        """Check if user is owner of a knowledge base."""
        return any(kb.id == kb_id for kb in self.owned_knowledge_bases)
