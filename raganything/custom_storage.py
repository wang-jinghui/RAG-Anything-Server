"""
Custom storage classes with proper workspace isolation for multi-tenant support.
"""

from lightrag.kg.postgres_impl import PGVectorStorage, SQL_TEMPLATES
from lightrag.kg import STORAGE_IMPLEMENTATIONS


class IsolatedPGVectorStorage(PGVectorStorage):
    """
    PGVectorStorage with dynamic workspace resolution.
    
    Problem: The original PGVectorStorage caches self.workspace during __post_init__,
    which is set from self.db.workspace at initialization time. When ClientManager
    reuses the same PostgreSQLDB instance across multiple tenants, the cached
    self.workspace becomes stale and causes cross-tenant data leakage.
    
    Solution: Override the query method to always use the current self.db.workspace
    value instead of the cached self.workspace.
    """
    
    async def query(self, query: str, top_k: int, query_embedding: list[float] = None) -> list[dict]:
        """
        Override query to use dynamic workspace from db instance.
        
        This ensures proper multi-tenant isolation by always using the current
        db.workspace value, even when it changes between queries.
        """
        if query_embedding is not None:
            embedding = query_embedding
        else:
            embeddings = await self.embedding_func(
                [query], _priority=5
            )
            embedding = embeddings[0]

        embedding_string = ",".join(map(str, embedding))

        vector_cast = (
            "halfvec"
            if getattr(self.db, "vector_index_type", None) == "HNSW_HALFVEC"
            else "vector"
        )
        
        # CRITICAL: Use self.workspace which is set per LightRAG instance
        # NOT self.db.workspace which is shared across all instances
        current_workspace = self.workspace
        
        # Debug logging
        from lightrag.utils import logger as lightrag_logger
        lightrag_logger.info(f"[IsolatedPGVectorStorage] Query workspace: {current_workspace}, namespace: {self.namespace}")
        
        sql = SQL_TEMPLATES[self.namespace].format(
            embedding_string=embedding_string,
            table_name=self.table_name,
            vector_cast=vector_cast,
        )
        params = {
            "workspace": current_workspace,  # Use dynamic workspace
            "closer_than_threshold": 1 - self.cosine_better_than_threshold,
            "top_k": top_k,
        }
        results = await self.db.query(sql, params=list(params.values()), multirows=True)
        return results


# Register our custom storage class with LightRAG
STORAGE_IMPLEMENTATIONS["VECTOR_STORAGE"]["implementations"].append("IsolatedPGVectorStorage")

# Also add to STORAGES dict so LightRAG can find the module
from lightrag.kg import STORAGES
STORAGES["IsolatedPGVectorStorage"] = "raganything.custom_storage"
