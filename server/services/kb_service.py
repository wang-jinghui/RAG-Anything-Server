"""
Knowledge Base service for business logic.
"""
import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from server.models.knowledge_base import KnowledgeBase
from server.models.user import User
from server.models.kb_user_access import KBUserAccess
from server.schemas import KnowledgeBaseCreate, KnowledgeBaseUpdate, AccessLevel


async def create_knowledge_base(
    db: AsyncSession,
    owner: User,
    kb_data: KnowledgeBaseCreate
) -> KnowledgeBase:
    """
    Create a new knowledge base.
    
    Args:
        db: Database session
        owner: Owner user object
        kb_data: Knowledge base creation data
        
    Returns:
        Created KnowledgeBase object
    """
    # Generate unique namespace prefix
    namespace_prefix = f"kb_{owner.id}_{uuid.uuid4().hex[:8]}"
    
    kb = KnowledgeBase(
        name=kb_data.name,
        description=kb_data.description,
        owner_id=owner.id,
        lightrag_namespace_prefix=namespace_prefix,
        vector_storage_config=kb_data.vector_storage_config,
        graph_storage_config=kb_data.graph_storage_config
    )
    
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    
    return kb


async def get_knowledge_base(
    db: AsyncSession,
    kb_id: uuid.UUID,
    user: User
) -> Optional[KnowledgeBase]:
    """
    Get knowledge base by ID with access check.
    
    Args:
        db: Database session
        kb_id: Knowledge base ID
        user: Requesting user
        
    Returns:
        KnowledgeBase if found and accessible, None otherwise
    """
    # Super admins can access any KB
    if user.is_super_admin:
        result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        return result.scalar_one_or_none()
    
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
    
    # Check granted access
    result = await db.execute(
        select(KBUserAccess).where(
            KBUserAccess.kb_id == kb_id,
            KBUserAccess.user_id == user.id
        )
    )
    access = result.scalar_one_or_none()
    
    if access:
        result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        return result.scalar_one_or_none()
    
    return None


async def get_user_knowledge_bases(
    db: AsyncSession,
    user: User,
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None
) -> List[KnowledgeBase]:
    """
    Get all knowledge bases accessible by user.
    
    Args:
        db: Database session
        user: Authenticated user
        skip: Pagination offset
        limit: Maximum results
        status_filter: Optional status filter
        
    Returns:
        List of accessible KnowledgeBase objects
    """
    if user.is_super_admin:
        # Super admins can see all KBs
        query = select(KnowledgeBase)
        if status_filter:
            query = query.where(KnowledgeBase.status == status_filter)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    # Get owned KBs
    owned_query = select(KnowledgeBase).where(
        KnowledgeBase.owner_id == user.id
    )
    if status_filter:
        owned_query = owned_query.where(KnowledgeBase.status == status_filter)
    
    result = await db.execute(owned_query)
    owned_kbs = result.scalars().all()
    
    # Get KBs with granted access
    result = await db.execute(
        select(KBUserAccess).where(KBUserAccess.user_id == user.id)
    )
    accesses = result.scalars().all()
    
    kb_ids_with_access = [access.kb_id for access in accesses]
    
    if kb_ids_with_access:
        shared_query = select(KnowledgeBase).where(
            KnowledgeBase.id.in_(kb_ids_with_access)
        )
        if status_filter:
            shared_query = shared_query.where(KnowledgeBase.status == status_filter)
        
        result = await db.execute(shared_query)
        shared_kbs = result.scalars().all()
    else:
        shared_kbs = []
    
    # Combine and paginate
    all_kbs = owned_kbs + shared_kbs
    return all_kbs[skip:skip+limit]


async def update_knowledge_base(
    db: AsyncSession,
    kb: KnowledgeBase,
    update_data: KnowledgeBaseUpdate
) -> KnowledgeBase:
    """
    Update knowledge base.
    
    Args:
        db: Database session
        kb: KnowledgeBase to update
        update_data: Update data
        
    Returns:
        Updated KnowledgeBase
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        setattr(kb, field, value)
    
    await db.commit()
    await db.refresh(kb)
    return kb


async def delete_knowledge_base(
    db: AsyncSession,
    kb: KnowledgeBase
) -> bool:
    """
    Delete knowledge base.
    
    Args:
        db: Database session
        kb: KnowledgeBase to delete
        
    Returns:
        True if deleted successfully
    """
    await db.delete(kb)
    await db.commit()
    return True


async def grant_kb_access(
    db: AsyncSession,
    kb: KnowledgeBase,
    user_email: str,
    access_level: AccessLevel,
    granted_by: User
) -> KBUserAccess:
    """
    Grant user access to a knowledge base.
    
    Args:
        db: Database session
        kb: KnowledgeBase to grant access to
        user_email: Email of user to grant access to
        access_level: Access level (owner/editor/viewer)
        granted_by: User granting access
        
    Returns:
        Created KBUserAccess object
        
    Raises:
        ValueError: If user not found or already has access
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == user_email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError("User not found")
    
    # Don't allow granting access to yourself
    if user.id == granted_by.id:
        raise ValueError("Cannot grant access to yourself")
    
    # Check if access already exists
    result = await db.execute(
        select(KBUserAccess).where(
            KBUserAccess.kb_id == kb.id,
            KBUserAccess.user_id == user.id
        )
    )
    existing_access = result.scalar_one_or_none()
    
    if existing_access:
        # Update existing access
        existing_access.access_level = access_level
        existing_access.granted_by = granted_by.id
        await db.commit()
        await db.refresh(existing_access)
        return existing_access
    
    # Create new access record
    access = KBUserAccess(
        kb_id=kb.id,
        user_id=user.id,
        access_level=access_level.value,
        granted_by=granted_by.id
    )
    
    db.add(access)
    await db.commit()
    await db.refresh(access)
    
    return access


async def revoke_kb_access(
    db: AsyncSession,
    kb: KnowledgeBase,
    user_id: uuid.UUID
) -> bool:
    """
    Revoke user access from a knowledge base.
    
    Args:
        db: Database session
        kb: KnowledgeBase to revoke access from
        user_id: User ID to revoke access from
        
    Returns:
        True if revoked successfully, False if no access existed
    """
    result = await db.execute(
        delete(KBUserAccess).where(
            KBUserAccess.kb_id == kb.id,
            KBUserAccess.user_id == user_id
        )
    )
    
    await db.commit()
    return result.rowcount > 0


async def get_kb_users(
    db: AsyncSession,
    kb: KnowledgeBase
) -> List[dict]:
    """
    Get all users with access to a knowledge base.
    
    Args:
        db: Database session
        kb: KnowledgeBase
        
    Returns:
        List of user info dicts with access details
    """
    # Get all access records
    result = await db.execute(
        select(KBUserAccess)
        .options(selectinload(KBUserAccess.user))
        .where(KBUserAccess.kb_id == kb.id)
    )
    accesses = result.scalars().all()
    
    # Format response
    users = []
    for access in accesses:
        users.append({
            "user_id": access.user.id,
            "email": access.user.email,
            "username": access.user.username,
            "access_level": access.access_level,
            "granted_at": access.granted_at,
            "granted_by": access.granted_by
        })
    
    # Also include owner
    owner_result = await db.execute(
        select(User).where(User.id == kb.owner_id)
    )
    owner = owner_result.scalar_one()
    
    users.append({
        "user_id": owner.id,
        "email": owner.email,
        "username": owner.username,
        "access_level": "owner",
        "granted_at": kb.created_at,
        "granted_by": None
    })
    
    return users
