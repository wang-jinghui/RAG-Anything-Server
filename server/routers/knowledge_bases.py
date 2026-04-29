"""
Knowledge Base management routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID

from server.models.database import get_db_session
from server.models.user import User
from server.models.knowledge_base import KnowledgeBase
from server.models.kb_document import KBDocument
from server.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    GrantAccessRequest,
    RevokeAccessRequest,
    KBUserResponse,
    AccessLevel
)
from server.middleware.auth import get_current_user
from server.services.kb_service import (
    create_knowledge_base,
    get_knowledge_base,
    get_user_knowledge_bases,
    update_knowledge_base,
    delete_knowledge_base,
    grant_kb_access,
    revoke_kb_access,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])


@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List all knowledge bases accessible by the current user.
    
    - **skip**: Number of results to skip for pagination
    - **limit**: Maximum number of results to return
    - **status**: Filter by status (active, archived, deleted)
    """
    kbs = await get_user_knowledge_bases(
        db, current_user, skip=skip, limit=limit, status_filter=status_filter
    )
    
    # Batch update document counts for all KBs in the list
    if kbs:
        kb_ids = [kb.id for kb in kbs]
        
        # Single query to get document counts for all KBs
        stmt = (
            select(KBDocument.knowledge_base_id, func.count())
            .where(
                KBDocument.knowledge_base_id.in_(kb_ids),
                KBDocument.upload_status == 'completed'
            )
            .group_by(KBDocument.knowledge_base_id)
        )
        result = await db.execute(stmt)
        doc_counts = dict(result.all())
        
        # Update each KB's document_count if different
        for kb in kbs:
            actual_count = doc_counts.get(kb.id, 0)
            if kb.document_count != actual_count:
                logger.info(f"Fixing document count for KB {kb.id}: {kb.document_count} -> {actual_count}")
                kb.document_count = actual_count
        
        await db.commit()
    
    return kbs


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base_endpoint(
    kb_data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new knowledge base.
    
    The creating user becomes the owner with full access.
    """
    kb = await create_knowledge_base(db, current_user, kb_data)
    return kb


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base_endpoint(
    kb_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get details of a specific knowledge base.
    """
    kb = await get_knowledge_base(db, kb_id, current_user)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or you don't have access"
        )
    
    # Real-time calculation of document count to ensure accuracy
    stmt = select(func.count()).select_from(KBDocument).where(
        KBDocument.knowledge_base_id == kb_id,
        KBDocument.upload_status == 'completed'
    )
    result = await db.execute(stmt)
    actual_doc_count = result.scalar() or 0
    
    # Update the document_count field to keep it in sync
    if kb.document_count != actual_doc_count:
        logger.info(f"Fixing document count for KB {kb_id}: {kb.document_count} -> {actual_doc_count}")
        kb.document_count = actual_doc_count
        await db.commit()
    
    return kb


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base_endpoint(
    kb_id: UUID,
    update_data: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update a knowledge base.
    
    Only owners can update knowledge base settings.
    """
    kb = await get_knowledge_base(db, kb_id, current_user)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or you don't have access"
        )
    
    # Check if user is owner (or super admin)
    if kb.owner_id != current_user.id and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can update knowledge bases"
        )
    
    kb = await update_knowledge_base(db, kb, update_data)
    return kb


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base_endpoint(
    kb_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a knowledge base.
    
    Only owners can delete knowledge bases. This action cannot be undone.
    """
    kb = await get_knowledge_base(db, kb_id, current_user)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or you don't have access"
        )
    
    # Check if user is owner (or super admin)
    if kb.owner_id != current_user.id and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can delete knowledge bases"
        )
    
    await delete_knowledge_base(db, kb)
    
    return {"message": "Knowledge base deleted successfully", "kb_id": str(kb_id)}


@router.post("/{kb_id}/access", status_code=status.HTTP_201_CREATED)
async def grant_access_endpoint(
    kb_id: UUID,
    access_request: GrantAccessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Grant access to a user for this knowledge base.
    
    - **user_email**: Email of the user to grant access to
    - **access_level**: Permission level (owner, editor, viewer)
    
    Only owners can grant access to others.
    """
    kb = await get_knowledge_base(db, kb_id, current_user)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    # Check if user is owner (or super admin)
    if kb.owner_id != current_user.id and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can grant access"
        )
    
    try:
        access = await grant_kb_access(
            db, kb, access_request.user_email, access_request.access_level, current_user
        )
        return {
            "message": "Access granted successfully",
            "user_email": access_request.user_email,
            "access_level": access.access_level
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{kb_id}/access", status_code=status.HTTP_200_OK)
async def revoke_access_endpoint(
    kb_id: UUID,
    request: RevokeAccessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Revoke access from a user for this knowledge base.
    
    Only owners can revoke access.
    Accepts user_email instead of user_id for better UX.
    """
    kb = await get_knowledge_base(db, kb_id, current_user)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    # Check if user is owner (or super admin)
    if kb.owner_id != current_user.id and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can revoke access"
        )
    
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.user_email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {request.user_email} not found"
        )
    
    # Don't allow revoking owner's access
    if user.id == kb.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke owner's access"
        )
    
    success = await revoke_kb_access(db, kb, user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have access to this knowledge base"
        )
    
    return {"message": "Access revoked successfully"}


@router.get("/{kb_id}/users", response_model=List[KBUserResponse])
async def get_kb_users_endpoint(
    kb_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all users with access to this knowledge base.
    """
    kb = await get_knowledge_base(db, kb_id, current_user)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    users = await get_kb_users(db, kb)
    return users
