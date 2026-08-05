# SupremeAI 2.0 — Unified Troubleshooting Guide

> **Purpose:** Single source of truth for diagnosing and resolving operational issues.  
> **Scope:** Render/Vercel deployment, backend services, database, cache, and CI/CD failures.  
> **Last Updated:** 2026-07-25  
> **Status:** ACTIVE & PRODUCTION READY

---

## 📌 How to Use This Guide

1. **Identify the symptom** in the table of contents below.
2. **Follow the root cause analysis** to understand why it happens.
3. **Apply the permanent fix** from the implemented solutions section.
4. **Verify** using the provided health check commands.

---

## 🚨 Common Deployment Failures (Render/Vercel)

### 1. Render OOM Crashes & Container Restarts

**Symptom:**
- Render dashboard shows container restarting repeatedly.
- Health endpoint returns `502 Bad Gateway` or connection timeout.
- Logs show `OOMKilled` or `MemoryLimitExceeded`.

**Root Cause:**
- Free-tier Render containers have 512MB RAM limit.
- Backend spawns multiple async workers or loads large ML models exceeding memory.
- No memory monitoring or graceful degradation configured.

**Permanent Fix:**
```python
# In backend/core/config.py or Dockerfile
ENV PYTHONMALLOC=malloc
ENV MALLOC_ARENA_MAX=2
```

```dockerfile
# In backend/Dockerfile - reduce memory footprint
RUN pip install --no-cache-dir -r requirements.txt
```

**Operational Workaround:**
```bash
# Check current memory usage
curl https://supremeai-backend.onrender.com/api/v1/health | jq '.memory'

# If OOM, scale down workers or enable lazy loading:
export WORKER_COUNT=1
export LAZY_LOAD_MODELS=true
```

**Prevention:**
- Monitor with: `watch -n 5 'curl -s https://supremeai-backend.onrender.com/api/v1/metrics | jq .memory_usage'`
- Set up Render alert for `restart_count > 3` in last 5 minutes.

---

### 2. Render 404 Service Discovery Failure

**Symptom:**
- CI/CD fails with `HTTP 404 Not Found` when triggering deploy.
- Error: `⚠️ Backup API deploy returned status: 404`

**Root Cause:**
- `RENDER_API_KEY` belongs to a different Render account/workspace than the target service.
- Service ID doesn't exist under the authenticated account.

**Implemented Fix:**
- `.github/scripts/verify-render-deploy.py` now auto-discovers correct service IDs.
- Admin backend uses webhook URL (`RENDER_DEPLOY_HOOK_URL_BACKUP`) instead of API key for reliability.

**Operational Steps:**
```bash
# Verify which services your API key can access:
python -c "import requests, os; r=requests.get('https://api.render.com/v1/services', headers={'Authorization':'Bearer '+os.getenv('RENDER_API_KEY')}); [print(s.get('service',s).get('id'), s.get('service',s).get('name')) for s in r.json()]"

# Update SERVICES dict in verify-render-deploy.py if needed.
```

**GitHub Secrets Required:**
| Secret | Purpose |
|--------|---------|
| `RENDER_API_KEY` | Primary backend deploy trigger |
| `RENDER_API_KEY_BACKUP` | Admin backend API trigger |
| `RENDER_DEPLOY_HOOK_URL_BACKUP` | ✅ Preferred admin deploy trigger |

---

### 3. CI False-Positive Pass — Admin Backend Never Deployed

**Symptom:**
- GitHub Actions shows `Admin Backend: SUCCESS / HEALTHY`.
- Render Dashboard shows admin service was **not** deployed (deploy timestamp predates CI run).

**Root Cause (3 chained bugs):**
1. `verify-render-deploy.py` remapped 404 to primary service, reporting false health.
2. Admin URL fallback checked primary backend for health.
3. `supreme-core-ci.yml` triggered admin deploy on primary service when 404 occurred.

**Permanent Fix (Commit `5412e0226a`):**
- 404 now fails admin verify immediately — no remap.
- No fallback URLs; only exact service URL is health-checked.
- CI exits with code 1 on admin 404 and shows actionable error.

