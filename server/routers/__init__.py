"""
API routers.
"""
from server.routers.auth import router as auth_router
from server.routers.knowledge_bases import router as kb_router

__all__ = ["auth_router", "kb_router"]
