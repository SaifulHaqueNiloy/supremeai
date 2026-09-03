# docs/plans — Implementation Plan (Master)

> **Covers:** সব ননএম্পটি প্ল্যান ফাইলের consolidated implementation status ও পরবর্তী কাজ।  
> **Single Source:** প্রতিটি সাব-সেকশন তার নিজ প্ল্যান ফাইলের বিপরীতে track করে।

---

## 1. `FREE_TIER_UPGRADE_PLAN.md` — Modular Monolith Migration

**Goal:** ৩টি Render Service → ১টি Single Render Free-Tier Compliant Service ($0/month)

### ✅ Already Done
| Component | Status |
|---|---|
| FastAPI backend + uvicorn | ✅ Running |
| Supabase (PostgreSQL + pgvector) | ✅ Connected |
| CascadeMemoryService | ✅ Production |
| LLM Gateway (multi-provider) | ✅ Active |
| Playwright browser (services/browser/) | ✅ Exists |

### 🚧 Pending Tasks

#### Step 1 — Scraper Module Embed (High Priority)
- **কাজ:** আলাদা scraper Docker service বন্ধ করে `backend/services/scraper/` মডিউলকে main FastAPI app-এ import করা
- **ফাইল:** `backend/main.py` → `from services.scraper import scraper_router` যোগ করা
- **টেস্ট:** `pytest tests/services/test_scraper.py`

