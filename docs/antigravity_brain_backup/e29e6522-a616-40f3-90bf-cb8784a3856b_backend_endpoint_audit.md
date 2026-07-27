# SupremeAI 2.0 — Backend Endpoint Audit Report
_Generated: 2026-07-11_

---

## 🗂️ Router Registration Overview

`main.py` manually registers **7 routers**, `core/app.py` dynamically loads **33 core routers** + **22 optional routers** via `_safe_include_router`. Total route files in `api/routes/`: **61 files**.

---

## 🔴 Critical Issues

### 1. DUPLICATE Router Registration — `auth`, `onboarding`, `evolution`

**`main.py`** AND **`core/app.py`** both register some of the same routers:

| Router | Registered in main.py | Registered in core/app.py (core_routers) | core/app.py (optional_routers) |
|--------|----------------------|------------------------------------------|-------------------------------|
| `api.routes.auth` | ✅ `/api/v1` | ✅ `""` (no prefix) | ❌ |
| `api.routes.integrations` | ✅ `/api/v1` | ❌ | ❌ |
| `api.routes.admin` | ✅ (direct) | ❌ | ❌ |
| `api.routes.onboarding` | ❌ | ✅ `""` | ✅ `/api` (DOUBLE!) |
| `api.routes.evolution` | ❌ | ✅ `""` | ✅ `""` (DOUBLE!) |

**auth router** is registered TWICE → `/api/v1/auth/login` AND `/auth/login` both exist.  
**onboarding** is registered TWICE in optional_routers.  
**evolution** is registered TWICE in optional_routers.

> [!CAUTION]
> Duplicate router registration causes FastAPI to create duplicate routes. The OpenAPI docs will show duplicate paths, and some middleware/rate-limiters may apply twice to the same request.

---

### 2. `task_workspace.py` — ROUTE CONFLICT with `task.py`

- `task_workspace.py` router: prefix `/task`, route `POST /execute` → **`/task/execute`**
- `task.py` router: no prefix, route `POST /task/execute` → **`/task/execute`**

Both register **the same path**. FastAPI will use whichever was registered first — the second is silently ignored.

> [!CAUTION]
> `/task/execute` is a core endpoint used by the frontend chat. One of these implementations is dead code.

---

### 3. `billing_api.py` vs `payments.py` — TWO Stripe implementations

- `billing_api.py`: prefix `/api/billing`, includes `POST /webhook/stripe`
- `payments.py`: prefix `/payments`, includes `POST /webhook`

Two separate Stripe webhook handlers exist on different paths. The SSLCommerz webhook is only in `billing_api.py`. These should be unified.

---

### 4. `swarm.py` — No URL prefix, routes registered under `integrations_router` in `main.py`

`swarm.py`'s router has **no prefix** (`router = APIRouter(tags=["Swarm"])`), and `swarm_router` is only imported in `__init__.py` but **never passed to `app.include_router()` anywhere** in `main.py` or `core/app.py`.

> [!CAUTION]
> Swarm endpoints (`/stream`, `/forge`, `/execute-healing`, `/telemetry/patch-result`) are **unreachable** unless registered explicitly.

---

### 5. `tenant_admin.py` — Prefix mismatch

- Router prefix: `/admin/tenant-limits`
- Called with: `prefix="/api"` in `optional_routers`
- Final paths: `/api/admin/tenant-limits` ✅

But the header comment says `GET /api/admin/tenant-limits` — this is correct **only if** the optional_routers prefix `/api` combines. This works but is fragile.

---

### 6. `auth.py` — `POST /login` blocked in production

```python
if settings.env != "local" and settings.env != "test":
    raise HTTPException(status_code=501, ...)
```

In production, `/api/v1/auth/login` returns **501 Not Implemented** with no fallback for non-Firebase authentication. Users cannot log in via direct credentials in production. If SSO/TOTP is not configured, the platform is **inaccessible**.

---

### 7. `billing_api.py` — Hardcoded `user_id = "default_user_session"`

```python
user_id = "default_user_session"  # in /wallet, /history, /add-funds
```

Wallet endpoints don't use JWT authentication — every user sees the same wallet balance.

> [!CAUTION]
> This is a **critical security flaw**. All billing data is shared across all users.

---

### 8. `task_workspace.py` — `save_to_supabase` is a no-op stub

```python
def save_to_supabase(task, result):
    pass  # supabase.table(...).insert(...).execute()
```

Background task does nothing. Task history is never persisted.

---

## 🟡 Moderate Issues

### 9. `agents.py` — No prefix in `main.py` registration, but registered with `/api/v1`

- `main.py` line 24: `app.include_router(agent_router, prefix="/api/v1")`
- But `agent_router` in `__init__.py` imports from `.agent_tasks` not `.agents`
- `agents.py` is registered separately in `core_routers` with prefix `""`
- Final path: `/agents/legal/analyze`, `/agents/medical/symptoms` etc. (no `/api/v1`)

This may be intentional but inconsistent with other agent paths.

---

### 10. `health.py` vs `core/app.py` — Duplicate `/health` endpoint

- `core/app.py` defines `@app.get("/health")` directly (line 151)
- `api/routes/health.py` registers `@router.post("/api/health/agents")`

These don't conflict but having a health route defined in `app.py` is an anti-pattern — all routes should be in dedicated route files.

---

### 11. `swarm.py` — `@limiter.limit("5/minute")` without SlowAPI state on app

`swarm.py` creates its own `Limiter` instance:
```python
limiter = Limiter(key_func=get_remote_address)
```
But SlowAPI requires `app.state.limiter = limiter` and the exception handler to be registered. The `core/app.py` registers the exception handler globally but this local limiter instance is not attached to the app — the limit decorator **will not work**.

