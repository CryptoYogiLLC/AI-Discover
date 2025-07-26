"""Tests for AI response caching service"""

import pytest
from unittest.mock import AsyncMock, patch
import json

from app.services.cache import (
    AIResponseCache,
    CacheStrategy,
    CacheMetrics,
    get_ai_cache,
    cache_ai_response,
)


@pytest.fixture
async def mock_redis():
    """Create mock Redis client"""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.ttl = AsyncMock(return_value=300)
    mock.expire = AsyncMock(return_value=True)
    mock.info = AsyncMock(return_value={"used_memory": 1024000})
    mock.scan_iter = AsyncMock(return_value=AsyncIterator([]))
    return mock


class AsyncIterator:
    """Helper class for async iteration in tests"""

    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


@pytest.fixture
async def ai_cache(mock_redis):
    """Create AI cache instance with mock Redis"""
    cache = AIResponseCache()
    with patch("app.services.cache.redis.from_url", return_value=mock_redis):
        await cache.connect()
        cache._client = mock_redis
    return cache


class TestAIResponseCache:
    """Test AIResponseCache functionality"""

    @pytest.mark.asyncio
    async def test_cache_initialization(self):
        """Test cache initialization"""
        cache = AIResponseCache(default_strategy=CacheStrategy.AGGRESSIVE)
        assert cache.default_strategy == CacheStrategy.AGGRESSIVE
        assert cache._client is None
        assert isinstance(cache._metrics, CacheMetrics)

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, ai_cache):
        """Test cache key generation"""
        # Simple key
        key = ai_cache._generate_cache_key("suggestion", "field1")
        assert key == "ai_cache:suggestion:field1"

        # Key with context
        context = {"form_type": "test", "user_id": 123}
        key_with_context = ai_cache._generate_cache_key("suggestion", "field1", context)
        assert key_with_context.startswith("ai_cache:suggestion:field1:")
        assert len(key_with_context.split(":")) == 4

    @pytest.mark.asyncio
    async def test_cache_get_miss(self, ai_cache, mock_redis):
        """Test cache miss"""
        mock_redis.get.return_value = None

        result = await ai_cache.get("suggestion", "field1")

        assert result is None
        assert ai_cache._metrics.misses == 1
        assert ai_cache._metrics.hits == 0
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_get_hit(self, ai_cache, mock_redis):
        """Test cache hit"""
        cached_value = {"value": "test", "confidence": 0.8}
        mock_redis.get.return_value = json.dumps(cached_value)

        result = await ai_cache.get("suggestion", "field1")

        assert result == cached_value
        assert ai_cache._metrics.hits == 1
        assert ai_cache._metrics.misses == 0
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_set_default_strategy(self, ai_cache, mock_redis):
        """Test setting cache with default strategy"""
        value = {"value": "test", "confidence": 0.8}

        success = await ai_cache.set("suggestion", "field1", value)

        assert success is True
        mock_redis.setex.assert_called_once()

        # Check TTL for moderate strategy (15 minutes)
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 900  # TTL in seconds

    @pytest.mark.asyncio
    async def test_cache_set_with_strategy(self, ai_cache, mock_redis):
        """Test setting cache with specific strategy"""
        value = {"value": "test"}

        success = await ai_cache.set(
            "suggestion", "field1", value, strategy=CacheStrategy.AGGRESSIVE
        )

        assert success is True

        # Check TTL for aggressive strategy (1 hour)
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 3600

    @pytest.mark.asyncio
    async def test_cache_set_with_ttl_override(self, ai_cache, mock_redis):
        """Test setting cache with TTL override"""
        value = {"value": "test"}

        success = await ai_cache.set(
            "suggestion", "field1", value, ttl_override=7200  # 2 hours
        )

        assert success is True

        # Check custom TTL
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 7200

    @pytest.mark.asyncio
    async def test_adaptive_strategy(self, ai_cache, mock_redis):
        """Test adaptive caching strategy"""
        value = {"value": "test"}

        # First access - normal TTL
        await ai_cache.set(
            "suggestion", "field1", value, strategy=CacheStrategy.ADAPTIVE
        )

        call_args = mock_redis.setex.call_args
        base_ttl = call_args[0][1]
        assert base_ttl == 600  # Default adaptive TTL

        # Simulate multiple accesses
        key = ai_cache._generate_cache_key("suggestion", "field1")
        ai_cache._access_counts[key] = 15

        # Set again - should have increased TTL
        await ai_cache.set(
            "suggestion", "field1", value, strategy=CacheStrategy.ADAPTIVE
        )

        call_args = mock_redis.setex.call_args
        increased_ttl = call_args[0][1]
        assert increased_ttl > base_ttl

    @pytest.mark.asyncio
    async def test_cache_invalidate_specific(self, ai_cache, mock_redis):
        """Test invalidating specific cache entry"""
        mock_redis.delete.return_value = 1

        deleted = await ai_cache.invalidate("suggestion", "field1")

        assert deleted == 1
        assert ai_cache._metrics.evictions == 1
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_invalidate_type(self, ai_cache, mock_redis):
        """Test invalidating all entries of a type"""
        # Mock scan_iter to return some keys
        mock_keys = ["ai_cache:suggestion:field1", "ai_cache:suggestion:field2"]
        mock_redis.scan_iter = AsyncMock(return_value=AsyncIterator(mock_keys))
        mock_redis.delete.return_value = 2

        deleted = await ai_cache.invalidate("suggestion")

        assert deleted == 2
        assert ai_cache._metrics.evictions == 2
        mock_redis.delete.assert_called_once_with(*mock_keys)

    @pytest.mark.asyncio
    async def test_warm_cache(self, ai_cache, mock_redis):
        """Test cache warming"""
        cache_entries = [
            {
                "cache_type": "suggestion",
                "identifier": "field1",
                "value": {"value": "default1"},
            },
            {
                "cache_type": "suggestion",
                "identifier": "field2",
                "value": {"value": "default2"},
                "context": {"form_type": "test"},
            },
        ]

        success_count = await ai_cache.warm_cache(cache_entries)

        assert success_count == 2
        assert mock_redis.setex.call_count == 2

    @pytest.mark.asyncio
    async def test_get_metrics(self, ai_cache, mock_redis):
        """Test getting cache metrics"""
        # Set some metrics
        ai_cache._metrics.hits = 10
        ai_cache._metrics.misses = 5

        metrics = await ai_cache.get_metrics()

        assert metrics.hits == 10
        assert metrics.misses == 5
        assert metrics.cache_size_bytes == 1024000  # From mock
        mock_redis.info.assert_called_once_with("memory")

    @pytest.mark.asyncio
    async def test_optimize_cache(self, ai_cache, mock_redis):
        """Test cache optimization"""
        # Set up access patterns
        ai_cache._access_counts = {
            "key1": 1,  # Rarely accessed
            "key2": 15,  # Frequently accessed
            "key3": 5,  # Moderately accessed
        }

        # Mock TTL for frequently accessed key
        mock_redis.ttl.return_value = 600  # 10 minutes
        mock_redis.delete.return_value = 1

        report = await ai_cache.optimize_cache()

        assert report["keys_analyzed"] == 3
        assert report["keys_evicted"] == 1  # key1 should be evicted
        assert len(report["optimizations"]) > 0

        # Check that rarely accessed key was deleted
        mock_redis.delete.assert_called_once_with("key1")

        # Check that TTL was extended for frequently accessed key
        mock_redis.expire.assert_called_once_with("key2", 3600)

    @pytest.mark.asyncio
    async def test_clear_all(self, ai_cache, mock_redis):
        """Test clearing all cache entries"""
        mock_keys = ["ai_cache:suggestion:field1", "ai_cache:validation:field2"]
        mock_redis.scan_iter = AsyncMock(return_value=AsyncIterator(mock_keys))
        mock_redis.delete.return_value = 2

        # Add some tracking data
        ai_cache._warm_cache_keys.add("key1")
        ai_cache._access_counts["key1"] = 5

        success = await ai_cache.clear_all()

        assert success is True
        assert len(ai_cache._warm_cache_keys) == 0
        assert len(ai_cache._access_counts) == 0
        mock_redis.delete.assert_called_once_with(*mock_keys)

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager"""
        with patch("app.services.cache.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            async with AIResponseCache() as cache:
                assert cache._client is not None

            mock_client.close.assert_called_once()

    def test_get_ai_cache_singleton(self):
        """Test singleton cache instance"""
        # Clear any existing instance
        import app.services.cache

        app.services.cache._cache_instance = None

        cache1 = get_ai_cache()
        cache2 = get_ai_cache()

        assert cache1 is cache2


class TestCacheDecorator:
    """Test cache_ai_response decorator"""

    @pytest.mark.asyncio
    async def test_decorator_cache_miss(self):
        """Test decorator with cache miss"""
        with patch("app.services.cache.get_ai_cache") as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True
            mock_get_cache.return_value = mock_cache

            @cache_ai_response("test_type", strategy=CacheStrategy.MODERATE)
            async def test_function(param1, param2=None):
                return {"result": param1 + (param2 or 0)}

            result = await test_function(5, param2=3)

            assert result == {"result": 8}
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_decorator_cache_hit(self):
        """Test decorator with cache hit"""
        with patch("app.services.cache.get_ai_cache") as mock_get_cache:
            mock_cache = AsyncMock()
            cached_result = {"result": 8}
            mock_cache.get.return_value = cached_result
            mock_get_cache.return_value = mock_cache

            @cache_ai_response("test_type")
            async def test_function(param1, param2=None):
                # This should not be called
                raise AssertionError("Function should not be called on cache hit")

            result = await test_function(5, param2=3)

            assert result == cached_result
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_not_called()
