"""Redis caching service for AI responses with intelligent cache management"""

import json
import hashlib
from typing import Optional, Any, Dict, List, Set
from datetime import datetime
from enum import Enum

import redis.asyncio as redis
from structlog import get_logger
from pydantic import BaseModel, Field

from app.core.config import settings

logger = get_logger(__name__)


class CacheStrategy(str, Enum):
    """Cache strategies for different types of AI responses"""

    AGGRESSIVE = "aggressive"  # Cache for long periods (suggestions)
    MODERATE = "moderate"  # Cache for moderate periods (validations)
    CONSERVATIVE = "conservative"  # Cache for short periods (real-time data)
    ADAPTIVE = "adaptive"  # Adjust based on usage patterns


class CacheMetrics(BaseModel):
    """Metrics for cache performance tracking"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    avg_response_time_ms: float = 0.0
    cache_size_bytes: int = 0
    last_reset: datetime = Field(default_factory=datetime.utcnow)


class AIResponseCache:
    """Redis-based caching service for AI responses"""

    # Default TTLs for different strategies (in seconds)
    TTL_MAPPING = {
        CacheStrategy.AGGRESSIVE: 3600,  # 1 hour
        CacheStrategy.MODERATE: 900,  # 15 minutes
        CacheStrategy.CONSERVATIVE: 300,  # 5 minutes
        CacheStrategy.ADAPTIVE: 600,  # 10 minutes (default)
    }

    # Prefix for all AI cache keys
    KEY_PREFIX = "ai_cache"

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_strategy: CacheStrategy = CacheStrategy.MODERATE,
    ):
        """Initialize AI Response Cache

        Args:
            redis_url: Redis connection URL
            default_strategy: Default caching strategy
        """
        self.redis_url = redis_url or str(settings.REDIS_URL)
        self.default_strategy = default_strategy
        self._client: Optional[redis.Redis[Any]] = None
        self._metrics = CacheMetrics()
        self._warm_cache_keys: Set[str] = set()
        self._access_counts: Dict[str, int] = {}

    async def connect(self) -> None:
        """Connect to Redis"""
        if not self._client:
            self._client = await redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            logger.info("Connected to Redis for AI caching")

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")

    async def __aenter__(self) -> "AIResponseCache":
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.disconnect()

    def _generate_cache_key(
        self, cache_type: str, identifier: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a unique cache key

        Args:
            cache_type: Type of cache (suggestion, validation, etc.)
            identifier: Unique identifier (field name, form type, etc.)
            context: Additional context for key generation

        Returns:
            Unique cache key
        """
        key_parts = [self.KEY_PREFIX, cache_type, identifier]

        if context:
            # Sort context items for consistent key generation
            context_str = json.dumps(sorted(context.items()))
            context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
            key_parts.append(context_hash)

        return ":".join(key_parts)

    async def get(
        self, cache_type: str, identifier: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Get value from cache

        Args:
            cache_type: Type of cache
            identifier: Unique identifier
            context: Additional context

        Returns:
            Cached value or None if not found
        """
        if not self._client:
            await self.connect()

        key = self._generate_cache_key(cache_type, identifier, context)

        try:
            start_time = datetime.utcnow()
            if not self._client:
                raise RuntimeError("Redis client not connected")
            value = await self._client.get(key)
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            if value:
                self._metrics.hits += 1
                self._access_counts[key] = self._access_counts.get(key, 0) + 1

                # Update average response time
                total_requests = self._metrics.hits + self._metrics.misses
                self._metrics.avg_response_time_ms = (
                    self._metrics.avg_response_time_ms * (total_requests - 1)
                    + response_time
                ) / total_requests

                logger.debug(
                    "Cache hit",
                    cache_type=cache_type,
                    identifier=identifier,
                    response_time_ms=response_time,
                )

                return json.loads(value)
            else:
                self._metrics.misses += 1
                logger.debug("Cache miss", cache_type=cache_type, identifier=identifier)
                return None

        except Exception as e:
            logger.error(
                "Cache get error",
                cache_type=cache_type,
                identifier=identifier,
                error=str(e),
            )
            return None

    async def set(
        self,
        cache_type: str,
        identifier: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
        strategy: Optional[CacheStrategy] = None,
        ttl_override: Optional[int] = None,
    ) -> bool:
        """Set value in cache

        Args:
            cache_type: Type of cache
            identifier: Unique identifier
            value: Value to cache
            context: Additional context
            strategy: Caching strategy (uses default if not provided)
            ttl_override: Override TTL in seconds

        Returns:
            Success status
        """
        if not self._client:
            await self.connect()

        key = self._generate_cache_key(cache_type, identifier, context)
        strategy = strategy or self.default_strategy

        # Determine TTL
        if ttl_override:
            ttl = ttl_override
        else:
            ttl = self.TTL_MAPPING[strategy]

            # Adaptive strategy adjusts TTL based on access patterns
            if strategy == CacheStrategy.ADAPTIVE:
                access_count = self._access_counts.get(key, 0)
                if access_count > 10:
                    ttl = int(ttl * 1.5)  # Increase TTL for frequently accessed items
                elif access_count < 2:
                    ttl = int(ttl * 0.5)  # Decrease TTL for rarely accessed items

        try:
            serialized_value = json.dumps(value)
            success = await self._client.setex(key, ttl, serialized_value)

            if success:
                logger.debug(
                    "Cache set",
                    cache_type=cache_type,
                    identifier=identifier,
                    ttl=ttl,
                    strategy=strategy,
                )

                # Track warm cache keys
                if strategy == CacheStrategy.AGGRESSIVE:
                    self._warm_cache_keys.add(key)

            return bool(success)

        except Exception as e:
            logger.error(
                "Cache set error",
                cache_type=cache_type,
                identifier=identifier,
                error=str(e),
            )
            return False

    async def invalidate(
        self,
        cache_type: str,
        identifier: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Invalidate cache entries

        Args:
            cache_type: Type of cache
            identifier: Specific identifier (None to invalidate all of type)
            context: Additional context

        Returns:
            Number of keys deleted
        """
        if not self._client:
            await self.connect()

        try:
            if identifier:
                # Invalidate specific key
                key = self._generate_cache_key(cache_type, identifier, context)
                deleted = await self._client.delete(key)

                # Remove from warm cache and access counts
                self._warm_cache_keys.discard(key)
                self._access_counts.pop(key, None)

                logger.info(
                    "Cache invalidated",
                    cache_type=cache_type,
                    identifier=identifier,
                    keys_deleted=deleted,
                )
            else:
                # Invalidate all keys of this type
                pattern = f"{self.KEY_PREFIX}:{cache_type}:*"
                keys = []

                async for key in self._client.scan_iter(pattern):
                    keys.append(key)

                if keys:
                    deleted = await self._client.delete(*keys)

                    # Clean up tracking
                    for key in keys:
                        self._warm_cache_keys.discard(key)
                        self._access_counts.pop(key, None)

                    logger.info(
                        "Cache type invalidated",
                        cache_type=cache_type,
                        keys_deleted=deleted,
                    )
                else:
                    deleted = 0

            self._metrics.evictions += deleted
            return deleted

        except Exception as e:
            logger.error(
                "Cache invalidation error", cache_type=cache_type, error=str(e)
            )
            return 0

    async def warm_cache(
        self,
        cache_entries: List[Dict[str, Any]],
        strategy: CacheStrategy = CacheStrategy.AGGRESSIVE,
    ) -> int:
        """Pre-populate cache with common entries

        Args:
            cache_entries: List of entries to cache
                Each entry should have: cache_type, identifier, value, context (optional)
            strategy: Caching strategy for warm entries

        Returns:
            Number of entries cached
        """
        if not self._client:
            await self.connect()

        success_count = 0

        for entry in cache_entries:
            try:
                success = await self.set(
                    cache_type=entry["cache_type"],
                    identifier=entry["identifier"],
                    value=entry["value"],
                    context=entry.get("context"),
                    strategy=strategy,
                )

                if success:
                    success_count += 1

            except Exception as e:
                logger.error("Cache warming error", entry=entry, error=str(e))

        logger.info(
            "Cache warmed",
            total_entries=len(cache_entries),
            success_count=success_count,
        )

        return success_count

    async def get_metrics(self) -> CacheMetrics:
        """Get cache performance metrics

        Returns:
            Cache metrics
        """
        if self._client:
            try:
                # Get cache size
                info = await self._client.info("memory")
                self._metrics.cache_size_bytes = info.get("used_memory", 0)
            except Exception as e:
                logger.error("Failed to get cache size", error=str(e))

        return self._metrics

    async def reset_metrics(self):
        """Reset cache metrics"""
        self._metrics = CacheMetrics()
        logger.info("Cache metrics reset")

    async def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache based on usage patterns

        Returns:
            Optimization report
        """
        if not self._client:
            await self.connect()

        report = {"optimizations": [], "keys_analyzed": 0, "keys_evicted": 0}

        try:
            # Analyze access patterns
            rarely_accessed = []
            frequently_accessed = []

            for key, count in self._access_counts.items():
                if count < 2:
                    rarely_accessed.append(key)
                elif count > 10:
                    frequently_accessed.append(key)

            report["keys_analyzed"] = len(self._access_counts)

            # Evict rarely accessed keys
            if rarely_accessed:
                evicted = await self._client.delete(*rarely_accessed)
                report["keys_evicted"] = evicted
                report["optimizations"].append(
                    f"Evicted {evicted} rarely accessed keys"
                )

                # Clean up tracking
                for key in rarely_accessed:
                    self._access_counts.pop(key, None)
                    self._warm_cache_keys.discard(key)

            # Extend TTL for frequently accessed keys
            for key in frequently_accessed:
                ttl = await self._client.ttl(key)
                if ttl > 0 and ttl < 1800:  # Less than 30 minutes
                    await self._client.expire(key, 3600)  # Extend to 1 hour
                    report["optimizations"].append(
                        f"Extended TTL for frequently accessed key: {key}"
                    )

            logger.info("Cache optimized", report=report)

        except Exception as e:
            logger.error("Cache optimization error", error=str(e))
            report["error"] = str(e)

        return report

    async def clear_all(self) -> bool:
        """Clear all AI cache entries

        Returns:
            Success status
        """
        if not self._client:
            await self.connect()

        try:
            pattern = f"{self.KEY_PREFIX}:*"
            keys = []

            async for key in self._client.scan_iter(pattern):
                keys.append(key)

            if keys:
                await self._client.delete(*keys)

            # Reset tracking
            self._warm_cache_keys.clear()
            self._access_counts.clear()

            logger.info("All AI cache cleared", keys_deleted=len(keys))
            return True

        except Exception as e:
            logger.error("Cache clear error", error=str(e))
            return False


# Singleton instance
_cache_instance: Optional[AIResponseCache] = None


def get_ai_cache() -> AIResponseCache:
    """Get singleton AI cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = AIResponseCache()
    return _cache_instance


# Decorator for caching function results
def cache_ai_response(
    cache_type: str,
    strategy: CacheStrategy = CacheStrategy.MODERATE,
    ttl_override: Optional[int] = None,
):
    """Decorator for caching AI response functions

    Args:
        cache_type: Type of cache
        strategy: Caching strategy
        ttl_override: Override TTL in seconds
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_ai_cache()

            # Generate cache key from function arguments
            identifier = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            identifier_hash = hashlib.md5(identifier.encode()).hexdigest()[:16]

            # Try to get from cache
            cached = await cache.get(cache_type, identifier_hash)
            if cached is not None:
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(
                cache_type,
                identifier_hash,
                result,
                strategy=strategy,
                ttl_override=ttl_override,
            )

            return result

        return wrapper

    return decorator
