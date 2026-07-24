# Phase 1 Audit Report: Security & Authentication 🔴 Critical

> **Audit Date:** 2025-01-XX
> **Auditor:** Principal Autonomous AI Architect
> **Status:** Issues Identified — Fixes Ready

---

## 1.1 JWT Secret Persistence (CRITICAL)

### File: `backend/core/config.py` (Line ~340)

**Issue:** `jwt_secret` property uses `secrets.token_hex(64)` as fallback when no secret is provided. This generates a **new random secret on every server restart**, invalidating all existing JWTs. Users will be logged out on every deploy.

```python
# Current code (problematic):
v = v or secrets.token_hex(64)  # New random secret every restart!
```

**Impact:**
- All JWT tokens invalidated on every server restart
- Users forced to re-authenticate after every deploy
- Session continuity broken

**Fix:** Implement persistent JWT secret with file-based cache:

```python
@property
def jwt_secret(self) -> str:
    v = self._get_cached_secret("SUPREMEAI_JWT_SECRET")
    if not v:
        v = self._load_or_generate_jwt_secret()
    if len(v) < 64 and "pytest" not in sys.modules:
        raise ValueError("JWT secret must be >= 64 bytes entropy in all environments.")
    return v

def _load_or_generate_jwt_secret(self) -> str:
    """Load from file or generate and persist for container restarts."""
    secret_file = "/etc/secrets/jwt_secret"
    if os.path.exists(secret_file):
        with open(secret_file) as f:
            return f.read().strip()
    new_secret = secrets.token_hex(64)
    try:
        os.makedirs(os.path.dirname(secret_file), exist_ok=True)
        with open(secret_file, "w") as f:
            f.write(new_secret)
    except OSError:
        logger.warning("Could not persist JWT secret to file — using in-memory only")
    return new_secret
```

**Pro Tip:** For production, always set `SUPREMEAI_JWT_SECRET` via Infisical or Render env vars. The file fallback is only for local development.

---

## 1.2 CORS Auto-Population (HIGH)

### File: `backend/core/config.py` (Line ~400)

**Issue:** `cors_origins` defaults to empty list `[]`. In production, if `CORS_ORIGINS` env var is not set, the validator removes localhost entries and then raises `ValueError` because the list is empty. This causes a **startup crash**.

```python
# Current code:
v = [o for o in v if "localhost" not in o and "127.0.0.1" not in o]
if not v:
    raise ValueError(f"{env.capitalize()} requires at least one non-localhost CORS origin.")
```

**Impact:**
- Production deployment fails if `CORS_ORIGINS` not explicitly set
- No graceful fallback to known deployment URLs

**Fix:** Auto-populate from known deployment targets:

```python
@field_validator("cors_origins", mode="after")
@classmethod
def validate_cors_origins(cls, v: list[str], info: ValidationInfo) -> list[str]:
    env = str(info.data.get("env", "local") or "local").lower()
    if env == "test":
        return v
    if env in {"production", "staging"}:
        v = [o for o in v if "localhost" not in o and "127.0.0.1" not in o]
        if not v:
            v = [
                "https://supremeai-studio-client.onrender.com",
                "https://supremeai-studio-client-qb34.onrender.com",
                "https://supremeai-admin.web.app",
                "https://supremeai-lac.vercel.app",
            ]
            logger.warning(f"Auto-populated CORS origins: {v}")
    return v
```

**Pro Tip:** Same fix should be applied to `user_cors_origins` and `admin_cors_origins` validators in `core/app_user.py` and `core/app_admin.py`.

---

## 1.3 Middleware Chain Order (HIGH)

### File: `backend/core/app_builder.py` (Line ~200)

**Issue:** Middleware registration order has security vulnerabilities:

