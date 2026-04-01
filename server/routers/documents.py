"""
Document management routes for uploading and managing documents in knowledge bases.
"""
import os
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from server.models.database import get_db_session
from server.models.user import User
from server.models.knowledge_base import KnowledgeBase
from server.models.kb_document import KBDocument
from server.schemas import DocumentUploadResponse, DocumentListResponse, UploadStatus
from server.middleware.auth import get_current_user
from server.middleware.tenant_resolver import resolve_knowledge_base_access
from server.services.kb_service import get_knowledge_base


async def _process_document_background(
    doc_id: UUID,
    kb_id: UUID,
    file_path: str,
    db: AsyncSession
):
    """
    Process document in background: parse and add to LightRAG.
    
    This function runs asynchronously and doesn't block the upload response.
    It updates the document status to 'completed' or 'failed' when done.
    """
    from server.models.kb_document import KBDocument
    from server.services.rag_service import process_document_with_raganything
    from datetime import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    
    print(f"\n[DBUG] === BACKGROUND TASK START ===")
    print(f"[DBUG] Doc ID: {doc_id}")
    print(f"[DBUG] KB ID: {kb_id}")
    print(f"[DBUG] File: {file_path}")
    
    try:
        logger.info(f"Starting background processing for document {doc_id}")
        print(f"[DBUG] Calling process_document_with_raganything...")
        
        # Process document using RAGAnything
        result = await process_document_with_raganything(
            file_path=file_path,
            kb_id=kb_id,
            doc_id=doc_id,
            db=db,  # Pass db parameter
        )
        
        logger.info(f"Processing result: {result}")
        print(f"[DBUG] Result: {result}")
        print(f"[DBUG] === BACKGROUND TASK END ===\n")
        
        if result['success']:
            # Update document status to completed
            doc = await db.get(KBDocument, doc_id)
            if doc:
                doc.upload_status = "completed"
                doc.lightrag_doc_id = result['doc_id']
                doc.processed_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Document {doc_id} marked as completed")
        else:
            # Handle processing error
            logger.error(f"Processing failed for {doc_id}: {result.get('error')}")
            doc = await db.get(KBDocument, doc_id)
            if doc:
                doc.upload_status = "failed"
                doc.error_message = result.get('error', 'Unknown error')
                await db.commit()
                logger.info(f"Document {doc_id} marked as failed")
                
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error processing {doc_id}: {e}", exc_info=True)
        doc = await db.get(KBDocument, doc_id)
        if doc:
            doc.upload_status = "failed"
            doc.error_message = str(e)
            await db.commit()


router = APIRouter(prefix="/knowledge-bases", tags=["Documents"])


