from __future__ import annotations

import time
import asyncio

from loguru import logger

from core.cache.redis_manager import redis_manager
from core.config import settings


class DistributedRateLimiter:
    """Rate limiter that uses Redis for distributed rate limiting in production."""

    def __init__(self, burst: int = 20, window: int = 60):
        self.burst = burst
        self.window = window
        self._rate_limit_enabled = settings.env in {"production", "staging"}

    async def acquire(self, key: str, limit: int = 6, window: int = 60) -> bool:
        """
        Acquire a rate limit token.

        Args:
            key: Unique identifier for the client/user
            limit: Maximum number of requests allowed in the window
            window: Time window in seconds

        Returns:
            bool: True if request is allowed, False otherwise
        """
        if not self._rate_limit_enabled:
            return True  # Allow all requests in development

        try:
            # Use Redis for distributed rate limiting
            if redis_manager.client is None:
                if settings.env in {"production", "staging"}:
                    # Fail-closed in production if Redis is unavailable
                    logger.error("Redis unavailable in production - blocking all requests")
                    return False
                else:
                    # Allow in development/testing if Redis unavailable
                    logger.warning("Redis unavailable - allowing request in non-production")
                    return True

            # Use sliding window counter algorithm with Redis
            now = time.time()
            pipeline = redis_manager.client.pipeline()

            # Remove expired entries
            pipeline.zremrangebyscore(key, 0, now - window)

            # Count current requests in window
            pipeline.zcard(key)

            # Add current request
            pipeline.zadd(key, {f"req_{now}": now})

            # Set expiration
            pipeline.expire(key, int(window + 1))

            results = await pipeline.execute()
            current_requests = results[1]

            # Return whether we're under the limit
            return current_requests < limit

        except Exception as e:
            logger.error(f"Redis rate limiter error: {e}")
            if settings.env in {"production", "staging"}:
                # Fail-closed in production
                return False
            else:
                # Allow in development/testing
                return True


class InMemoryFallbackLimiter:
    """In-memory fallback rate limiter for single-node scenarios."""

    def __init__(self, burst: int = 20, window: float = 60.0):
        self.burst = burst
        self.window = window
        self._hits: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()
        logger.warning("Using in-memory rate limiter - not suitable for production!")

    async def is_allowed(self, key: str, limit: int = 6) -> bool:
        """Acquire a rate limit token using in-memory storage with thread-safe operations."""
        now = time.time()

        async with self._lock:  # Prevent race conditions
            # Clean old hits
            if key in self._hits:
                self._hits[key] = [hit for hit in self._hits[key] if now - hit < self.window]
            else:
                self._hits[key] = []

            # Check if under limit
            if len(self._hits[key]) < limit:
                self._hits[key].append(now)
                return True

            return False


class AsyncRateLimiter:
    """
    Async Redis rate limiter using centralized redis_manager.
    Pipeline reduces network round-trips.
    Includes an in-memory fallback (Pre-Deletion Safety Check).

    বাংলা: কেন্দ্রীয় redis_manager ব্যবহার করে — আলাদা Redis connection তৈরি করে না।
    Zero-Cost, ফ্রি-টিয়ার Upstash Redis এর সাথে সামঞ্জস্যপূর্ণ।
    """

    def __init__(self) -> None:
        self._rate_limit_enabled: bool = os.getenv(
            "RATE_LIMIT_ENABLED", "true"
        ).lower() in {
            "true",
            "1",
            "yes",
        }
        self._fallback_limiter = InMemoryFallbackLimiter()

    async def _get_redis(self):
        """Helper for test mock compatibility."""
        return await redis_manager.get_client_async()

    async def acquire(self, key: str, limit: int, window: int) -> bool:
        if not self._rate_limit_enabled:
            return True
        try:
            client = await self._get_redis()
            if client is None:
                return self._fallback_limiter.is_allowed(key, limit=limit)
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            results = await pipe.execute()
            current = results[0]
            return current <= limit
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"Redis rate limiter unavailable: {e}. Falling back to in-memory limiter (degraded mode)."
            )
            return self._fallback_limiter.is_allowed(key, limit=limit)

    async def acquire_tenant(self, tenant_id: str, tier: str = "free") -> bool:
        """Multi-tenant tier-based rate limiting. (Bangla: টেন্যান্ট-ভিত্তিক টিয়ার্ড রেট লিমিট)"""
        tiers = {
            "free": (60, 60),  # 60 requests per 60 seconds
            "pro": (600, 60),  # 600 requests per 60 seconds
            "enterprise": (6000, 60),  # 6000 requests per 60 seconds
        }
        limit, window = tiers.get(tier.lower(), tiers["free"])
        key = f"rate_limit:tenant:{tenant_id}:{tier}"
        return await self.acquire(key, limit=limit, window=window)

    async def close(self) -> None:
        # বাংলা মন্তব্য: আলাদা Redis connection নেই — centralized redis_manager বন্ধ করা যাবে না এখান থেকে
        pass


rate_limiter = AsyncRateLimiter()


async def advanced_rate_limit_check(
    key: str,
    limit: int = 100,
    window: int = 3600,
    burst_multiplier: float = 1.5,
) -> bool:
    """Advanced rate limiting with burst capability. (Bangla: বার্স্ট ক্যাপাবিলিটি সহ অ্যাডভান্সড রেট লিমিটিং)

    Args:
        key: The rate limit identifier key (IP or user ID).
        limit: Base rate limit per window.
        window: Time window in seconds.
        burst_multiplier: Multiplier for burst allowance.

    Returns:
        bool: True if request is allowed, False otherwise.
    """
    effective_limit = int(limit * burst_multiplier)
    return await rate_limiter.acquire(key, limit=effective_limit, window=window)
