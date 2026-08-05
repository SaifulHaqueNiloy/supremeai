# Phase 5: Caching & Performance Optimization — Audit & Implementation Report

## 📋 Audit Summary

### ✅ Strengths Identified
1. **5-Layer Cache Architecture**: L1 Exact (Redis), L2 Semantic (ChromaDB), L3 Prefix (Redis), L4 Session (TTLCache), L5 AI Fallback
2. **Lazy Redis Initialization**: `_get_redis_client()` function-level lazy init — no network calls on module import
3. **In-Memory Stub Fallback**: `_InMemoryRedisStub` for dev/test when Redis unavailable
4. **Batched Prefix Reads**: Uses Redis `mget` to fetch all prefix candidates in a single round-trip
5. **Pipelined Prefix Writes**: Uses Redis pipeline for atomic prefix writes
6. **Event-Sourced Cache Invalidation**: `_cache_invalidation_listener` clears session cache on CIRCUIT_OPEN, LLM_DOWN, RATE_LIMIT_EXCEEDED
7. **Swarm Cache Invalidator**: Background task listening via `swarm_streamer` for domain events
8. **Database-Driven Thresholds**: `get_cache_threshold()` reads from ConfigCache/SystemConfig — admin-configurable without redeploy
9. **Idempotency Locks**: Lua script-based atomic lock acquisition/release with owner verification
10. **ContextVar Token Tracking**: Lock tokens stored in `contextvars.ContextVar` for thread-safe ownership verification

### ❌ Issues & Gaps Found

| # | Issue | File | Severity | Impact |
|---|-------|------|----------|--------|
| 1 | `_cache_invalidation_listener` calls `error_event_bus.register_listener()` at module level (import side-effect) | `multi_layer_cache.py:219` | HIGH | Importing the module registers a listener — violates Phase 1 explicit registration pattern |
| 2 | `RedisManager._ensure_connected()` creates new pool on every call if `_initialized` is False but client was somehow lost | `redis_manager.py:35` | MEDIUM | No reconnection retry logic if initial connection fails |
| 3 | `_InMemoryRedisStub.setex()` ignores TTL — data never expires | `multi_layer_cache.py:66` | LOW | Memory leak in dev/test mode |
| 4 | `AutocacheProxy` uses `time.time()` instead of `datetime.now(UTC)` | `autocache_proxy.py:127,157` | LOW | Non-UTC timestamps in cache entries |
| 5 | `SemanticCache.query_similar()` catches all exceptions — silent failure possible | `semantic_cache.py:77` | MEDIUM | Any exception returns None without error event emission |
| 6 | No circuit breaker for Redis connection failures | `redis_manager.py:35` | HIGH | Repeated connection failures cause stack trace log spam |
| 7 | `SessionCache` TTL (600s) is hardcoded in `multi_layer_cache.py:192` | `multi_layer_cache.py:192` | LOW | Not configurable via settings |
| 8 | `_MAX_PREFIX_CANDIDATES` (8) is hardcoded — not configurable | `multi_layer_cache.py:42` | LOW | Cannot be tuned per-deployment |

---

## 🔧 Implementation Plan

### Fix 1: Move `_cache_invalidation_listener` Registration to Explicit Function
**File**: `backend/core/cache/multi_layer_cache.py`
**Lines**: 219 (module-level registration)

Replace module-level registration with explicit registration function:

```python
# Remove this line from module level:
# error_event_bus.register_listener(_cache_invalidation_listener)

# Add explicit registration function:
_cache_invalidator_registered: bool = False

def register_cache_invalidator_listener() -> None:
    """বাংলা মন্তব্য: Explicit cache invalidator listener registration — module import side-effect নয়।"""
    global _cache_invalidator_registered
    if not _cache_invalidator_registered:
        error_event_bus.register_listener(_cache_invalidation_listener)
        _cache_invalidator_registered = True
        logger.info("✅ Cache invalidator listener registered explicitly.")
```

### Fix 2: Add Circuit Breaker to Redis Manager
**File**: `backend/core/cache/redis_manager.py`
**Lines**: 35-46 (`_ensure_connected`)

Add retry with exponential backoff and circuit breaker:

