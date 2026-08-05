# Phase 2: Security & Authentication Layer — Audit & Implementation Plan

## 📋 Audit Summary

### ✅ Strengths Identified
1. **Fail-Closed JWT Auth**: `auth_middleware.py` properly rejects invalid/expired tokens
2. **Constant-Time API Key Comparison**: `hmac.compare_digest` used correctly
3. **Crypto-Secure Key Generation**: `secrets.token_urlsafe` for API keys
4. **Fernet Key Rotation**: `RotatingFernet` supports multiple encryption keys
5. **JIT OTP Anti-Hacking**: Context-aware middleware with IP/country/fingerprint checks
6. **Lazy Secret Vault**: `get_secret_vault()` singleton with TTL caching
7. **Comprehensive Middleware Chain**: Auth → API Key → Honeypot → AutoNoGuard → GZip

### ❌ Issues & Gaps Found

| # | Issue | File | Severity | Impact |
|---|-------|------|----------|--------|
| 1 | No JWT refresh/revocation mechanism | `core/security/__init__.py` | HIGH | Tokens valid for 60min with no way to revoke |
| 2 | API Key expiration not enforced on validation | `core/security/__init__.py` | HIGH | Revoked keys silently accepted |
| 3 | Hardcoded config values (TTL, cooldown) | `middleware/anti_hacking.py` | MEDIUM | Not env-configurable |
| 4 | Enforce mode off by default | `middleware/anti_hacking.py` | MEDIUM | Anti-hacking is alert-only |
| 5 | Tenant rate limiter uses undefined method | `middleware/tenant_rate_limiter.py` | HIGH | Will crash at runtime |
| 6 | No centralized audit event logging | All security files | MEDIUM | Security events not persisted |
| 7 | InfisicalClient type hint None assignment | `core/security/secret_vault.py` | LOW | Linter errors only |
| 8 | Secret vault backward compat creates new instance | `core/security/secret_vault.py` | LOW | Minor perf overhead |
| 9 | CORS origins not shown in health/audit | `backend/core/config.py` | MEDIUM | No visibility |
| 10 | No per-key rate limiting | `middleware/tenant_rate_limiter.py` | MEDIUM | Can't throttle single abusive key |

---

## 🔧 Implementation Plan

### Fix 1: Add JWT Token Blacklist & Refresh Mechanism
**File**: `backend/core/security/__init__.py`
**Lines**: After `verify_token()` function (~line 80)

```python
# Add Redis-backed token blacklist
from core.cache.redis_manager import redis_manager

BLACKLIST_PREFIX = "jwt:blacklist:"
BLACKLIST_TTL = 86400  # 24 hours (max token age)

async def revoke_token(jti: str, exp: int) -> None:
    """Revoke a JWT by its JWT ID (jti claim).
    Expired tokens are auto-cleaned by Redis TTL.
    """
    if redis_manager and redis_manager.client:
        ttl = max(1, exp - int(time.time()))
        await redis_manager.client.setex(f"{BLACKLIST_PREFIX}{jti}", min(ttl, BLACKLIST_TTL), "revoked")

async def is_token_revoked(jti: str) -> bool:
    """Check if a token has been revoked."""
    if not redis_manager or not redis_manager.client:
        return False  # Degrade gracefully if Redis is down
    return await redis_manager.client.exists(f"{BLACKLIST_PREFIX}{jti}") > 0
```

**Update `verify_token()`** to check blacklist after JWT decode.

### Fix 2: Enforce API Key Expiration in Validation
**File**: `backend/core/security/__init__.py`
**Lines**: Add `verify_api_key_with_expiry()` near `verify_api_key()` (~line 110)

```python
async def verify_api_key_with_expiry(plain_key: str, stored_hash: str, expires_at: int | None) -> bool:
    """Verify API key hash AND check expiration."""
    if expires_at is not None and time.time() > expires_at:
        logger.warning("API key has expired")
        return False
    return verify_api_key(plain_key, stored_hash)
```

### Fix 3: Make Anti-Hacking Config Env-Driven
**File**: `backend/middleware/anti_hacking.py`
**Lines**: Replace hardcoded constants at top

```python
from core.config import settings

_CONTEXT_TTL = int(os.getenv("SECURITY_CONTEXT_TTL", "86400"))
_OTP_COOLDOWN_PREFIX = "security:otp_cooldown:"
_OTP_COOLDOWN_SECONDS = settings.otp_cooldown_seconds
_CAUTION_LOG_PREFIX = "security:caution_log:"
_CAUTION_LOG_TTL = int(os.getenv("SECURITY_CAUTION_LOG_TTL", "86400"))
```

### Fix 4: Fix Tenant Rate Limiter Method
**File**: `backend/middleware/tenant_rate_limiter.py`
**Lines**: Replace `redis_mgr.get_cache()` with proper Redis methods

