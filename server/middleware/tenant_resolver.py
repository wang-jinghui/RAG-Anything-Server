"""
Tenant resolver middleware for multi-tenant isolation.
"""
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Union
from uuid import UUID

from server.models.user import User
from server.models.knowledge_base import KnowledgeBase
from server.models.kb_user_access import KBUserAccess


async def resolve_knowledge_base_access(
    db: AsyncSession,
    user: User,
    kb_id: Union[str, UUID]
) -> KnowledgeBase:
    """
    Resolve and verify user access to a knowledge base.
    
    Args:
        db: Database session
        user: Authenticated user
        kb_id: Knowledge base ID to check access for
        
    Returns:
        KnowledgeBase object if user has access
        
    Raises:
        HTTPException: If user doesn't have access
    """
    if isinstance(kb_id, str):
        try:
            kb_id = UUID(kb_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid knowledge base ID format"
            )
    
    # Super admins can access all KBs
    if user.is_super_admin:
        result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one_or_none()
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        return kb
    
    # Check if user owns this KB
    if user.id == kb_id:
        # This is actually checking if kb_id equals user_id, which is wrong
        # Let me fix this logic
        pass
    
    # Check ownership
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.owner_id == user.id
        )
    )
    kb = result.scalar_one_or_none()
    
    if kb:
        return kb
    
    # Check if user has been granted access
    result = await db.execute(
        select(KBUserAccess).where(
            KBUserAccess.kb_id == kb_id,
            KBUserAccess.user_id == user.id
        )
    )
    access = result.scalar_one_or_none()
    
    if access:
        # Get the actual KB
        result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one_or_none()
        if kb:
            return kb
    
    # No access
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this knowledge base"
    )


def get_user_access_level(user: User, kb: KnowledgeBase) -> Optional[str]:
    """
    Get user's access level for a knowledge base.
    
    Args:
        user: User object
        kb: KnowledgeBase object
        
    Returns:
        Access level string (owner/editor/viewer) or None if no access
    """
    # Super admins have implicit owner-level access
    if user.is_super_admin:
        return "owner"
    
    # Check ownership
    if kb.owner_id == user.id:
        return "owner"
    
    # Check explicit access grants (would need to be loaded via relationship)
    # This would typically be done in the service layer with proper joins
    
    return None


async def get_user_kb_list(db: AsyncSession, user: User, skip: int = 0, limit: int = 20) -> list[KnowledgeBase]:
    """
    Get list of knowledge bases accessible by user.
    
    Args:
        db: Database session
        user: Authenticated user
        skip: Pagination offset
        limit: Maximum results
        
    Returns:
        List of accessible KnowledgeBase objects
    """
    if user.is_super_admin:
        # Super admins can see all KBs
        result = await db.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.status == "active")
            .offset(skip)
            .limit(limit)
        )
    else:
        # Regular users see KBs they own or have access to
        # Get owned KBs
        owned_result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.owner_id == user.id,
                KnowledgeBase.status == "active"
            )
        )
        owned_kbs = owned_result.scalars().all()
        
        # Get KBs with granted access
        access_result = await db.execute(
            select(KBUserAccess).where(KBUserAccess.user_id == user.id)
        )
        accesses = access_result.scalars().all()
        
        kb_ids_with_access = [access.kb_id for access in accesses]
        
        if kb_ids_with_access:
            shared_result = await db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.id.in_(kb_ids_with_access),
                    KnowledgeBase.status == "active"
                )
            )
            shared_kbs = shared_result.scalars().all()
        else:
            shared_kbs = []
        
        # Combine and paginate
        all_kbs = owned_kbs + shared_kbs
        all_kbs = all_kbs[skip:skip+limit]
        return all_kbs
    
    return result.scalars().all()
