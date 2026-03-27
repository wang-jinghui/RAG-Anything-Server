"""
SQLAlchemy models.
"""
from server.models.database import Base

# Import all models to register them with Base.metadata
from server.models.user import User
from server.models.knowledge_base import KnowledgeBase
from server.models.api_key import APIKey
from server.models.kb_document import KBDocument
from server.models.kb_user_access import KBUserAccess

__all__ = ["Base", "User", "KnowledgeBase", "APIKey", "KBDocument", "KBUserAccess"]