```
Current Order:                    Correct Order:
1. RequestContextMiddleware       1. RequestContextMiddleware
2. SupremeContextMiddleware       2. GZipMiddleware (decode body early)
3. RequestIdMiddleware            3. RequestIdMiddleware
4. TenantExtractionMiddleware     4. TrustedOriginMiddleware
5. TrustedOriginMiddleware        5. SupremeContextMiddleware
6. ChaosInjectorMiddleware  ← X  6. TenantExtractionMiddleware
7. ObservabilityMiddleware        7. ObservabilityMiddleware
8. HoneypotMiddleware       ← X  8. AuthMiddleware (AUTH FIRST)
9. AuthMiddleware                 9. APIKeyAuthMiddleware
10. APIKeyAuthMiddleware          10. AutonoGuardMiddleware
11. IdempotencyMiddleware         11. HoneypotMiddleware (now authenticated)
12. ResponseStandardizationMdw    12. ChaosInjectorMiddleware (now authenticated)
13. AutonoGuardMiddleware         13. IdempotencyMiddleware
14. GZipMiddleware          ← X  14. ResponseStandardizationMiddleware
```

**Issues:**
1. `ChaosInjectorMiddleware` runs BEFORE auth — unauthenticated users can inject chaos
2. `HoneypotMiddleware` runs BEFORE auth — useless on unauthenticated requests
3. `AutonoGuardMiddleware` runs AFTER `ResponseStandardizationMiddleware` — OTP responses not standardized
4. `GZipMiddleware` runs LAST — should be early to decode compressed request bodies

**Fix:** Reorder middleware:

```python
# Corrected order in build_app_shell():
fastapi_app.add_middleware(RequestContextMiddleware)       # 1 - Always first
fastapi_app.add_middleware(GZipMiddleware, minimum_size=1000)  # 2 - Decode body early
fastapi_app.add_middleware(RequestIdMiddleware)            # 3
fastapi_app.add_middleware(TrustedOriginMiddleware)        # 4
fastapi_app.add_middleware(SupremeContextMiddleware)       # 5
fastapi_app.add_middleware(TenantExtractionMiddleware)     # 6
fastapi_app.add_middleware(ObservabilityMiddleware)        # 7
fastapi_app.add_middleware(AuthMiddleware)                 # 8 - AUTH FIRST
fastapi_app.add_middleware(APIKeyAuthMiddleware)           # 9
fastapi_app.add_middleware(AutonoGuardMiddleware)          # 10 - Security BEFORE internals
fastapi_app.add_middleware(HoneypotMiddleware)             # 11 - Now authenticated
fastapi_app.add_middleware(ChaosInjectorMiddleware)        # 12 - Now authenticated
fastapi_app.add_middleware(IdempotencyMiddleware)          # 13
fastapi_app.add_middleware(ResponseStandardizationMiddleware)  # 14 - Last
```

**Pro Tip:** Middleware order is critical for security. Always place auth middleware before any middleware that could leak information or be exploited.

---

## 1.4 Secret Vault Fallback Inconsistency (HIGH)

### File: `backend/core/security/secret_vault.py` (Line ~130)

**Issue:** `_fallback_to_env()` has inconsistent behavior across environments:

```python
# Current code:
if self.env in ("test", "testing", "ci", "local"):
    env_fallback = f"mock_{secret_id}"  # Mock in test
else:
    env_fallback = ""  # Empty string in production! CRITICAL!
```

**Impact:**
- Production returns empty string `""` for missing secrets
- Empty API keys could crash downstream services (OpenAI, Gemini, etc.)
- No alerting when critical secrets are missing

**Fix:** Add critical secret validation and alerting:

```python
def _fallback_to_env(self, secret_id: str, default: str | None) -> str:
    env_fallback = os.getenv(secret_id, default)
    if env_fallback is None:
        if self.env in ("production", "staging"):
            logger.critical(f"🚨 CRITICAL: Secret '{secret_id}' missing in {self.env}!")
            # Emit alert via error_event_bus
            try:
                error_event_bus.emit(ErrorEvent(
                    module="secret_vault",
                    error_type="CRITICAL_SECRET_MISSING",
                    message=f"Secret '{secret_id}' not found in Infisical or env!",
                    severity="CRITICAL",
                ))
            except Exception:
                pass
            # Fail-closed for critical secrets
            critical_secrets = {
                "SUPREMEAI_JWT_SECRET", "SUPREMEAI_ADMIN_PASSWORD_HASH",
                "REDIS_URL", "SUPABASE_DATABASE_URL_POOLER"
            }
            if secret_id in critical_secrets:
                raise RuntimeError(
                    f"CRITICAL: Secret '{secret_id}' not found in {self.env}! Fail-closed."
                )
            env_fallback = ""  # Non-critical secrets can be empty
        else:
            logger.warning(f"Mocking missing secret '{secret_id}' for {self.env}.")
            env_fallback = f"mock_{secret_id}"
    self._cache[secret_id] = _CacheEntry(env_fallback)
    return env_fallback
```

**Pro Tip:** Define `CRITICAL_SECRETS` as a class constant or in settings. This makes it easy to audit which secrets are considered critical.

---

## 1.5 API Key Middleware Performance (MEDIUM)

### File: `backend/core/security/api_key_middleware.py` (Line ~50)

**Issue:** Every API request with `x-api-key` header triggers a database query. No Redis caching.

```python
# Current code:
row = await pool.fetchrow(
    "SELECT id, key_hash, revoked, rate_limit_rps, expires_at FROM api_keys WHERE key_hash = $1 LIMIT 1",
    key_hash,
)
```

**Impact:**
- DB query on EVERY request with API key
- No caching — high latency for repeated API key checks
- DB connection pool exhaustion under high load

**Fix:** Add Redis caching layer:

```python
async def _get_cached_api_key(self, key_hash: str) -> dict | None:
    """Get API key from Redis cache or DB."""
    from core.cache.redis_manager import redis_manager

    cache_key = f"apikey:{key_hash}"
    cached = await redis_manager.get_cache(cache_key)
    if cached:
        return json.loads(cached)

    pool = await get_db_pool()
    row = await pool.fetchrow(
        "SELECT id, key_hash, revoked, rate_limit_rps, expires_at FROM api_keys WHERE key_hash = $1 LIMIT 1",
        key_hash,
    )
    if row:
        await redis_manager.set_cache(
            cache_key,
            json.dumps(dict(row)),
            ex_seconds=300  # 5 min cache
        )
    return dict(row) if row else None
```

**Pro Tip:** Use `ex_seconds=300` (5 min) for API key cache. This balances freshness with performance. For revoked keys, you can set a shorter TTL or use Redis pub/sub for instant invalidation.

---

## 1.6 AutonoGuard Circuit Breaker Duplication (MEDIUM)

### File: `backend/core/autonoguard_engine.py` (Line ~30)

**Issue:** Two different circuit breaker implementations exist:
1. `core/autonoguard_engine.py` uses `from core.resilience.circuit_breaker import CircuitBreaker`
2. `core/cache/redis_manager.py` uses `from pybreaker import CircuitBreaker`

```python
# autonoguard_engine.py:
from core.resilience.circuit_breaker import CircuitBreaker

# redis_manager.py:
from pybreaker import CircuitBreaker
```

**Impact:**
- Different APIs (`allow_request()` vs `call()`)
- Different failure thresholds and recovery timeouts
- Maintenance burden — two implementations to maintain

**Fix:** Standardize on `pybreaker` (battle-tested, fewer bugs):

```python
# autonoguard_engine.py — Migrate to pybreaker
from pybreaker import CircuitBreaker as PyCircuitBreaker

class AutonoGuardEngine:
    _circuit_breaker: PyCircuitBreaker = PyCircuitBreaker(
        fail_max=5,
        reset_timeout=60.0,
        name="autonoguard",
    )

    async def heal_error(self, exc, context):
        try:
            return self._circuit_breaker.call(lambda: self._do_heal(exc, context))
        except CircuitBreakerError:
            logger.warning("Circuit breaker open — skipping error remediation")
            return None
```