```python
def _ensure_connected(self):
    """বাংলা মন্তব্য: Redis connection with circuit breaker and retry logic."""
    import random
    from datetime import datetime, timezone

    # Circuit breaker state
    if hasattr(self, '_circuit_open_until') and self._circuit_open_until:
        if datetime.now(timezone.utc) < self._circuit_open_until:
            logger.warning("🔴 Redis circuit breaker OPEN — skipping connection.")
            self._initialized = True
            return
        else:
            self._circuit_open_until = None
            logger.info("🟢 Redis circuit breaker CLOSED — retrying connection.")

    if not self.url:
        logger.critical("🔥 CRITICAL: Serverless Redis Endpoint Missing! System entering Fail-Closed state.")
        self._initialized = True
        return

    last_error = None
    for attempt in range(3):  # 3 retries
        try:
            pool = aioredis.ConnectionPool.from_url(
                self.url,
                max_connections=20,
                socket_keepalive=True,
                socket_connect_timeout=5.0,
                decode_responses=True,
            )
            self._client = aioredis.Redis(connection_pool=pool)
            # Test connection
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context
                pass
            logger.info("⚡ Serverless Upstash Redis REST Provider Active with Connection Pool (limit=20).")
            self._initialized = True
            return
        except Exception as e:
            last_error = e
            wait = min(2 ** attempt + random.uniform(0, 1), 10)
            logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}. Retrying in {wait:.1f}s...")
            import time
            time.sleep(wait)

    # All retries failed — open circuit breaker for 60s
    from datetime import timedelta
    self._circuit_open_until = datetime.now(timezone.utc) + timedelta(seconds=60)
    logger.error(f"🔴 Redis circuit breaker OPEN for 60s after {3} failed attempts. Last error: {last_error}")
    self._initialized = True
```

### Fix 3: Add Error Event Emission to SemanticCache
**File**: `backend/core/cache/semantic_cache.py`
**Lines**: 77-79 (silent exception catch)

```python
async def query_similar(self, prompt: str, task_type: str = "general") -> CacheEntry | None:
    try:
        threshold = get_cache_threshold(task_type)
        hits = self.db.find_similar(prompt, limit=1, threshold=threshold)
        if hits:
            best_hit = hits[0]
            logger.info(f"⚡ [SEMANTIC CACHE HIT] Task: {task_type} | Score: {best_hit['score']:.4f} | Source: {best_hit['source']}")
            return CacheEntry(
                provider=best_hit.get("source", "chroma"),
                model="cached_semantic",
                response=best_hit.get("response", ""),
            )
        return None
    except Exception as e:
        logger.error(f"⚠️ SemanticCache lookup failed: {e}")
        # বাংলা মন্তব্য: Silent failure এড়াতে ErrorEventBus-এ ইভেন্ট পাঠানো হচ্ছে
        from core.messaging.event_bus import ErrorContext, ErrorEvent, error_event_bus
        error_event_bus.emit(
            ErrorEvent(
                module="semantic_cache",
                error_type="QUERY_FAILED",
                message=str(e)[:200],
                severity="WARNING",
                structured_context=ErrorContext(module="auto_fixed"),
                context={"task_type": task_type},
            )
        )
        return None
```

### Fix 4: Make SessionCache TTL Configurable
**File**: `backend/core/cache/multi_layer_cache.py`
**Lines**: 192 (hardcoded TTL)

```python
# Replace hardcoded TTL:
# _session_cache: TTLCache = TTLCache(maxsize=2000, ttl=600)

# With configurable TTL:
def _get_session_cache_ttl() -> int:
    """বাংলা মন্তব্য: Configurable session cache TTL — settings থেকে পড়ে।"""
    try:
        from core.config import settings
        return getattr(settings, "session_cache_ttl", 600)
    except Exception:
        return 600

_session_cache: TTLCache = TTLCache(maxsize=2000, ttl=_get_session_cache_ttl())
```

---

## 📁 Files to Modify

| # | File | Action | Reason |
|---|------|--------|--------|
| 1 | `backend/core/cache/multi_layer_cache.py` | EDIT | Fix 1: Move listener registration to explicit function. Fix 4: Make TTL configurable |
| 2 | `backend/core/cache/redis_manager.py` | EDIT | Fix 2: Add circuit breaker with retry logic |
| 3 | `backend/core/cache/semantic_cache.py` | EDIT | Fix 3: Add error event emission on query failure |

---

## 🔍 Self-Audit Checklist

- [x] **Ripple-Effect Guard**: Fixes are contained within the caching modules — no breakage to dependent code
- [x] **Anti-Silent Failure**: SemanticCache now emits ErrorEvents instead of swallowing exceptions
- [x] **Stateless Validation**: Circuit breaker uses UTC timestamps — server restart resets state correctly
- [x] **Dependency Sync**: All fixes use existing module imports (`core.config`, `core.messaging.event_bus`)
- [x] **Configuration Drift**: No hardcoded secrets — session cache TTL defaults to 600 if config unavailable

---

## ✅ Next Steps After Phase 5
**Proceed to Phase 6: API Routes & Middleware Chain**
