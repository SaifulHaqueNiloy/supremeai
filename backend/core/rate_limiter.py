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


def get_rate_limiter():
    """Get appropriate rate limiter based on environment settings."""
    if settings.env in {"production", "staging"}:
        return DistributedRateLimiter()
    else:
        # In development, prefer Redis if available, fallback to in-memory
        if redis_manager.client:
            return DistributedRateLimiter()
        else:
            return InMemoryFallbackLimiter()
