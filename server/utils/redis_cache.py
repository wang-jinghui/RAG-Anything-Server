"""
Redis-based query cache with tenant isolation.

Provides a high-performance caching layer for RAG queries with automatic
namespace isolation per knowledge base.
"""
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class RedisQueryCache:
    """
    Redis-backed query cache with knowledge base isolation.
    
    Cache key format: rag:kb:{kb_id}:query:{query_hash}
    
    Features:
    - Automatic namespace isolation per KB
    - Configurable TTL
    - JSON serialization
    - Async support
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 86400,  # 24 hours
        key_prefix: str = "rag"
    ):
        """
        Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds (default: 24h)
            key_prefix: Key prefix for namespacing
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis package is required. Install with: pip install redis"
            )
        
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self._redis_client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            try:
                await self._redis_client.ping()
                logger.info(f"Redis cache initialized: {self.redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
    
    async def close(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
            logger.info("Redis cache closed")
    
    def _generate_cache_key(self, kb_id: str, query: str, mode: str = "naive", **kwargs) -> str:
        """
        Generate cache key with KB isolation.
        
        Args:
            kb_id: Knowledge base ID
            query: Query text
            mode: Query mode
            **kwargs: Additional parameters to include in hash
            
        Returns:
            Cache key string
        """
        # Create a hash of query + parameters
        params_str = f"{query}|{mode}"
        for k, v in sorted(kwargs.items()):
            params_str += f"|{k}={v}"
        
        query_hash = hashlib.md5(params_str.encode('utf-8')).hexdigest()
        
        # Format: rag:kb:{kb_id}:query:{hash}
        return f"{self.key_prefix}:kb:{kb_id}:query:{query_hash}"
    
    async def get(self, kb_id: str, query: str, mode: str = "naive", **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get cached query result.
        
        Args:
            kb_id: Knowledge base ID
            query: Query text
            mode: Query mode
            **kwargs: Additional parameters
            
        Returns:
            Cached result dict or None if cache miss
        """
        if self._redis_client is None:
            await self.initialize()
        
        cache_key = self._generate_cache_key(kb_id, query, mode, **kwargs)
        
        try:
            cached_data = await self._redis_client.get(cache_key)
            if cached_data:
                result = json.loads(cached_data)
                logger.debug(f"Cache HIT: {cache_key[:50]}...")
                return result
            else:
                logger.debug(f"Cache MISS: {cache_key[:50]}...")
                return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def set(
        self,
        kb_id: str,
        query: str,
        answer: str,
        mode: str = "naive",
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Cache query result.
        
        Args:
            kb_id: Knowledge base ID
            query: Query text
            answer: Query answer
            mode: Query mode
            ttl: TTL in seconds (None uses default)
            **kwargs: Additional metadata
            
        Returns:
            True if successful
        """
        if self._redis_client is None:
            await self.initialize()
        
        cache_key = self._generate_cache_key(kb_id, query, mode, **kwargs)
        
        cache_data = {
            "answer": answer,
            "kb_id": kb_id,
            "query": query,
            "mode": mode,
            "created_at": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        try:
            ttl = ttl or self.default_ttl
            await self._redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data, ensure_ascii=False)
            )
            logger.debug(f"Cache SET: {cache_key[:50]}... (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def invalidate_kb_cache(self, kb_id: str) -> int:
        """
        Invalidate all cache entries for a knowledge base.
        
        Call this when documents are uploaded/deleted.
        
        Args:
            kb_id: Knowledge base ID
            
        Returns:
            Number of keys deleted
        """
        if self._redis_client is None:
            await self.initialize()
        
        pattern = f"{self.key_prefix}:kb:{kb_id}:query:*"
        
        try:
            # Find all keys matching the pattern
            keys = []
            async for key in self._redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self._redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries for KB {kb_id}")
                return deleted
            else:
                logger.debug(f"No cache entries found for KB {kb_id}")
                return 0
        except Exception as e:
            logger.error(f"Redis invalidation error: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        if self._redis_client is None:
            await self.initialize()
        
        try:
            info = await self._redis_client.info('stats')
            return {
                "hits": info.get('keyspace_hits', 0),
                "misses": info.get('keyspace_misses', 0),
                "hit_rate": 0,  # Calculate if needed
                "connected_clients": info.get('connected_clients', 0),
                "used_memory_human": info.get('used_memory_human', 'N/A'),
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {}
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Singleton instance for easy access
_query_cache: Optional[RedisQueryCache] = None


def get_query_cache() -> Optional[RedisQueryCache]:
    """Get the global query cache instance."""
    return _query_cache


def init_query_cache(redis_url: str = None, **kwargs) -> RedisQueryCache:
    """
    Initialize the global query cache.
    
    Args:
        redis_url: Redis URL (from env if not provided)
        **kwargs: Additional arguments for RedisQueryCache
        
    Returns:
        RedisQueryCache instance
    """
    global _query_cache
    
    if redis_url is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    _query_cache = RedisQueryCache(redis_url=redis_url, **kwargs)
    return _query_cache
