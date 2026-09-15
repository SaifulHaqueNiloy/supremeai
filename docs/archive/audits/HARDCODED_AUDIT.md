# 🔍 SupremeAI Hardcoded Values Audit
> **Generated:** 2026-08-24 | **Scope:** Full codebase scan (`backend/`, `frontend/`, `infrastructure/`, `scripts/`, `.github/`)  
> **Goal:** Identify all static values that should be externalized to Infisical, config, or environment variables.

---

## 🔴 CRITICAL — Production URLs & Endpoints

These are live service URLs hardcoded in source files. If a service changes, code must be manually updated.

| File | Line | Hardcoded Value | Recommended Variable |
|------|------|-----------------|----------------------|
| [`scripts/keepalive.js`](file:///f:/supremeai/scripts/keepalive.js#L4) | 4 | `https://supremeai-backend-docker.onrender.com` | `BACKEND_URL` |
| [`scripts/health/check_system_health.py`](file:///f:/supremeai/scripts/health/check_system_health.py#L46) | 46 | `supremeai-backend-docker.onrender.com` (fallback) | `BACKEND_URL` |
| [`scripts/monitoring/sla_tracker.py`](file:///f:/supremeai/scripts/monitoring/sla_tracker.py#L68) | 68-69 | `supremeai-backend-docker.onrender.com`, `supremeai-scraper-6nwi.onrender.com` | `BACKEND_URL`, `SCRAPER_URL` |
| [`infrastructure/cloudflare/worker.js`](file:///f:/supremeai/infrastructure/cloudflare/worker.js#L76) | 76-78 | `supremeai-backend-v2.onrender.com`, `supremeai-scraper-6nwi.onrender.com` | Use `env.RENDER_URL`, `env.SCRAPER_SERVICE_URL` |
| [`firebase.json`](file:///f:/supremeai/firebase.json#L18) | 18, 22, 82 | `supremeai-backend-docker.onrender.com` | `BACKEND_URL` |
| [`frontend/main.js`](file:///f:/supremeai/frontend/main.js#L11) | 11 | `supremeai-backend-docker.onrender.com` | `VITE_USER_BACKEND` |
| [`frontend/src/components/admin/infra/ServiceHealthMonitor.tsx`](file:///f:/supremeai/frontend/src/components/admin/infra/ServiceHealthMonitor.tsx#L57) | 57, 67 | `supremeai-backend-docker.onrender.com`, `supremeai-scraper-6nwi.onrender.com` | Load from `/api/config/public` |
| [`frontend/src/components/admin/data/CrownJewelBrowser.tsx`](file:///f:/supremeai/frontend/src/components/admin/data/CrownJewelBrowser.tsx#L62) | 62-63 | `supremeai-backend-docker.onrender.com`, `supremeai-scraper-6nwi.onrender.com` | Load from `/api/config/public` |
| [`backend/middleware/cors_policy.py`](file:///f:/supremeai/backend/middleware/cors_policy.py#L23) | 23-29 | `supremeai-a.web.app`, `supremeai-admin.web.app` | `CORS_ORIGINS`, `ADMIN_CORS_ORIGINS` env var |
| [`backend/core/security/origin_validator.py`](file:///f:/supremeai/backend/core/security/origin_validator.py#L22) | 22-31 | `supremeai-a.web.app`, `supremeai-admin.web.app` | `CORS_ORIGINS` env var |

---

## 🔴 CRITICAL — Redis URL Defaults (localhost)

Render-এ `localhost:6379` নেই, তাই এই fallback গুলো প্রোডাকশনে ব্রেক করে।

| File | Line | Hardcoded Value | Fix |
|------|------|-----------------|-----|
| [`backend/core/cache.py`](file:///f:/supremeai/backend/core/cache.py#L37) | 37, 59, 313 | `redis://localhost:6379` | `settings.redis_url` |
| [`backend/core/rate_limit.py`](file:///f:/supremeai/backend/core/rate_limit.py#L60) | 60 | `redis://localhost:6379` | `settings.redis_url` |
| [`backend/core/rate_limit_quota.py`](file:///f:/supremeai/backend/core/rate_limit_quota.py#L13) | 13 | `redis://localhost:6379` | `settings.redis_url` |
| [`backend/core/optimization/optimized_redis_client.py`](file:///f:/supremeai/backend/core/optimization/optimized_redis_client.py#L54) | 54, 143 | `redis://localhost:6379` | `settings.redis_url` |
| [`backend/core/queue/task_queue_enhanced.py`](file:///f:/supremeai/backend/core/queue/task_queue_enhanced.py#L93) | 93, 582 | `redis://localhost:6379` | `settings.redis_url` |
| [`backend/api/routes/websocket_agent.py`](file:///f:/supremeai/backend/api/routes/websocket_agent.py#L97) | 97-99 | `redis://localhost:6379` | `settings.redis_url` |
| [`backend/tools/collaborative_editor.py`](file:///f:/supremeai/backend/tools/collaborative_editor.py#L26) | 26-29 | `redis://localhost:6379` | `settings.redis_url` |

---

## 🟠 HIGH — App Identity & Domain Names

| File | Line | Hardcoded Value | Recommended Variable |
|------|------|-----------------|----------------------|
| [`backend/tools/social/viral_referral_engine.py`](file:///f:/supremeai/backend/tools/social/viral_referral_engine.py#L330) | 330 | `https://supremeai.com` | `APP_BASE_URL` |
| [`backend/tools/sso_integrator.py`](file:///f:/supremeai/backend/tools/sso_integrator.py#L218) | 218-250 | `https://supremeai.com/metadata`, `/acs`, `/sls` | `APP_BASE_URL` |
| [`backend/tools/social/telegram_bot.py`](file:///f:/supremeai/backend/tools/social/telegram_bot.py#L358) | 358, 891, 1059 | `https://supremeai-admin.web.app` | `ADMIN_DASHBOARD_URL` |
| [`scripts/tenant/auto_tenant_setup.py`](file:///f:/supremeai/scripts/tenant/auto_tenant_setup.py#L44) | 44, 276, 292 | `admin@supremeai.com`, `noreply@supremeai.com`, `app.supremeai.com` | `ADMIN_EMAIL`, `SENDER_EMAIL`, `APP_BASE_URL` |
| [`scripts/tenant/auto_tenant_health_report.py`](file:///f:/supremeai/scripts/tenant/auto_tenant_health_report.py#L421) | 421, 597 | `noreply@supremeai.com`, `admin@supremeai.com` | `SENDER_EMAIL`, `ADMIN_EMAIL` |
| [`scripts/db/auto_seed.py`](file:///f:/supremeai/scripts/db/auto_seed.py#L38) | 38 | `admin@supremeai.com` | `ADMIN_EMAIL` |
| [`frontend/src/shared/supremeShared.ts`](file:///f:/supremeai/frontend/src/shared/supremeShared.ts#L36) | 36, 42 | `https://api.supremeai.com`, `wss://api.supremeai.com/ws` | `VITE_USER_BACKEND` |
| [`infrastructure/firebase_functions/firebase_functions_v1/providers-smart.js`](file:///f:/supremeai/infrastructure/firebase_functions/firebase_functions_v1/providers-smart.js#L7) | 7, 14 | `studio.supremeai.com`, `supremeai-dashboard.web.app` | `ADMIN_DASHBOARD_URL` |
| [`tools/vscode-extension/src/providers/SupremeAICustomerDashboardProvider.ts`](file:///f:/supremeai/tools/vscode-extension/src/providers/SupremeAICustomerDashboardProvider.ts#L107) | 107 | `https://supremeai-a.web.app` | VS Code settings config |

---

## 🟠 HIGH — Rate Limits & Tier Configurations

এই ভ্যালুগুলো পরিবর্তন করতে এখন কোড deploy করতে হয়।

| File | Line | Hardcoded Value | Recommended Approach |
|------|------|-----------------|----------------------|
| [`backend/core/rate_limit.py`](file:///f:/supremeai/backend/core/rate_limit.py#L46) | 46-51 | Anonymous: 10/min, Auth: 60/min, Premium: 300/min, Admin: 1000/min | DB-backed `rate_limit_tiers` config |
| [`backend/core/rate_limit.py`](file:///f:/supremeai/backend/core/rate_limit.py#L54) | 54-58 | `/api/chat/stream`: 30/min, `/api/ai/generate`: 20/min | DB-backed `endpoint_overrides` config |
| [`backend/core/retry_budget.py`](file:///f:/supremeai/backend/core/retry_budget.py#L33) | 33 | `max_tokens=20`, `refill_rate_per_sec=1.0` | `RETRY_BUDGET_MAX_TOKENS`, `RETRY_BUDGET_REFILL_RATE` |

---

## 🟡 MEDIUM — LLM / AI Configurations

| File | Line | Hardcoded Value | Recommended Variable |
|------|------|-----------------|----------------------|
| [`backend/services/video_to_code_pipeline.py`](file:///f:/supremeai/backend/services/video_to_code_pipeline.py#L203) | 203, 282 | `max_tokens=1500`, `max_tokens=2000` | `LLM_MAX_TOKENS_VIDEO` |
| [`backend/services/diagram_parser_service.py`](file:///f:/supremeai/backend/services/diagram_parser_service.py#L341) | 341, 475 | `max_tokens=1500`, `max_tokens=2000` | `LLM_MAX_TOKENS_DIAGRAM` |
| [`backend/core/tier8/self_improvement_agent.py`](file:///f:/supremeai/backend/core/tier8/self_improvement_agent.py#L246) | 246 | `max_tokens=2048`, `temperature=0.2` | `SELF_IMPROVE_MAX_TOKENS` |
| [`backend/core/tier8/swarm_coordination_agent.py`](file:///f:/supremeai/backend/core/tier8/swarm_coordination_agent.py#L281) | 281 | `max_tokens=1024`, `temperature=0.3` | `SWARM_MAX_TOKENS` |
| [`backend/core/evolution/daily_learner.py`](file:///f:/supremeai/backend/core/evolution/daily_learner.py#L129) | 129-130 | `max_tokens=2000`, `temperature=0.3` | `DAILY_LEARNER_MAX_TOKENS` |
| [`backend/core/security/intelligence/guardian_ai.py`](file:///f:/supremeai/backend/core/security/intelligence/guardian_ai.py#L299) | 299 | `temperature=0.0` | `GUARDIAN_AI_TEMPERATURE` |

---

## 🟡 MEDIUM — Timeouts & Connection Settings

| File | Line | Hardcoded Value | Recommended Variable |
|------|------|-----------------|----------------------|
| [`backend/core/orchestration/orchestrator.py`](file:///f:/supremeai/backend/core/orchestration/orchestrator.py#L75) | 75 | `timeout=120` | `ORCHESTRATOR_TIMEOUT` |
| [`backend/core/shutdown.py`](file:///f:/supremeai/backend/core/shutdown.py#L49) | 49 | `timeout=30` | `SHUTDOWN_TIMEOUT` |
| [`backend/core/lifespan.py`](file:///f:/supremeai/backend/core/lifespan.py#L132) | 132 | `timeout=30.0` | `DB_BOOTSTRAP_TIMEOUT` |
| [`backend/core/type_sync_bus.py`](file:///f:/supremeai/backend/core/type_sync_bus.py#L177) | 177, 211 | `timeout=120`, `timeout=60` | `TYPE_SYNC_TIMEOUT` |
| [`backend/core/optimization/optimized_redis_client.py`](file:///f:/supremeai/backend/core/optimization/optimized_redis_client.py#L77) | 77-78 | `socket_connect_timeout=5`, `socket_timeout=5` | `REDIS_SOCKET_TIMEOUT` |
| [`backend/core/kaggle_orchestrator.py`](file:///f:/supremeai/backend/core/kaggle_orchestrator.py#L123) | 123 | `timeout=300.0` (5 min) | `KAGGLE_TASK_TIMEOUT` |

---

## 🟡 MEDIUM — Ports & Internal Addresses

| File | Line | Hardcoded Value | Recommended Variable |
|------|------|-----------------|----------------------|
| [`backend/core/evolution/digital_twin/topology.py`](file:///f:/supremeai/backend/core/evolution/digital_twin/topology.py#L521) | 521, 534 | `port=8000`, `port=8001` | `BACKEND_PORT`, `DIGITAL_TWIN_PORT` |

---

## 🟡 MEDIUM — Admin / Security Defaults

> [!CAUTION]
> নিচের ৩টি ফাইলে `admin@supremeai.com` হার্ডকোড করা আছে **dev fallback হিসেবে production কোডে**। `ENVIRONMENT != "production"` চেক না থাকলে এটি সিকিউরিটি রিস্ক।

| File | Line | Hardcoded Value | Fix |
|------|------|-----------------|-----|
| [`backend/core/security/authentication/rbac.py`](file:///f:/supremeai/backend/core/security/authentication/rbac.py#L271) | 271-274 | `"sub": "admin@supremeai.com"` | `ADMIN_EMAIL` + env guard |
| [`backend/api/deps.py`](file:///f:/supremeai/backend/api/deps.py#L35) | 35 | `"sub": "admin@supremeai.com"` | `ADMIN_EMAIL` + env guard |
| [`backend/api/dependencies.py`](file:///f:/supremeai/backend/api/dependencies.py#L113) | 113 | `"sub": "admin@supremeai.com"` | `ADMIN_EMAIL` + env guard |

---

## 🟢 LOW — CI/CD & Infrastructure Config

| File | Line | Hardcoded Value | Status |
|------|------|-----------------|--------|
| [`.github/workflows/ci.yml`](file:///f:/supremeai/.github/workflows/ci.yml#L240) | 240-241 | `VITE_USER_BACKEND`, `VITE_ADMIN_BACKEND` | ✅ **Fixed** — Infisical-first with fallback |
| [`mkdocs.yml`](file:///f:/supremeai/mkdocs.yml#L7) | 7-8 | `https://github.com/SaifulHaqueNiloy/supremeai` | Acceptable for docs |
| [`backend/action.yml`](file:///f:/supremeai/backend/action.yml#L51) | 51 | `SaifulHaqueNiloy/supremeai.git@main` | Acceptable for CI |

---

## 📋 Summary & Priority Action Plan

| Priority | Count | Action |
|----------|-------|--------|
| 🔴 Critical (fix immediately) | ~17 files | Redis `localhost` defaults + dead `onrender.com` URLs |
| 🟠 High (this week) | ~12 files | App domain URLs + CORS origins via Infisical env |
| 🟡 Medium (next sprint) | ~15 files | Timeouts, LLM params → DB `ai_config` table |
| 🟢 Low (nice to have) | ~3 files | CI/CD, docs references |

### Recommended 3-Step Strategy

1. **Redis (Immediate)** — সব `"redis://localhost:6379"` fallback কে `settings.redis_url` দিয়ে replace করুন
2. **URLs (This week)** — `BACKEND_URL`, `SCRAPER_URL`, `ADMIN_DASHBOARD_URL`, `APP_BASE_URL` Infisical-এ রাখুন এবং `cors_policy.py` + `origin_validator.py`-এর hardcoded list এনভায়রনমেন্ট ভ্যারিয়েবল থেকে লোড করুন  
3. **AI/Rate Limits (Next sprint)** — একটি `system_config` DB টেবিল তৈরি করুন যেখানে LLM parameters ও rate limit tiers থাকবে, এবং Admin Dashboard থেকে সেগুলো লাইভ পরিবর্তন করা যাবে