**Verification:**
```bash
# Check latest deploy ID matches CI run:
curl -H "Authorization: Bearer $RENDER_API_KEY_BACKUP" \
  https://api.render.com/v1/services/srv-d9fg48bh523c73f63bb0/deploys | jq '.[0]'
```

---

### 4. CI Polling Sequential Timing False Positive

**Symptom:**
- Backend is actually `LIVE` and returning `200 OK`.
- CI still fails: `No new deploy record found within 3 minutes`.

**Root Cause:**
- Render free-tier builds take 4+ minutes.
- Primary service check starts before free-tier build finishes.
- 3-minute timeout expires before service becomes live.

**Permanent Fix:**
- **LIVE Status Bypass:** If service already `LIVE`, skip age check and do direct health check.
- **Extended Threshold:** Poll timeout increased from 3 → 10 minutes.

**Verification:**
```bash
python .github/scripts/verify-render-deploy.py
# Should complete within 10 minutes for free-tier.
```

---

### 5. CORS Preflight Block — Admin Portal Cannot Reach Backend

**Symptom:**
- Browser console: `403 Forbidden — Cross-Origin Request Blocked`.
- `https://supremeai-admin.web.app` API calls fail.

**Root Cause:**
- Browser sends HTTP `OPTIONS` Preflight before cross-origin requests.
- `TrustedOriginMiddleware` lacked `OPTIONS` handler for admin origin.

**Permanent Fix:**
```python
# backend/core/security/origin_validator.py
if request.method == "OPTIONS":
    if not origin or origin in allowed:
        headers = {
            "Access-Control-Allow-Origin": origin or "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        }
        return JSONResponse(status_code=200, content={"status": "ok"}, headers=headers)
```

**Firebase Hosting Rewrites Required:**
```json
// firebase.json
{
  "hosting": {
    "rewrites": [
      { "source": "/api/**", "destination": "https://supremeai-backend.onrender.com/api/**" },
      { "source": "/admin-api/**", "destination": "https://supremeai-admin.onrender.com/admin-api/**" },
      { "source": "/api/v1/**", "destination": "https://supremeai-admin.onrender.com/api/v1/**" }
    ]
  }
}
```

---

## 🛢️ Database & Cache Issues

### 6. Firestore Connection Pool Exhaustion

**Symptom:**
- Backend logs: `ResourceExhausted: Too many open connections`.
- Requests timeout after 30s with no response.
- Firestore quota dashboard shows connection limit reached.

**Root Cause:**
- Connection pool not sized appropriately for concurrent load.
- Connections not being released back to pool after requests.
- Free-tier Firestore has connection limits (typically 100-500).

**Permanent Fix:**
```python
# backend/core/pgbouncer_pool.py
# Singleton pattern with optimized settings
pool = await asyncpg.create_pool(
    dsn=settings.database_url,
    min_size=5,
    max_size=30,
    statement_cache_size=0,  # PgBouncer handles prepared statements
    command_timeout=30,
)
```

**Operational Mitigation:**
```bash
# 1. Check active connections
curl https://supremeai-backend.onrender.com/api/v1/metrics | jq '.database.active_connections'

# 2. If near limit, restart with pool reset:
curl -X POST "https://api.render.com/deploy/srv-d9d3n58js32c738n79k0?key=$RENDER_API_KEY"
```

**Prevention:**
- Monitor connection count: set alert at >80% of max.
- Implement connection release middleware to ensure cleanup on request end.

---

### 7. Qdrant Write Retries & Performance Degradation

**Symptom:**
- Error logs: `qdrant_client.exceptions.ResponseHandlingException: 429 Too Many Requests`.
- Search operations slow (>2s) or returning partial results.
- Vector search relevance dropping.

**Root Cause:**
- Burst writes exceed Qdrant free-tier rate limits.
- No exponential backoff or circuit breaker on Qdrant client.
- Batch operations not chunked.