@router.post("/{kb_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    kb_id: UUID,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = Depends,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Upload a document to a knowledge base.
    
    Supported formats: PDF, DOCX, TXT, MD, PPTX, XLSX
    
    The document will be processed and added to the knowledge base's vector storage.
    """
    # Verify user has access to this KB
    kb = await get_knowledge_base(db, kb_id, current_user)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or you don't have access"
        )
    
    # Check access level (at least editor)
    # For now, allow owners and editors (viewers can't upload)
    # This would need proper access level checking from kb_user_access table
    
    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".txt", ".md", ".pptx", ".xlsx"}
    
    # Handle both string and tuple filenames (httpx returns tuple)
    if isinstance(file.filename, tuple):
        filename = file.filename[0] if len(file.filename) > 0 else "unknown"
    elif isinstance(file.filename, str):
        filename = file.filename
    else:
        filename = str(file.filename)
    
    # Get file extension - splitext returns (root, ext) tuple
    _, file_ext = os.path.splitext(filename)
    file_ext = file_ext.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Create unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Save file temporarily
    temp_dir = f"./temp_uploads/{kb_id}"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, unique_filename)
    
    try:
        # Save uploaded file
        logger.warning(f"\n=== UPLOAD START ===")
        logger.warning(f"Filename: {filename}")
        logger.warning(f"KB ID: {kb_id}")
        logger.warning(f"Temp path: {temp_file_path}")
        
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.warning(f"File saved, size: {len(content)} bytes")
        
        # Create document record
        doc = KBDocument(
            knowledge_base_id=kb_id,
            file_name=filename,  # Use the processed filename
            file_path=temp_file_path,
            lightrag_doc_id=str(uuid.uuid4()),  # Will be updated after processing
            file_size=len(content),
            mime_type=file.content_type or "application/octet-stream",
            upload_status="pending",  # Keep as pending during processing
            uploaded_by=current_user.id
        )
        
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        # Process document SYNCHRONOUSLY (not in background)
        # This ensures the document is actually processed before returning
        logger.info(f"\n[SYNC] Starting synchronous processing...")
        logger.info(f"[SYNC] Doc ID: {doc.id}")
        logger.info(f"[SYNC] File: {temp_file_path}")
        
        try:
            from server.services.rag_service import process_document_with_raganything
            result = await process_document_with_raganything(
                doc_id=doc.id,
                kb_id=kb_id,
                file_path=temp_file_path,
                db=db
            )
            
            logger.info(f"[SYNC] Processing result: {result}")
            
            if result['success']:
                doc.upload_status = "completed"
                doc.lightrag_doc_id = result['doc_id']
                doc.processed_at = datetime.utcnow()
                logger.info(f"[SYNC] ✅ Document processed successfully")
            else:
                doc.upload_status = "failed"
                doc.error_message = result.get('error', 'Unknown error')
                logger.info(f"[SYNC] ❌ Processing failed: {result.get('error')}")
        except Exception as e:
            logger.error(f"[SYNC] ❌ Exception during processing: {e}", exc_info=True)
            doc.upload_status = "failed"
            doc.error_message = str(e)
        
        await db.commit()
        
        return DocumentUploadResponse(
            id=doc.id,
            kb_id=doc.knowledge_base_id,
            file_name=doc.file_name,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            upload_status=UploadStatus(doc.upload_status),
            uploaded_at=doc.uploaded_at,
            processed_at=doc.processed_at,
            error_message=doc.error_message
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/{kb_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    kb_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List all documents in a knowledge base.
    """
    # Verify user has access to this KB
    kb = await get_knowledge_base(db, kb_id, current_user)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or you don't have access"
        )
    
    # Build query
    from sqlalchemy import select
    
    query = select(KBDocument).where(KBDocument.knowledge_base_id == kb_id)
    
    if status_filter:
        query = query.where(KBDocument.upload_status == status_filter)
    
    # Get total count
    count_query = select(KBDocument).where(KBDocument.knowledge_base_id == kb_id)
    if status_filter:
        count_query = count_query.where(KBDocument.upload_status == status_filter)
    
    result = await db.execute(count_query)
    total = len(result.scalars().all())
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(KBDocument.uploaded_at.desc())
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return DocumentListResponse(
        documents=[
            DocumentUploadResponse(
                id=doc.id,
                kb_id=doc.knowledge_base_id,
                file_name=doc.file_name,
                file_size=doc.file_size,
                mime_type=doc.mime_type,
                upload_status=UploadStatus(doc.upload_status),
                uploaded_at=doc.uploaded_at,
                processed_at=doc.processed_at,
                error_message=doc.error_message
            )
            for doc in documents
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{kb_id}/documents/{doc_id}", response_model=DocumentUploadResponse)
async def get_document(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get details of a specific document.
    """
    # Verify user has access to this KB
    kb = await get_knowledge_base(db, kb_id, current_user)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or you don't have access"
        )
    
    # Get document
    from sqlalchemy import select
    
    result = await db.execute(
        select(KBDocument).where(
            KBDocument.id == doc_id,
            KBDocument.knowledge_base_id == kb_id
        )
    )
    
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentUploadResponse(
        id=doc.id,
        kb_id=doc.knowledge_base_id,
        file_name=doc.file_name,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        upload_status=UploadStatus(doc.upload_status),
        uploaded_at=doc.uploaded_at,
        processed_at=doc.processed_at,
        error_message=doc.error_message
    )


@router.delete("/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    kb_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a document from the knowledge base.
    
    This will also remove the document's vectors from the storage.
    """
    # Verify user has access to this KB
    kb = await get_knowledge_base(db, kb_id, current_user)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or you don't have access"
        )
    
    # Check if user is owner (only owners can delete)
    if kb.owner_id != current_user.id and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can delete documents"
        )
    
    # Get document
    from sqlalchemy import select
    
    result = await db.execute(
        select(KBDocument).where(
            KBDocument.id == doc_id,
            KBDocument.knowledge_base_id == kb_id
        )
    )
    
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Delete temporary file if exists
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        
        # Delete document record
        await db.delete(doc)
        await db.commit()
        
        # TODO: Remove from LightRAG storage
        # - Call raganything to delete vectors associated with lightrag_doc_id
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
