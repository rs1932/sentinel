"""
Cache Manager for RBAC Service

Simple in-memory cache with TTL support. Can be extended to use Redis
in production environments.
"""

import asyncio
import time
from typing import Optional, Dict, Any
from src.utils.logging import get_logger

logger = get_logger(__name__)


class InMemoryCacheManager:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up expired entries."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())
    
    async def _cleanup_expired(self):
        """Background task to remove expired cache entries."""
        while True:
            try:
                current_time = time.time()
                expired_keys = []
                
                for key, entry in self._cache.items():
                    if entry['expires_at'] <= current_time:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self._cache[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
                # Run cleanup every 60 seconds
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {e}")
                await asyncio.sleep(60)
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        if entry['expires_at'] <= time.time():
            # Expired
            del self._cache[key]
            return None
        
        return entry['value']
    
    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        """Set value in cache with TTL in seconds."""
        expires_at = time.time() + ttl
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at
        }
    
    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        self._cache.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of entries in cache."""
        return len(self._cache)
    
    async def close(self):
        """Close cache manager and cleanup resources."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


# Global cache manager instance
_cache_manager: Optional[InMemoryCacheManager] = None


async def get_cache_manager() -> InMemoryCacheManager:
    """Get or create the global cache manager instance."""
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = InMemoryCacheManager()
        logger.info("Created in-memory cache manager")
    
    return _cache_manager


async def close_cache_manager():
    """Close the global cache manager."""
    global _cache_manager
    
    if _cache_manager:
        await _cache_manager.close()
        _cache_manager = None
        logger.info("Closed cache manager")


# Type alias for dependency injection
CacheManager = InMemoryCacheManager