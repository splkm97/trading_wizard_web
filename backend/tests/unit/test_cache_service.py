"""Unit tests for the cache service."""

import time


class TestCacheService:
    """Tests for CacheService functionality."""

    def test_local_cache_set_and_get(self):
        """Test basic set/get operations with local cache."""
        from src.core.cache import CacheService

        cache = CacheService(redis_url=None)  # Force local cache

        # Set a value
        cache.set("test_key", {"data": "value"}, ttl_seconds=60)

        # Get the value
        result = cache.get("test_key")
        assert result == {"data": "value"}

    def test_local_cache_ttl_expiry(self):
        """Test that cached values expire after TTL."""
        from src.core.cache import CacheService

        cache = CacheService(redis_url=None)

        # Set with very short TTL
        cache.set("expire_key", {"data": "temporary"}, ttl_seconds=1)

        # Should exist immediately
        assert cache.get("expire_key") is not None

        # Wait for expiry
        time.sleep(1.5)

        # Should be expired now
        assert cache.get("expire_key") is None

    def test_local_cache_delete(self):
        """Test delete operation."""
        from src.core.cache import CacheService

        cache = CacheService(redis_url=None)

        cache.set("delete_key", {"data": "to_delete"}, ttl_seconds=60)
        assert cache.get("delete_key") is not None

        cache.delete("delete_key")
        assert cache.get("delete_key") is None

    def test_local_cache_clear_pattern(self):
        """Test clear_pattern operation."""
        from src.core.cache import CacheService

        cache = CacheService(redis_url=None)

        # Set multiple keys with same prefix
        cache.set("signals:bollinger:latest", {"data": 1}, ttl_seconds=60)
        cache.set("signals:contrarian:latest", {"data": 2}, ttl_seconds=60)
        cache.set("prices:batch:123", {"data": 3}, ttl_seconds=60)

        # Clear signals prefix
        count = cache.clear_pattern("signals:*")
        assert count == 2

        # Verify signals are cleared
        assert cache.get("signals:bollinger:latest") is None
        assert cache.get("signals:contrarian:latest") is None

        # Verify prices still exist
        assert cache.get("prices:batch:123") is not None

    def test_cache_key_generators(self):
        """Test cache key generator methods."""
        from src.core.cache import CacheService

        assert CacheService.signals_key("bollinger") == "signals:bollinger:latest"
        assert CacheService.signals_key("contrarian") == "signals:contrarian:latest"
        assert CacheService.user_recommendations_key(123) == "recommendations:user:123"
        assert CacheService.stock_price_key("005930") == "price:005930"

    def test_is_redis_available_false_without_redis(self):
        """Test is_redis_available returns False when Redis not configured."""
        from src.core.cache import CacheService

        cache = CacheService(redis_url=None)
        assert cache.is_redis_available is False

    def test_get_nonexistent_key_returns_none(self):
        """Test getting a non-existent key returns None."""
        from src.core.cache import CacheService

        cache = CacheService(redis_url=None)
        assert cache.get("nonexistent_key") is None

    def test_cache_complex_data_structures(self):
        """Test caching complex nested data structures."""
        from src.core.cache import CacheService

        cache = CacheService(redis_url=None)

        complex_data = {
            "signals": [
                {
                    "stock_code": "005930",
                    "stock_name": "Samsung Electronics",
                    "confidence_score": 75.5,
                    "indicators": {"rsi": 45.2, "macd_histogram": 0.5},
                },
                {
                    "stock_code": "000660",
                    "stock_name": "SK Hynix",
                    "confidence_score": 68.3,
                    "indicators": {"rsi": 42.1, "macd_histogram": 0.3},
                },
            ],
            "computed_at": "2026-01-13T10:00:00",
            "count": 2,
        }

        cache.set("test_complex", complex_data, ttl_seconds=60)
        result = cache.get("test_complex")

        assert result == complex_data
        assert len(result["signals"]) == 2
        assert result["signals"][0]["stock_code"] == "005930"
