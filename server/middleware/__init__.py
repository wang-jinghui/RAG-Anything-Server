"""
Authentication and tenant resolution middleware.
"""
from server.middleware.auth import (
    get_current_user,
    require_super_admin,
    get_optional_user
)

from server.middleware.tenant_resolver import (
    resolve_knowledge_base_access,
    get_user_access_level,
    get_user_kb_list
)

__all__ = [
    "get_current_user",
    "require_super_admin",
    "get_optional_user",
    "resolve_knowledge_base_access",
    "get_user_access_level",
    "get_user_kb_list"
]