#### Step 2 — Single render.yaml Consolidation
- **কাজ:** `render.yaml`-এ `services` সংখ্যা ৩ থেকে ১-এ নামিয়ে আনা
- **ফাইল:** [`render.yaml`](file:///f:/supremeai/render.yaml) (root)
- **টেস্ট:** Render Preview deploy → health endpoint check

#### Step 3 — In-Process Worker Migration
- **কাজ:** Celery/Redis worker → FastAPI `lifespan` + `asyncio.create_task()` দিয়ে background task
- **ফাইল:** `backend/worker_service.py` → `backend/core/background_tasks.py` তৈরি
- **টেস্ট:** `pytest tests/test_background_tasks.py`

#### Step 4 — Render Free Tier Resource Guard
- **কাজ:** 512MB RAM + 0.1 vCPU সীমায় থাকতে Memory Profiler + Auto-GC যোগ করা
- **ফাইল:** `backend/middleware/resource_guard.py` (new)
- **টেস্ট:** Load test: 50 concurrent requests → RAM < 450MB

---

## 2. `MISSING_SERVICES_INTEGRATION_PLAN_V4.1.md` — Missing Services Integration

**Focus:** Infisical, IDE Trio, PGVector/Eternal Brain, Sentry, Multi-Model AI

### ✅ Already Done
| Service | Status |
|---|---|
| Infisical Secret Vault (`core/security/secret_vault.py`) | ✅ Implemented |
| CascadeMemoryService pgvector (Eternal Brain) | ✅ Production |
| Multi-Model LLM Router (Gemini/Groq/OpenRouter) | ✅ Active |
| TTL Cache + Circuit Breaker (Infisical) | ✅ Done |

### 🚧 Pending Tasks

#### Step 1 — Infisical Secret Consolidation (83% capacity → safe)
- **কাজ:** ৩০টি স্বতন্ত্র সিক্রেটকে JSON-packed গ্রুপে কমানো (`AI_PROVIDERS_JSON`, `DB_CONFIG_JSON`)
- **ফাইল:** `backend/core/security/secret_vault.py` → `load_grouped_secrets()` মেথড যোগ
- **টেস্ট:** `python scripts/verify_infisical_secrets.py`

#### Step 2 — IDE Trio Integration (VS Code Extension)
- **কাজ:** `backend/services/ide_trio/` → REST API endpoint expose করা: `/api/ide/context`, `/api/ide/complete`
- **ফাইল:** `backend/api/routes/ide_trio.py` (new)
- **টেস্ট:** cURL test against local dev server

#### Step 3 — Sentry Error Tracking Integration
- **কাজ:** `sentry_sdk.init()` → `backend/core/app.py` lifespan-এ যোগ করা (DSN from Infisical)
- **ফাইল:** `backend/core/app.py`
- **টেস্ট:** Trigger a test exception → verify Sentry dashboard capture

#### Step 4 — pgvector HNSW Index
- **কাজ:** `ai_memory` table-এ cosine similarity HNSW index তৈরি করা (retrieval 10x faster)
- **Migration:** `backend/alembic_migrations/versions/XXX_hnsw_index.py`
- **SQL:** `CREATE INDEX CONCURRENTLY ON ai_memory USING hnsw (embedding vector_cosine_ops)`

---

## 3. `PRODUCTION_UPGRADE_PLAN.md` — Enterprise Production Upgrade

**Goal:** Dev phase → Enterprise-grade (99.99% uptime, <100ms P95)

> [!IMPORTANT]
> এই প্ল্যানে K8s/Microservices-এর উল্লেখ আছে — কিন্তু বর্তমান **Free-Tier First** পলিসিতে K8s deploy করা অসম্ভব। শুধুমাত্র Free-Tier-compatible অংশগুলো বাস্তবায়নযোগ্য।

### ✅ Already Done
| Component | Status |
|---|---|
| JWT Auth + RBAC middleware | ✅ Active |
| pgvector HNSW (partial) | ⚠️ Index missing |
| Multi-provider LLM routing | ✅ Active |
| Self-correction service | ✅ Active |

### 🚧 Pending (Free-Tier Compatible Items Only)

#### Step 1 — PgBouncer Connection Pooling
- **কাজ:** Supabase Transaction Mode pooler URL → `SUPABASE_POOLER_URL` env var
- **ফাইল:** `backend/core/persistence.py` → pooler URL priority
- **টেস্ট:** `pytest tests/core/test_persistence.py`

#### Step 2 — WebSocket Connection Cap & Heartbeat
- **কাজ:** সব `websocket_*.py`-এ `MAX_CONNECTIONS=50`, per-user cap=3, 30s heartbeat
- **ফাইলসমূহ:** `backend/api/routes/websocket_voice.py`, `websocket_hitl.py`, `websocket_agent.py`
- **টেস্ট:** `pytest tests/api/routes/test_websocket_*.py`

#### Step 3 — Distributed Tracing (OpenTelemetry, Zero Cost)
- **কাজ:** `opentelemetry-sdk` + Jaeger/Honeycomb free tier connector
- **ফাইল:** `backend/core/telemetry.py` (new)
- **টেস্ট:** একটি request trace করে span দেখা

#### Step 4 — DB Index Migration
- **কাজ:** `conversations.user_id`, `messages.conversation_id`, `artifacts.conversation_id`-এ B-tree index
- **Migration:** `backend/alembic_migrations/versions/XXX_user_indexes.py`

---

## 4. `SUPREMEAI_FREE_TIER_MULTI_SERVICE_SCALE_MASTER_PLAN.md` — Scaling Constitution

**Goal:** Free tier সীমার মধ্যে সর্বোচ্চ ক্যাপাসিটি, policy-safe architecture

### ✅ Already Done
| Rule | Status |
|---|---|
| Rule 1: Replaceable adapter per provider | ✅ LLMGateway wraps all providers |
| Rule 4: Deduplicate → Cache → Reuse | ✅ IntelligentCache exists |
| Rule 5: No single point of correctness | ✅ Multi-provider fallback |

### 🚧 Pending Tasks

#### Step 1 — Capability Registry (Plan Requirement)
- **কাজ:** প্রতিটি LLM provider-এর capability, cost/token, rate limit → database-backed registry
- **ফাইল:** `backend/brain/capability_registry.py` (new)
- **স্কিমা:** `ai_memory` metadata JSONB-তে `brain_domain="capability_knowledge"` হিসেবে store

#### Step 2 — Upstash Queue/Rate-Limiter Integration
- **কাজ:** Upstash Redis-এ per-user rate limiting + task queue (free 10K commands/day)
- **ফাইল:** `backend/core/queue_service.py` (new/extend existing)
- **টেস্ট:** `pytest tests/core/test_queue_service.py`

#### Step 3 — Cloudflare Workers Edge Cache
- **কাজ:** Static assets + public API responses → CF Workers Cache (free 100K requests/day)
- **ফাইল:** `cloudflare/` directory-তে `worker.js` + `wrangler.toml`
- **টেস্ট:** CF Worker deploy → cache hit ratio check

#### Step 4 — Provider Cost/Quota Model
- **কাজ:** প্রতিটি LLM call-এর token cost track করে budget guardrail
- **ফাইল:** `backend/core/llm/cost_tracker.py` (new)
- **টেস্ট:** `pytest tests/core/llm/test_cost_tracker.py`

---

## Implementation Priority Order

```
Priority 1 (This Week):
  ├── FREE_TIER_UPGRADE: Step 1 (Scraper embed) + Step 2 (render.yaml)
  ├── MISSING_SERVICES: Step 1 (Infisical consolidation) + Step 4 (HNSW index)
  └── PRODUCTION: Step 2 (WebSocket cap)

Priority 2 (Next Week):
  ├── FREE_TIER_UPGRADE: Step 3 (Worker migration) + Step 4 (Resource guard)
  ├── MISSING_SERVICES: Step 2 (IDE Trio) + Step 3 (Sentry)
  └── SCALING: Step 1 (Capability Registry) + Step 2 (Upstash Queue)

Priority 3 (Following Week):
  ├── PRODUCTION: Step 1 (PgBouncer) + Step 3 (OpenTelemetry)
  └── SCALING: Step 3 (CF Workers) + Step 4 (Cost Tracker)
```

## Verification Gate

প্রতিটি Step শেষে:
```bash
cd backend
poetry run pytest -n auto --timeout=60 -q --no-cov
# → 0 failures required before next step
```