---

### 12. `evolution.py` — `FitnessEngine` used as a FastAPI Dependency incorrectly

```python
fitness_engine: FitnessEngine | None = Depends(FitnessEngine)
```
`FitnessEngine` is a class, not a dependency factory. FastAPI will try to call `FitnessEngine()` with zero args — if FitnessEngine's `__init__` requires args this will crash on each request.

---

### 13. `integrations.py` — No DB migration guard for `Integration` model

The GitHub callback tries to query `Integration` table with SQLAlchemy but there's no check if the migration has been run. If `alembic upgrade head` hasn't been run, every callback will crash with `table does not exist`.

---

### 14. `admin.py` — `god_layer` instantiated at module load with hardcoded path

```python
god_layer = AdminGodLayer(db_path="data/admin_rules.db")
```
Relative path `data/admin_rules.db` — this will fail if the server is started from a directory other than `/backend/`. Should use `Path(__file__).parent / ".." / "data" / "admin_rules.db"`.

---

### 15. `websocket_agent.py` — `SupabaseDB` called with sync methods in async context

```python
user_pref_record = await asyncio.to_thread(db.get_user_preferences, user_id)
```
Uses `asyncio.to_thread` which is correct. But `upsert_user_preferences` is also run via `asyncio.to_thread` inside `analyze_and_save_preferences`. This is fine but adds latency per message. Consider native async Supabase client.

---

## 🟢 What's Working Well

| Area | Status |
|------|--------|
| `core/app.py` CORS config | ✅ Properly configured, no wildcard |
| `core/app.py` Middleware stack | ✅ Auth, Rate-limit, Honeypot, Observability all chained |
| `auth.py` JWT token structure | ✅ Proper HS256, expiry, role claims |
| `task.py` semantic cache | ✅ Vector cache with fallback |
| `swarm.py` ForgeCompiler DAG | ✅ Topological sort with cycle detection |
| `billing_api.py` Stripe signature verification | ✅ Secure |
| `payments.py` Stripe mock fallback | ✅ Dev-friendly |
| `evolution.py` Proposal approval flow | ✅ Admin-gated |
| `memory.py` Checkpoint/Window endpoints | ✅ Clean, no issues |
| `websocket_agent.py` auth rejection | ✅ WS_1008 on no-token |
| `dependencies.py` test bypass | ✅ `is_test_environment()` guard |
| `health.py` Redis/API key checks | ✅ Proper degraded state |
| `_safe_include_router` pattern | ✅ Won't crash on import failure |
| `router_health_check` minimum route count | ✅ Fail-fast safety net |

---

## 📋 Fix Priority List

| # | Issue | Severity | File(s) |
|---|-------|----------|---------|
| 1 | Duplicate auth/onboarding/evolution router registration | 🔴 Critical | `main.py`, `core/app.py` |
| 2 | `/task/execute` conflict between task.py and task_workspace.py | 🔴 Critical | `task.py`, `task_workspace.py` |
| 3 | `swarm_router` never registered on the app | 🔴 Critical | `main.py` or `core/app.py` |
| 4 | Billing hardcoded `user_id = "default_user_session"` | 🔴 Critical | `billing_api.py` |
| 5 | `save_to_supabase` is a no-op stub | 🟡 Moderate | `task_workspace.py` |
| 6 | `FitnessEngine` misused as FastAPI Depends | 🟡 Moderate | `evolution.py` |
| 7 | `AdminGodLayer` relative DB path | 🟡 Moderate | `admin.py` |
| 8 | Swarm local limiter not attached to app | 🟡 Moderate | `swarm.py` |
| 9 | Two Stripe webhook implementations | 🟡 Moderate | `billing_api.py`, `payments.py` |
| 10 | Production login returns 501 with no SSO fallback | 🟡 Moderate | `auth.py` |

---

## Route Prefix Map (Resolved)

| Router Module | Declared Prefix | `include_router` Prefix | Final Base URL |
|--------------|----------------|------------------------|----------------|
| `auth.py` | `/auth` | `/api/v1` (main.py) + `""` (app.py) | `/api/v1/auth/*` + `/auth/*` (DUPLICATE) |
| `task.py` | none | `""` | `/task/execute`, `/api/chat/*` |
| `task_workspace.py` | `/task` | none (main.py) | `/task/execute` (CONFLICT) |
| `admin.py` | `/api/admin` | none | `/api/admin/*` |
| `admin_dashboard.py` | varies | `""` | depends on router defs |
| `swarm.py` | none | NOT REGISTERED | ❌ UNREACHABLE |
| `integrations.py` | none | `/api/v1` | `/api/v1/integrations/*` |
| `billing_api.py` | `/api/billing` | `""` | `/api/billing/*` |
| `payments.py` | `/payments` | `""` | `/payments/*` |
| `llm_gateway.py` | `/api/admin/llm` | `""` | `/api/admin/llm/*` |
| `metrics.py` | `/api/admin/metrics` | `""` | `/api/admin/metrics/*` |
| `tenant_admin.py` | `/admin/tenant-limits` | `/api` | `/api/admin/tenant-limits/*` |
| `evolution.py` | `/api/evolution` | `""` + `""` | `/api/evolution/*` (DOUBLE REG) |
| `memory.py` | `/memory` | `""` | `/memory/*` |
| `agents.py` | `/agents` | `""` | `/agents/*` |
| `health.py` | none | `""` | `/api/health/agents` |
| `websocket_agent.py` | `/ws` | none (main.py) | `/ws/chat` |
| `public_config.py` | `/config/public` | `/api` | `/api/config/public` |
| `traffic_monitor.py` | `/api/admin/traffic` | none | `/api/admin/traffic/live` |
