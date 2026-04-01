"""
RAG Anything service manager for document processing and querying.

This module provides a service layer to manage RAGAnything instances
with proper configuration and tenant isolation.
"""
import asyncio
from typing import Dict, Optional, Any
from uuid import UUID
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from server.rag_config import RAGConfig, LLMConfig, EmbeddingConfig
from server.models.knowledge_base import KnowledgeBase


class RAGInstanceManager:
    """
    Manages a pool of RAGAnything instances with namespace isolation.
    
    Each knowledge base gets its own isolated RAG instance with
    namespaced storage to prevent data leakage between tenants.
    """
    
    def __init__(self):
        self._instances: Dict[str, Any] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._config: Optional[RAGConfig] = None
    
    def initialize(self, config: Optional[RAGConfig] = None):
        """
        Initialize the instance manager with global RAG config.
        
        Args:
            config: Global RAG configuration. If None, loads from env.
        """
        self._config = config or RAGConfig.from_env()
    
    @asynccontextmanager
    async def get_rag_instance(
        self,
        kb: KnowledgeBase,
        llm_model_func: Optional[Any] = None,
        embedding_func: Optional[Any] = None
    ):
        """
        Get or create a RAGAnything instance for a specific knowledge base.
        
        Usage:
            async with manager.get_rag_instance(kb) as rag:
                result = await rag.aquery("your query")
        
        Args:
            kb: KnowledgeBase object with namespace info
            llm_model_func: Optional custom LLM function
            embedding_func: Optional custom embedding function
        
        Yields:
            Configured RAGAnything instance
        """
        kb_id_str = str(kb.id)
        namespace = kb.lightrag_namespace_prefix
        
        # Create lock for this KB if not exists
        if kb_id_str not in self._locks:
            self._locks[kb_id_str] = asyncio.Lock()
        
        async with self._locks[kb_id_str]:
            # Check if instance exists
            if kb_id_str not in self._instances:
                # Create new instance with namespace
                rag = await self._create_rag_instance(
                    namespace=namespace,
                    llm_model_func=llm_model_func,
                    embedding_func=embedding_func
                )
                self._instances[kb_id_str] = rag
            
            try:
                yield self._instances[kb_id_str]
            except Exception as e:
                # Remove instance on error to force recreation
                if kb_id_str in self._instances:
                    del self._instances[kb_id_str]
                raise e
    
    async def _create_rag_instance(
        self,
        namespace: str,
        llm_model_func: Optional[Any] = None,
        embedding_func: Optional[Any] = None
    ) -> Any:
        """
        Create a new RAGAnything instance with namespace isolation.
        
        Args:
            namespace: LightRAG namespace prefix
            llm_model_func: Optional custom LLM function
            embedding_func: Optional custom embedding function
        
        Returns:
            Initialized RAGAnything instance
        """
        try:
            from raganything import RAGAnything
        except ImportError:
            raise ImportError(
                "raganything package not found. Please install it with: "
                "pip install raganything"
            )
        
        # Use global config or default
        config = self._config or RAGConfig.from_env()
        
        # Modify working_dir to include namespace for isolation
        namespaced_working_dir = f"{config.working_dir}/{namespace}"
        
        # Create config with namespace
        rag_config = RAGConfig(
            llm=config.llm,
            embedding=config.embedding,
            vector_storage=config.vector_storage,
            graph_storage=config.graph_storage,
            working_dir=namespaced_working_dir,
            chunk_token_size=config.chunk_token_size,
        )
        
        # Create RAGAnything config with namespace
        from raganything.config import RAGAnythingConfig as RAGAnythingConfigObj
        raganything_config = RAGAnythingConfigObj(
            working_dir=namespaced_working_dir,
            parser='mineru',
            parse_method='auto',
        )
        
        # Create RAGAnything instance - ONLY pass config and function refs
        # Following the official documentation pattern
        rag = RAGAnything(
            config=raganything_config,
            llm_model_func=llm_model_func or self._default_llm_func(config),
            embedding_func=embedding_func or self._default_embedding_func(config),
        )
        
        # Initialize LightRAG
        await rag._ensure_lightrag_initialized()
        
        return rag
    
    def _default_llm_func(self, config: RAGConfig) -> Any:
        """Create default LLM function based on config."""
        if config.llm.provider == "openai":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=config.llm.api_key,
                base_url=config.llm.base_url
            )
            
            async def llm_func(prompts: list[str], **kwargs) -> list[str]:
                responses = []
                for prompt in prompts:
                    response = await client.chat.completions.create(
                        model=config.llm.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=config.llm.max_tokens,
                        temperature=config.llm.temperature,
                    )
                    responses.append(response.choices[0].message.content)
                return responses
            
            return llm_func
        
        elif config.llm.provider == "ollama":
            import ollama
            
            # Log configuration for debugging
            print(f"\n=== OLLAMA LLM CONFIG ===")
            print(f"Provider: {config.llm.provider}")
            print(f"Model: {config.llm.model}")
            print(f"Base URL: {config.llm.base_url}")
            print(f"API Key: {'***' if config.llm.api_key else 'None'}")
            print(f"===========================\n")
            
            # Create Ollama client with custom host
            client = ollama.Client(host=config.llm.base_url)
            
            # Use async chat function
            async def llm_func_async(prompts: list[str], **kwargs) -> list[str]:
                responses = []
                for prompt in prompts:
                    response = client.chat(
                        model=config.llm.model,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    responses.append(response['message']['content'])
                return responses
            
            return llm_func_async
        
        else:
            # Default: assume OpenAI-compatible API
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=config.llm.api_key,
                base_url=config.llm.base_url
            )
            
            async def llm_func(prompts: list[str], **kwargs) -> list[str]:
                responses = []
                for prompt in prompts:
                    response = await client.chat.completions.create(
                        model=config.llm.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=config.llm.max_tokens,
                        temperature=config.llm.temperature,
                    )
                    responses.append(response.choices[0].message.content)
                return responses
            
            return llm_func
    
    def _default_embedding_func(self, config: RAGConfig) -> Any:
        """Create default embedding function based on config."""
        from lightrag.utils import EmbeddingFunc
        
        if config.embedding.provider == "openai":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=config.embedding.api_key,
                base_url=config.embedding.base_url
            )
            
            async def embed_func(texts: list[str]) -> list[list[float]]:
                all_embeddings = []
                for i in range(0, len(texts), config.embedding.batch_size):
                    batch = texts[i:i + config.embedding.batch_size]
                    response = await client.embeddings.create(
                        model=config.embedding.model,
                        input=batch,
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                return all_embeddings
            
            # Return EmbeddingFunc object, not just a function
            return EmbeddingFunc(
                embedding_dim=config.embedding.embedding_dim,
                max_token_size=8192,  # Default value, not in EmbeddingConfig
                func=embed_func,
            )
        
        elif config.embedding.provider == "ollama":
            import ollama
            import numpy as np
            
            # Log configuration for debugging
            print(f"\n=== OLLAMA EMBEDDING CONFIG ===")
            print(f"Provider: {config.embedding.provider}")
            print(f"Model: {config.embedding.model}")
            print(f"Base URL: {config.embedding.base_url}")
            print(f"API Key: {'***' if config.embedding.api_key else 'None'}")
            print(f"==================================\n")
            
            # Create Ollama client with custom host
            client = ollama.Client(host=config.embedding.base_url)
            
            # Use async embedding function
            async def embed_func_async(texts: list[str]) -> list[list[float]]:
                all_embeddings = []
                for text in texts:
                    response = client.embed(
                        model=config.embedding.model,
                        input=text
                    )
                    # Convert to numpy array then back to list for compatibility
                    embedding = np.array(response['embeddings'][0])
                    all_embeddings.append(embedding)
                # Return as numpy array of arrays
                return np.array(all_embeddings)
            
            # Return EmbeddingFunc object with async function
            return EmbeddingFunc(
                embedding_dim=config.embedding.embedding_dim,
                max_token_size=8192,  # Default value
                func=embed_func_async,
            )
        
        else:
            # Default: assume OpenAI-compatible API
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=config.embedding.api_key,
                base_url=config.embedding.base_url
            )
            
            async def embed_func(texts: list[str]) -> list[list[float]]:
                all_embeddings = []
                for i in range(0, len(texts), config.embedding.batch_size):
                    batch = texts[i:i + config.embedding.batch_size]
                    response = await client.embeddings.create(
                        model=config.embedding.model,
                        input=batch,
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                return all_embeddings
            
            # Return EmbeddingFunc object, not just a function (Default OpenAI)
            return EmbeddingFunc(
                embedding_dim=config.embedding.embedding_dim,
                max_token_size=8192,  # Default value
                func=embed_func,
            )
    
    async def close_all(self):
        """Close all RAG instances and cleanup resources."""
        for kb_id, rag in list(self._instances.items()):
            try:
                # If RAGAnything has cleanup method
                if hasattr(rag, 'close'):
                    await rag.close()
            except Exception:
                pass
        
        self._instances.clear()
        self._locks.clear()


# Global instance manager
rag_manager = RAGInstanceManager()


def get_rag_manager() -> RAGInstanceManager:
    """Get the global RAG instance manager."""
    return rag_manager


async def process_document_with_raganything(
    file_path: str,
    kb_id: UUID,
    doc_id: UUID,
    db: AsyncSession,  # Added db parameter
    parser: str = "docling",
    parse_method: str = "auto",
) -> dict:
    """
    Process a document using RAGAnything: parse and add to LightRAG.
    
    This is a convenience function that creates a temporary RAGAnything instance,
    processes the document, and returns the result.
    
    Args:
        file_path: Path to the document file
        kb_id: Knowledge base ID for namespace isolation
        doc_id: Document ID to use in LightRAG
        parser: Parser to use ('mineru', 'docling', 'paddleocr')
        parse_method: Parse method ('auto', 'txt', 'ocr')
    
    Returns:
        dict with keys:
            - success: bool
            - doc_id: str (the LightRAG document ID)
            - content_blocks: int (number of content blocks parsed)
            - error: str (if failed)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"\n=== PROCESS_DOCUMENT_WITH_RAGANYTHING START ===")
    logger.info(f"File: {file_path}")
    logger.info(f"KB ID: {kb_id}")
    logger.info(f"Doc ID: {doc_id}")
    logger.info(f"Parser: {parser}")
    
    try:
        from raganything import RAGAnything
        from raganything.config import RAGAnythingConfig
        
        # Create namespaced working directory
        namespace = f"kb_{kb_id}"
        working_dir = f"./rag_storage/{namespace}"
        
        # Select parser based on file extension
        from pathlib import Path
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.md', '.txt']:
            # For simple text files, read content and pass to ainsert
            from server.models.knowledge_base import KnowledgeBase
            from sqlalchemy import select
            
            # Get KB to create proper RAG instance
            result_db = await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
            )
            kb = result_db.scalar_one_or_none()
            
            if not kb:
                return {
                    'success': False,
                    'error': f'Knowledge base not found: {kb_id}',
                }
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Read MD/TXT file content: {len(content)} chars")
            
            # Get RAG instance from manager (properly configured with LLM and embedding)
            rag_manager.initialize()
            async with rag_manager.get_rag_instance(kb) as rag:
                logger.info(f"Processing MD/TXT file with ainsert...")
                logger.info(f"File path: {file_path}")
                logger.info(f"Doc ID: {doc_id}")
                
                try:
                    logger.warning(f"\n=== CALLING AINSERT ===")
                    logger.warning(f"Input content length: {len(content)}")
                    logger.warning(f"File paths: {str(doc_id)}")
                    logger.warning(f"IDs: {str(doc_id)}")
                    
                    # Pass content string (not file path!) to ainsert
                    track_id = await rag.lightrag.ainsert(
                        input=content,  # Pass content string!
                        file_paths=str(doc_id),
                        ids=str(doc_id),
                    )
                    logger.warning(f"✅ ainsert() completed with track_id: {track_id}")
                    
                    # Check if document was actually processed
                    doc_status = await rag.lightrag.doc_status.get_by_id(str(doc_id))
                    if doc_status:
                        logger.warning(f"Doc status: {doc_status.get('status')}")
                        logger.warning(f"Chunks count: {doc_status.get('chunks_count')}")
                    else:
                        logger.warning(f"❌ Doc status not found!")
                    
                    return {
                        'success': True,
                        'doc_id': str(doc_id),
                        'content_blocks': 1,
                    }
                except Exception as insert_error:
                    logger.error(f"❌ Insertion failed: {insert_error}", exc_info=True)
                    return {
                        'success': False,
                        'error': f'Failed to insert document: {insert_error}',
                    }
        elif file_ext == '.pdf':
            # Use configured parser for PDF (default: mineru remote API)
            selected_parser = parser
        elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            # Use paddleocr for images (local OCR, no API needed)
            selected_parser = 'paddleocr'
        else:
            # Default to configured parser
            selected_parser = parser
        
        # Create config
        config = RAGAnythingConfig(
            parser=selected_parser,
            parse_method=parse_method,
            working_dir=working_dir,
            parser_output_dir=f"{working_dir}/output",
            enable_image_processing=True,
            enable_table_processing=True,
        )
        
        # Initialize LLM and embedding functions from environment variables
        from raganything.config import get_llm_model_func, get_embedding_func
        llm_func = get_llm_model_func()
        embedding_func = get_embedding_func()
        
        if not llm_func:
            logger.error("Failed to initialize LLM function from environment")
            return {'success': False, 'error': 'LLM function not initialized'}
        
        if not embedding_func:
            logger.error("Failed to initialize embedding function from environment")
            return {'success': False, 'error': 'Embedding function not initialized'}
        
        logger.info(f"Initialized LLM: {llm_func}")
        logger.info(f"Initialized Embedding: {embedding_func}")
        
        # Create RAGAnything instance with model functions
        rag = RAGAnything(
            config=config,
            llm_model_func=llm_func,
            embedding_func=embedding_func
        )
        
        # Process document
        result = await rag.process_document_complete(
            file_path=file_path,
            doc_id=str(doc_id),
        )
        
        return {
            'success': True,
            'doc_id': result.get('doc_id', str(doc_id)),
            'content_blocks': len(result.get('content_list', [])),
        }
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return {
            'success': False,
            'error': str(e),
            'error_detail': error_detail,
        }