**Permanent Fix:**
```python
# backend/core/resilience/circuit_breaker.py
# Circuit breaker for Qdrant operations
cb = DynamicCircuitBreaker(
    name="qdrant_write",
    failure_threshold=5,
    recovery_timeout=60,
)

async def qdrant_write_with_retry(operation, max_retries=3):
    async with cb:
        for attempt in range(max_retries):
            try:
                return await operation()
            except RateLimitError:
                await asyncio.sleep(2 ** attempt)
```

**Operational Mitigation:**
```bash
# 1. Check Qdrant health
curl https://supremeai-backend.onrender.com/api/v1/health | jq '.services.qdrant'

# 2. Flush cache if stale data:
curl -X POST "https://supremeai-backend.onrender.com/api/v1/admin/cache/flush" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 3. Monitor Qdrant metrics:
curl https://supremeai-backend.onrender.com/api/v1/metrics | jq '.qdrant'
```

**Prevention:**
- Batch writes in chunks of 50-100 vectors.
- Add 100ms delay between batches.
- Set up Render alert for `qdrant_error_rate > 0.1`.

---

## ⚙️ Backend Runtime Errors

### 8. Circuit Breaker Open — Cascading Failures

**Symptom:**
- All LLM API calls fail instantly with `CircuitBreakerOpen` error.
- Health check shows `circuit_breaker: open` for multiple services.
- Logs: `Circuit breaker 'llm_gateway' is open, failing fast`.

**Root Cause:**
- LLM provider (Gemini/OpenAI) experienced outage or rate limiting.
- Circuit breaker threshold exceeded (e.g., 5 failures in 60s).
- No automatic recovery or notifications configured.

**Permanent Fix:**
```python
# backend/core/resilience/circuit_breaker.py
# Circuit breaker auto-recovers after timeout
# Alerts via Telegram/Discord webhook on state change:
if self.state == CircuitState.OPEN:
    send_alert(f"Circuit breaker '{name}' opened due to {failure_reason}")
```

**Operational Recovery:**
```bash
# 1. Check circuit breaker status
curl https://supremeai-backend.onrender.com/api/v1/circuit-breakers | jq

# 2. Manual reset (if provider recovered):
curl -X POST "https://supremeai-backend.onrender.com/api/v1/admin/circuit-breaker/reset" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"name": "llm_gateway"}'

# 3. Verify with test request:
curl -X POST "https://supremeai-backend.onrender.com/api/v1/chat" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -d '{"prompt": "test"}'
```

---

### 9. Pydantic Validation Crash on Startup

**Symptom:**
- Container crashes on startup with `ValidationError`.
- Health check returns `502` or connection refused.
- Logs: `ValueError: <SECRET_a2a52488)`?

**Root Cause:**
- Secrets loaded from Infisical but Pydantic model expects them at import time.
- Lazy properties not used; static `Field(validation_alias=...)` fails when vault unavailable.

**Permanent Fix:**
```python
# backend/core/config.py
# Convert all secrets to lazy @property with Infisical-backed getter
@property
def <SECRET_c359aff0) -> str | None:
    val = self._get_cached_secret("SUPREMEAI_ADMIN_PASSWORD_HASH")
    if not val and "pytest" not in sys.modules and os.getenv("CI") != "true":
        raise ValueError("supremeai_admin_password_hash must be explicitly set.")
    return val
```

**Operational Fix:**
```bash
# 1. Ensure secrets are synced to Render environment:
python scripts/sync_all_platforms_env.py --apply

# 2. Verify secret is visible:
render env get SUPREMEAI_ADMIN_PASSWORD_HASH --service-id srv-d9d3n58js32c738n79k0

# 3. Restart service:
curl -X POST "https://api.render.com/deploy/srv-d9d3n58js32c738n79k0?key=$RENDER_API_KEY"
```

---

## 📊 Quick Operational Checklist

### When Service Is Down