**Pro Tip:** If you prefer the custom implementation for lighter weight, migrate `redis_manager.py` to use it instead. The key is consistency — pick ONE and use it everywhere.

---

## 1.7 Rate Limiter Fail-Open (MEDIUM)

### File: `backend/core/app_builder.py` (Line ~100)

**Issue:** Native Redis rate limiter uses `fail-open` when Redis is unavailable:

```python
# Current code:
if not redis_manager.client:
    logger.warning("Rate limit check skipped — Redis unavailable (fail-open)")
    return True  # FAIL-OPEN: allows all requests!
```

**Impact:**
- When Redis is down, rate limiting is completely disabled
- Attackers can flood the API without restriction
- Violates Malware Immunity (DNA #5)

**Fix:** Change to `fail-closed`:

```python
if not redis_manager.client:
    logger.warning("Rate limit check failed — Redis unavailable (fail-closed)")
    return False  # FAIL-CLOSED: blocks all requests
```

**Pro Tip:** For production, consider a hybrid approach: fail-closed for authenticated endpoints, fail-open for public endpoints. This balances security with availability.

---

## 1.8 IP Churn Detection Using Redis Hashes (LOW)

### File: `backend/core/autonoguard_engine.py` (Line ~100)

**Issue:** IP churn detection uses Redis hashes with `first_seen` as a hash field, causing type confusion:

```python
# Current code:
raw_ips = await redis_manager.client.hgetall(key)
if isinstance(raw_ips, dict):
    ips = list(raw_ips.keys())
    first_seen = float(raw_ips.get("first_seen", time.time()))
```

**Impact:**
- `first_seen` is stored as a hash field alongside IP addresses
- Type confusion between IP keys and metadata keys
- Inaccurate churn detection

**Fix:** Use Redis sorted sets for proper IP tracking:

```python
async def detect_ip_churn(self, admin_id: str, current_ip: str) -> ChurnDetection:
    key = f"{_ip_churn_prefix}{admin_id}"
    now = time.time()

    # Use sorted set with timestamp as score
    await redis_manager.client.zadd(key, {current_ip: now})
    # Remove entries older than 1 hour
    await redis_manager.client.zremrangebyscore(key, 0, now - 3600)
    await redis_manager.client.expire(key, 3600)

    # Count unique IPs in last hour
    ip_count = await redis_manager.client.zcard(key)
    is_churn = ip_count > 5

    return ChurnDetection(
        is_churn=is_churn,
        previous_ips=await redis_manager.client.zrange(key, 0, -1),
        first_seen=now,
        churn_count=ip_count,
    )
```

**Pro Tip:** Redis sorted sets are perfect for time-series data like IP tracking. The score (timestamp) enables efficient range queries and automatic expiry.

---

## 1.9 Settings Validator Duplication (MEDIUM)

### File: `backend/core/config.py` (Lines ~450-550)

**Issue:** Four separate `@model_validator(mode="after")` methods with overlapping concerns:

1. `validate_docs_auth` — docs password fallback
2. `validate_stripe_completeness` — Stripe mock mode
3. `validate_production_completeness` — production degraded mode
4. `validate_completeness` — general resilience guard

**Impact:**
- Execution order of `mode="after"` validators is not guaranteed
- `validate_completeness` runs in ALL envs, duplicating production checks
- `validate_stripe_completeness` returns `self` without action — dead code

**Fix:** Consolidate into a single validator:

```python
@model_validator(mode="after")
def validate_all(self):
    """Consolidated validation for all environments."""
    if self.env == "test":
        return self

    # Docs auth
    if self.env in {"production", "staging"} and self.docs_auth_enabled:
        pwd = self.docs_password.get_secret_value() if self.docs_password else ""
        if not pwd:
            self.docs_password = SecretStr("supreme-admin-2026-prod")

    # Production checks (degraded mode allowed)
    if self.env == "production":
        missing = []
        if not self.openrouter_api_key: missing.append("OPENROUTER_API_KEY")
        if not self.gemini_api_key: missing.append("GEMINI_API_KEY")
        if not self.ci_webhook_secret: missing.append("CI_WEBHOOK_SECRET")
        if missing:
            logger.warning(f"⚠️ Production missing: {', '.join(missing)}. Degraded mode.")

    # Stripe (non-blocking)
    if self.env in {"production", "staging"} and not self.stripe_api_key.get_secret_value():
        logger.warning("⚠️ Stripe API key missing. Billing in mock mode.")

    return self
```

**Pro Tip:** Always consolidate `model_validator` methods. Multiple validators with `mode="after"` have undefined execution order in Pydantic v2.

---

## 1.10 Auth Middleware Duplicate JWT Decode (LOW)

### File: `backend/core/security/auth_middleware.py` (Lines ~50, ~170)

**Issue:** JWT decode logic is duplicated between `_decode_jwt()` and `verify_admin_session_fail_closed()`:

```python
# _decode_jwt():
payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], options={"verify_exp": True})

# verify_admin_session_fail_closed():
payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], options={"verify_exp": True})
```

**Impact:**
- Code duplication — maintenance burden
- If one function is updated, the other may be forgotten
- Inconsistent error handling

**Fix:** Have `verify_admin_session_fail_closed()` call `_decode_jwt()`:

```python
async def verify_admin_session_fail_closed(request: Any) -> dict[str, Any]:
    from fastapi import HTTPException

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Malformed authorization header")

    token = auth_header[7:]
    payload = _decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    role = payload.get("role")
    if role not in ("admin", "master_admin"):
        raise HTTPException(status_code=401, detail="Not authorized")

    return payload
```

**Pro Tip:** DRY (Don't Repeat Yourself) is especially important for security-critical code. A bug in one copy could be a vulnerability.

---

## Summary of Phase 1 Issues

| ID | Issue | Severity | File | Line |
|----|-------|----------|------|------|
| 1.1 | JWT Secret Regeneration on Restart | 🔴 CRITICAL | `core/config.py` | ~340 |
| 1.2 | CORS Empty in Production Causes Crash | 🟡 HIGH | `core/config.py` | ~400 |
| 1.3 | Middleware Chain Order Vulnerabilities | 🟡 HIGH | `core/app_builder.py` | ~200 |
| 1.4 | Secret Vault Returns Empty String in Prod | 🟡 HIGH | `core/security/secret_vault.py` | ~130 |
| 1.5 | API Key Middleware No Redis Cache | 🟢 MEDIUM | `core/security/api_key_middleware.py` | ~50 |
| 1.6 | Duplicate Circuit Breaker Implementations | 🟢 MEDIUM | `autonoguard_engine.py` | ~30 |
| 1.7 | Rate Limiter Fail-Open When Redis Down | 🟢 MEDIUM | `core/app_builder.py` | ~100 |
| 1.8 | IP Churn Detection Type Confusion | 🔵 LOW | `autonoguard_engine.py` | ~100 |
| 1.9 | Settings Validator Duplication | 🟢 MEDIUM | `core/config.py` | ~450-550 |
| 1.10 | Auth Middleware Duplicate JWT Decode | 🔵 LOW | `core/security/auth_middleware.py` | ~50, ~170 |

---

## Next Steps

1. Apply all CRITICAL and HIGH priority fixes first
2. Run full test suite after each fix
3. Deploy to staging for validation
4. Proceed to Phase 2 (Infrastructure & Deployment)

---

*End of Phase 1 Audit Report*