```python
async def enforce_tenant_rate_limit(request: Request):
    tenant_id = request.headers.get("x-tenant-id", "anonymous_pool")
    
    from core.cache.redis_manager import redis_manager
    
    if not redis_manager or not redis_manager.client:
        logger.warning("⚠️ Redis manager unavailable. Bypassing rate limiter.")
        return

    cache_key = f"rate_limit:{tenant_id}"
    
    # Use INCR with expiry atomic operation
    pipe = redis_manager.client.pipeline()
    pipe.incr(cache_key)
    pipe.expire(cache_key, 60)
    results = await pipe.execute()
    current_hits = results[0]
    
    if current_hits > 100:  # Max 100 requests per minute
        logger.warning(f"🚨 Rate limit exceeded for tenant: {tenant_id} ({current_hits} hits)")
        raise HTTPException(status_code=429, detail="Too Many Requests")
```

### Fix 5: Centralized Security Audit Logging
**New File**: `backend/core/security/audit_logger.py`

```python
"""Centralized security audit logging with structured context.
All security events (login, token issue, API key use, context mismatch)
are logged with trace IDs and stored in Redis + logs.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from core.cache.redis_manager import redis_manager

AUDIT_PREFIX = "audit:event:"
AUDIT_LIST_PREFIX = "audit:recent:"
MAX_RECENT_EVENTS = 1000

async def log_security_event(
    event_type: str,
    user_id: str | None,
    details: dict[str, Any],
    severity: str = "INFO",
) -> str:
    """Log a security event with unique trace ID."""
    event_id = f"sec-{uuid.uuid4().hex[:12]}"
    event = {
        "event_id": event_id,
        "event_type": event_type,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "details": details,
    }
    
    # Always log to structured logger
    logger.bind(event_type=event_type, severity=severity).info(f"Security event: {event_type}", extra=event)
    
    # Persist to Redis if available
    if redis_manager and redis_manager.client:
        try:
            await redis_manager.client.setex(
                f"{AUDIT_PREFIX}{event_id}",
                86400 * 30,  # 30 day retention
                json.dumps(event, default=str),
            )
            await redis_manager.client.lpush(
                AUDIT_LIST_PREFIX,
                json.dumps({"event_id": event_id, "event_type": event_type, "timestamp": event["timestamp"]}, default=str),
            )
            await redis_manager.client.ltrim(AUDIT_LIST_PREFIX, 0, MAX_RECENT_EVENTS - 1)
        except Exception as e:
            logger.warning(f"Failed to persist audit event {event_id}: {e}")
    
    return event_id
```

### Fix 6: Add Per-API-Key Rate Limiting
**New File**: `backend/core/security/api_key_limiter.py`

```python
import time
from typing import Callable

from fastapi import HTTPException, Request
from loguru import logger

from core.cache.redis_manager import redis_manager

API_KEY_LIMIT_PREFIX = "apikey:rate:"
MAX_REQUESTS_PER_MINUTE = 60

async def enforce_api_key_rate_limit(api_key_hash: str) -> None:
    """Per-API-key rate limiting using sliding window counter."""
    if not redis_manager or not redis_manager.client:
        return  # Degrade gracefully
    
    cache_key = f"{API_KEY_LIMIT_PREFIX}{api_key_hash}"
    current_minute = int(time.time() / 60)
    window_key = f"{cache_key}:{current_minute}"
    
    pipe = redis_manager.client.pipeline()
    pipe.incr(window_key)
    pipe.expire(window_key, 120)  # 2 minute window safety
    results = await pipe.execute()
    current_count = results[0]
    
    if current_count > MAX_REQUESTS_PER_MINUTE:
        logger.warning(f"API key rate limit exceeded: {api_key_hash[:8]}... ({current_count} requests)")
        raise HTTPException(status_code=429, detail="API key rate limit exceeded")
```

---

## 📁 Files to Modify

| # | File | Action | Lines | Reason |
|---|------|--------|-------|--------|
| 1 | `backend/core/security/__init__.py` | EDIT | After line 80 | Add JWT blacklist functions |
| 2 | `backend/core/security/__init__.py` | EDIT | After line 110 | Add API key expiry validation |
| 3 | `backend/middleware/anti_hacking.py` | EDIT | Top constants | Make config env-driven |
| 4 | `backend/middleware/tenant_rate_limiter.py` | REWRITE | Entire file | Fix undefined methods |
| 5 | `backend/core/security/audit_logger.py` | CREATE | New file | Centralized audit logging |
| 6 | `backend/core/security/api_key_limiter.py` | CREATE | New file | Per-key rate limiting |
| 7 | `backend/core/config.py` | EDIT | Settings class | Add security config vars |
| 8 | `backend/core/app_builder.py` | EDIT | Health endpoint | Expose CORS origins in health |

---

## 🔍 Self-Audit Checklist

- [ ] **Ripple-Effect Guard**: JWT blacklist addition won't break existing auth flow; blacklist check is additive
- [ ] **Anti-Silent Failure**: Audit logging always logs to logger; Redis failure is caught and warned
- [ ] **Stateless Validation**: All security checks are stateless; JWT blacklist uses Redis (externalized state)
- [ ] **Dependency Sync**: New files only import from existing modules (`redis_manager`, `config`, `logger`)
- [ ] **Configuration Drift**: Hardcoded values replaced with env-var driven config; no secrets hardcoded

---

## 📝 Next Steps After Phase 2
Transition to Phase 3: LLM Gateway & AI Orchestration