```bash
# 1. Health check all endpoints:
curl https://supremeai-backend.onrender.com/api/v1/health
curl https://supremeai-admin.onrender.com/api/v1/health

# 2. Check Render service status:
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv-d9d3n58js32c738n79k0 | jq '.service.status'

# 3. Sync secrets if environment changed:
python scripts/sync_all_platforms_env.py --apply

# 4. Manual deploy trigger (last resort):
curl -X POST "https://api.render.com/deploy/srv-d9d3n58js32c738n79k0?key=$RENDER_API_KEY"
```

### When CI Fails

```bash
# 1. Re-run with debug:
gh run rerun <RUN_ID> --debug

# 2. Check specific step logs:
gh run view <RUN_ID> --log-failed

# 3. Verify secrets are set:
gh secret list

# 4. Test deploy script locally:
python .github/scripts/verify-render-deploy.py
```

---

## 📚 Reference Documentation

### Primary Sources
- **[docs/operations/FULLSTACK_ERROR_FIX_AND_TROUBLESHOOTING_GUIDE.md](docs/operations/FULLSTACK_ERROR_FIX_AND_TROUBLESHOOTING_GUIDE.md)** — Comprehensive error catalog with Bengali annotations.
- **[docs/operations/RENDER_DEPLOYMENT_TROUBLESHOOTING_GUIDE.md](docs/operations/RENDER_DEPLOYMENT_TROUBLESHOOTING_GUIDE.md)** — Render-specific deployment issues and account architecture.
- **[bug_prophet_report.md](bug_prophet_report.md)** — Automated code risk analysis (212 files scanned).

### Related Documentation
- **[docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)** — Environment setup and local development.
- **[docs/SUPREMEAI_MASTER_BLUEPRINT.md](docs/SUPREMEAI_MASTER_BLUEPRINT.md)** — System architecture and design decisions.
- **[PHASE0_AUDIT_REPORT.md](PHASE0_AUDIT_REPORT.md)** — Security hardening audit (July 2026).

---

## 🎯 BugProphet Risk Analysis Summary

**Total Files Scanned:** 212  
**Risk Distribution:** 8 Critical, 0 High, 113 Medium, 123 Low

### Top Risk Files (Action Required)

| File | Risk Score | Critical Issues | Recommended Action |
|------|-----------|-----------------|-------------------|
| `backend/tools/code/cot_reasoner.py` | 6.9/10 | 2 | Replace `__import__()` with safe AST-based imports. |
| `backend/tools/security_tools/multi_account_rotator.py` | 4.7/10 | 0 | Break down 146-line `perform_autonomous_signup` function. |
| `backend/tools/health_checker.py` | 3.9/10 | 1 | Replace `__import__()` with safe alternatives. |
| `backend/core/factual_verifier.py` | 3.7/10 | 1 | Replace `__import__()` with safe alternatives. |
| `backend/core/skill_manager.py` | 3.7/10 | 1 | Replace `exec()` with sandboxed execution or AST validation. |
| `backend/core/evolution/evolution_react_agent.py` | 3.7/10 | 1 | Replace `compile()` with safer AST transformations. |
| `backend/core/evolution/self_evolution_agent.py` | 3.7/10 | 1 | Replace `compile()` with safer AST transformations. |

**Note:** All CRITICAL findings (`BP003`) relate to dynamic code execution (`__import__`, `exec()`, `compile()`). These are high-risk for code injection attacks. See `docs/SECURITY.md` for secure coding standards.

**Full Report:** See `bug_prophet_report.md` for line-by-line details.

---

## 🔄 Recent Updates

| Date | Change | Commit |
|------|--------|--------|
| 2026-07-25 | Consolidated troubleshooting docs from 3 sources into unified guide | `35453288` |
| 2026-07-23 | Fixed false-positive CI pass for admin backend | `5412e022` |
| 2026-07-23 | Added CORS preflight handler for admin portal | `51d593ce` |
| 2026-07-20 | Phase 0 security hardening completed | `782064b8` |

---

*SupremeAI 2.0 — Self-healing, zero-cost AI infrastructure. Always refer to this guide first before escalating issues.*
