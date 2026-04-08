"""
Query routes for searching and retrieving information from knowledge bases.
"""
import time
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from server.models.database import get_db_session
from server.models.user import User
from server.schemas import QueryRequest, QueryResponse, QuerySource
from server.middleware.auth import get_current_user
from server.services.kb_service import get_knowledge_base
from server.services.rag_service import get_rag_manager

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/knowledge-bases", tags=["Query"])


@router.post("/{kb_id}/query", response_model=QueryResponse)
async def query_knowledge_base(
    kb_id: UUID,
    query_data: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Query a specific knowledge base.
    
    Uses RAG (Retrieval-Augmented Generation) to search the KB and generate answers.
    """
    start_time = time.time()
    
    # Verify user has access to this KB
    kb = await get_knowledge_base(db, kb_id, current_user)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or you don't have access"
        )
    
    try:
        # Get RAG manager
        rag_manager = get_rag_manager()
        
        logger.info(f"Executing query: {query_data.query[:100]}...")
        logger.info(f"Query mode: {query_data.mode.value}, top_k: {query_data.top_k}")
        
        # Get RAG instance for this KB
        # CRITICAL: get_rag_instance already uses kb_id for namespace (see rag_service.py line 63)
        # Upload uses "kb_{kb_id}", query also uses "kb_{kb_id}" - CONSISTENT!
        
        logger.info(f"=== QUERY DEBUG INFO ===")
        logger.info(f"KB ID: {kb_id}")
        expected_namespace = f"kb_{kb_id}"
        logger.info(f"Expected namespace: {expected_namespace}")
        
        async with rag_manager.get_rag_instance(kb) as rag:
            logger.info(f"RAG working_dir: {rag.working_dir}")
            if hasattr(rag, 'lightrag') and rag.lightrag:
                logger.info(f"LightRAG workspace: {rag.lightrag.workspace}")
            else:
                logger.error("LightRAG not initialized!")
            logger.debug("RAG instance obtained")
            
            # Log LightRAG initialization status
            if hasattr(rag, 'lightrag') and rag.lightrag:
                # LightRAG object doesn't have workspace_dir, check config instead
                logger.debug(f"LightRAG initialized: {rag.lightrag is not None}")
            else:
                logger.error("LightRAG not initialized!")
            
            # Execute query
            logger.debug("Calling rag.aquery()...")
            result = await rag.aquery(
                query=query_data.query,
                mode=query_data.mode.value,
                top_k=query_data.top_k,
                vlm_enhanced=query_data.vlm_enhanced,  # Pass VLM enhanced flag
                # Note: max_tokens and temperature are not supported by LightRAG's QueryParam
                # temperature=query_data.temperature,  # Removed
            )
            logger.debug(f"Query completed. Result type: {type(result)}")
            logger.debug(f"Query result value: {repr(result)[:200] if result else 'None'}")
        
        # Format response
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Query processed in {processing_time:.2f}ms")
        
        # Extract answer from result
        # RAGAnything's aquery returns str or AsyncIterator, not dict
        if isinstance(result, dict):
            # If it's a dict (shouldn't happen, but handle it)
            answer = result.get("answer", "") or result.get("llm_response", {}).get("content", "")
        elif isinstance(result, str):
            # Normal case: aquery returns string directly
            # Check if result is "None" string (indicates empty response)
            if result == "None":
                logger.warning("LLM returned 'None' string - this indicates empty response")
                answer = ""
            else:
                answer = result
        else:
            # Fallback for other types
            answer = str(result)
        
        logger.info(f"Extracted answer: {repr(answer[:100] if answer else 'EMPTY')}")
        
        return QueryResponse(
            answer=answer,
            sources=[],  # Will be populated when LightRAG returns chunk metadata
            query_mode=query_data.mode.value,
            processing_time_ms=processing_time,
            kb_ids=[kb_id]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/query", response_model=QueryResponse)
async def query_all_knowledge_bases(
    query_data: QueryRequest,
    kb_ids: Optional[List[UUID]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Query across multiple or all accessible knowledge bases.
    
    If kb_ids is not provided, queries all KBs accessible by the current user.
    """
    start_time = time.time()
    
    # Get list of KBs to query
    if kb_ids:
        # Query specific KBs
        kbs = []
        for kb_id in kb_ids:
            kb = await get_knowledge_base(db, kb_id, current_user)
            if kb:
                kbs.append(kb)
        
        if not kbs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accessible knowledge bases found"
            )
    else:
        # Query all user's KBs
        from server.services.kb_service import get_user_knowledge_bases
        kbs = await get_user_knowledge_bases(db, current_user, limit=100)
        
        if not kbs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You don't have any knowledge bases"
            )
    
    # Query each KB and aggregate results
    all_answers = []
    all_sources = []
    
    rag_manager = get_rag_manager()
    
    for kb in kbs:
        try:
            async with rag_manager.get_rag_instance(kb) as rag:
                result = await rag.aquery(
                    query=query_data.query,
                    mode=query_data.mode.value,
                    top_k=query_data.top_k,
                )
                
                if isinstance(result, dict):
                    all_answers.append(result.get("answer", ""))
                    # Extract sources if available
                    if "sources" in result:
                        for source in result["sources"]:
                            all_sources.append(QuerySource(
                                content=source.get("content", ""),
                                score=source.get("score", 0.0),
                                metadata=source.get("metadata", {}),
                                kb_id=kb.id
                            ))
                else:
                    all_answers.append(str(result))
                    
        except Exception as e:
            # Log error but continue with other KBs
            print(f"Error querying KB {kb.id}: {e}")
            continue
    
    # Aggregate answers
    if not all_answers:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query any knowledge base"
        )
    
    # Combine answers (simple concatenation for now)
    # TODO: Use LLM to synthesize better combined answer
    combined_answer = "\n\n---\n\n".join(all_answers)
    
    processing_time = (time.time() - start_time) * 1000
    
    return QueryResponse(
        answer=combined_answer,
        sources=all_sources[:query_data.top_k],  # Limit sources
        query_mode=query_data.mode.value,
        processing_time_ms=processing_time,
        kb_ids=[kb.id for kb in kbs]
    )
