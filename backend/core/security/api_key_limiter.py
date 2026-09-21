"""Per-API-Key Rate Limiting using sliding window counter.

বাংলা মন্তব্য: একক API key দিয়ে যেন কেউ পুরো সিস্টেম abuse করতে না পারে, সেজন্য প্রতি কি (Key) ভিত্তিক ডিস্ট্রিবিউটেড রেট লিমিটিং।
"""

import time

from fastapi import HTTPException

from core.logging_config import logger

API_KEY_LIMIT_PREFIX = "apikey:rate:"
DEFAULT_MAX_REQUESTS_PER_MINUTE = 60


async def enforce_api_key_rate_limit(
    api_key_hash: str, max_requests: int = DEFAULT_MAX_REQUESTS_PER_MINUTE
) -> None:
    """Enforce rate limits per API Key hash using atomic Redis counters."""
    from core.cache.redis_manager import redis_manager

    if not redis_manager or not getattr(redis_manager, "client", None):
        return  # Fail open gracefully if Redis is down

    current_minute = int(time.time() / 60)
    window_key = f"{API_KEY_LIMIT_PREFIX}{api_key_hash[:16]}:{current_minute}"

    try:
        # Issue #460: single atomic EVAL (1 billable op) instead of the
        # INCR+EXPIRE 2-command pipeline.
        from core.cache.rate_limit_atomic import atomic_window_incr

        current_count = await atomic_window_incr(redis_manager.client, window_key, 120)

        if current_count > max_requests:
            logger.warning(
                f"🚨 API key rate limit exceeded for key hash prefix {api_key_hash[:8]}: ({current_count} hits)"
            )
            raise HTTPException(status_code=429, detail="API key rate limit exceeded")
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"⚠️ API Key rate limiter error: {exc}. Failing open for resilience.")


class APIKeyLimiter:
    """Per-API-key rate limiter facade.

    বাংলা: একক API key-ভিত্তিক rate limiter-এর class-based facade।
    Issue #895: test contract (`backend/tests/core/test_security_and_intelligence_contracts.py`)
    একটি `APIKeyLimiter` class expect করে। এই class বিদ্যমান
    `enforce_api_key_rate_limit()` async function-এর চারপাশে thin wrapper — কোনো
    নতুন behavior নয়, শুধু class-based API surface যাতে callers/test contract
    match করে।

    Usage::

        limiter = APIKeyLimiter(max_requests=120)
        await limiter.enforce(api_key_hash)
    """

    def __init__(self, max_requests: int = DEFAULT_MAX_REQUESTS_PER_MINUTE) -> None:
        self.max_requests = max_requests

    async def enforce(self, api_key_hash: str) -> None:
        """Enforce the per-key rate limit (delegates to module-level function)."""
        await enforce_api_key_rate_limit(api_key_hash, max_requests=self.max_requests)

    # Allow `APIKeyLimiter(...)(api_key_hash)` shorthand too.
    async def __call__(self, api_key_hash: str) -> None:
        await self.enforce(api_key_hash)


# Module-level convenience singleton (default 60 req/min ceiling).
api_key_limiter = APIKeyLimiter()
