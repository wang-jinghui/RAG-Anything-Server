"""
RAG Anything service manager for document processing and querying.

This module provides a service layer to manage RAGAnything instances
with proper configuration and tenant isolation.
"""
import asyncio
from typing import Dict, Optional, Any
from uuid import UUID
from contextlib import asynccontextmanager

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
        
        # Convert to LightRAG kwargs
        lightrag_kwargs = rag_config.to_lightrag_kwargs()
        
        # Create RAGAnything instance
        rag = RAGAnything(
            config=type('Config', (), {
                'working_dir': namespaced_working_dir,
                'parse_method': 'mineru',
                'parser': 'mineru',
                'enable_image_processing': True,
                '__dict__': {}
            })(),
            llm_model_func=llm_model_func or self._default_llm_func(config),
            embedding_func=embedding_func or self._default_embedding_func(config),
            **lightrag_kwargs
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
            
            async def llm_func(prompts: list[str], **kwargs) -> list[str]:
                responses = []
                for prompt in prompts:
                    response = await ollama.async_chat(
                        model=config.llm.model,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    responses.append(response['message']['content'])
                return responses
            
            return llm_func
        
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
            
            return embed_func
        
        elif config.embedding.provider == "ollama":
            import ollama
            
            async def embed_func(texts: list[str]) -> list[list[float]]:
                all_embeddings = []
                for text in texts:
                    response = await ollama.async_embed(
                        model=config.embedding.model,
                        prompt=text
                    )
                    all_embeddings.append(response['embeddings'][0])
                return all_embeddings
            
            return embed_func
        
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
            
            return embed_func
    
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
