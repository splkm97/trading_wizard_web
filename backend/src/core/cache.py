"""Redis cache service with in-memory fallback for development."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CacheService:
    """Multi-layer cache service using Redis with in-memory fallback."""

    def __init__(self, redis_url: Optional[str] = None):
        self._redis = None
        self._local_cache: Dict[str, Tuple[Any, datetime]] = {}

        if redis_url:
            try:
                import redis

                self._redis = redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory fallback: {e}")
                self._redis = None

    @property
    def is_redis_available(self) -> bool:
        """Check if Redis is available."""
        return self._redis is not None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if self._redis:
            try:
                data = self._redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        else:
            # In-memory fallback with TTL check
            if key in self._local_cache:
                value, expires_at = self._local_cache[key]
                if datetime.now() < expires_at:
                    return value
                else:
                    del self._local_cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> bool:
        """Set value in cache with TTL."""
        if self._redis:
            try:
                self._redis.setex(key, ttl_seconds, json.dumps(value, default=str))
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                return False
        else:
            # In-memory fallback
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            self._local_cache[key] = (value, expires_at)
            return True

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if self._redis:
            try:
                self._redis.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                return False
        else:
            if key in self._local_cache:
                del self._local_cache[key]
            return True

    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern (Redis only)."""
        if self._redis:
            try:
                keys = self._redis.keys(pattern)
                if keys:
                    return self._redis.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear_pattern error: {e}")
        else:
            # In-memory: simple prefix matching
            to_delete = [k for k in self._local_cache if k.startswith(pattern.replace("*", ""))]
            for k in to_delete:
                del self._local_cache[k]
            return len(to_delete)
        return 0

    # Cache key generators
    @staticmethod
    def signals_key(strategy: str = "bollinger") -> str:
        """Generate cache key for signals."""
        return f"signals:{strategy}:latest"

    @staticmethod
    def user_recommendations_key(user_id: int) -> str:
        """Generate cache key for user-specific recommendations."""
        return f"recommendations:user:{user_id}"

    @staticmethod
    def prices_key(stock_codes: List[str]) -> str:
        """Generate cache key for batch prices."""
        codes_hash = hash(frozenset(stock_codes))
        return f"prices:batch:{codes_hash}"

    @staticmethod
    def stock_price_key(stock_code: str) -> str:
        """Generate cache key for single stock price."""
        return f"price:{stock_code}"


# Lazy initialization - will be initialized when first accessed
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create cache service instance."""
    global _cache_service
    if _cache_service is None:
        from src.core.config import settings

        _cache_service = CacheService(settings.REDIS_URL)
    return _cache_service


# Convenience alias
cache_service = get_cache_service
