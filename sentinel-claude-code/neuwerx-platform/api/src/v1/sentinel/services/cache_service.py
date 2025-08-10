from typing import Optional, Any
from datetime import datetime, timedelta
import json
from abc import ABC, abstractmethod
import logging

from ..config import settings

logger = logging.getLogger(__name__)

class CacheServiceInterface(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300):
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        pass
    
    @abstractmethod
    async def clear(self):
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

class InMemoryCacheService(CacheServiceInterface):
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    async def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if key in self._expiry and datetime.now() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                return None
            return self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        self._cache[key] = value
        self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
        logger.debug(f"Cached key: {key} with TTL: {ttl}s")
    
    async def delete(self, key: str):
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        logger.debug(f"Deleted cache key: {key}")
    
    async def clear(self):
        self._cache.clear()
        self._expiry.clear()
        logger.info("Cache cleared")
    
    async def exists(self, key: str) -> bool:
        if key in self._cache:
            if key in self._expiry and datetime.now() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                return False
            return True
        return False

class RedisCacheService(CacheServiceInterface):
    
    def __init__(self):
        import redis.asyncio as redis
        self._redis = None
        self._pool = None
    
    async def _get_connection(self):
        if not self._redis:
            import redis.asyncio as redis
            self._pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            self._redis = redis.Redis(connection_pool=self._pool)
        return self._redis
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            redis = await self._get_connection()
            value = await redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        try:
            redis = await self._get_connection()
            await redis.setex(key, ttl, json.dumps(value))
            logger.debug(f"Cached key: {key} with TTL: {ttl}s")
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
    
    async def delete(self, key: str):
        try:
            redis = await self._get_connection()
            await redis.delete(key)
            logger.debug(f"Deleted cache key: {key}")
        except Exception as e:
            logger.error(f"Redis delete error: {str(e)}")
    
    async def clear(self):
        try:
            redis = await self._get_connection()
            await redis.flushdb()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Redis clear error: {str(e)}")
    
    async def exists(self, key: str) -> bool:
        try:
            redis = await self._get_connection()
            return await redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {str(e)}")
            return False

class CacheServiceFactory:
    _instance = None
    
    @staticmethod
    def get_cache_service() -> CacheServiceInterface:
        if CacheServiceFactory._instance is None:
            if settings.REDIS_ENABLED:
                CacheServiceFactory._instance = RedisCacheService()
                logger.info("Using Redis cache service")
            else:
                CacheServiceFactory._instance = InMemoryCacheService()
                logger.info("Using in-memory cache service")
        return CacheServiceFactory._instance

cache_service = CacheServiceFactory.get_cache_service()