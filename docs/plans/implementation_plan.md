# docs/plans — Implementation Plan (Master, Reconciled)

> **Purpose:** Consolidated implementation direction for the current SupremeAI codebase.
> **Rule:** Existing plans are historical design inputs; this file records the current execution order where plans overlap or conflict.

---

## 0. Current Architecture Direction

SupremeAI follows:

```text
User Goal
  ↓
Intent / Context
  ↓
Capability + Resource Discovery
  ↓
Reusable Implementation Discovery
  ↓
Cost / Risk / Quality / Authorization evaluation
  ↓
reuse / compose / adapt / delegate / generate
  ↓
execute
  ↓
verify
  ↓
learn + promote safely
```

The system must optimize **work avoided**, not merely infrastructure added.

---

## 1. Bootstrap Brain — Current Priority

Source plans:

- `docs/ADMIN_TASKS/SUPREMEAI_BOOTSTRAP_BRAIN_AND_DECISION_LOGIC_PLAN.md`
- `docs/ADMIN_TASKS/implementation_plan.md`

### Decision

`discover_reusable_implementation` is logically available for **every `dev` task**.

It is tiered:

```text
L1: memory / semantic cache
 ↓ miss
L2: internal code / docs / registered capabilities
 ↓ miss
L3: external GitHub / OSS / official SDK / compatible source
```

L3 is policy- and expected-value-gated. Therefore “always enabled” does **not** mean “always perform an expensive web/GitHub search.”

### Methodology decision

The methodology is selected **after discovery**:

```text
reuse → compose → adapt → delegate → generate_new_code
```

Greenfield code is the fallback.

### Required finishing work

- bootstrap seed
- L1/L2/L3 discovery service
- planner wiring
- resource/authorization discovery
- advisor contract
- brain metrics
- verification + governed promotion

---

## 2. Free-Tier Scaling — Reconciled Direction

Source plans:

- `docs/plans/FREE_TIER_UPGRADE_PLAN.md`
- `docs/FREE_TIER_STORAGE_PLAN.md`
- `docs/plans/FREE_TIER_FEDERATION_MASTER_PLAN_V4.md`
- `docs/plans/FREE_TIER_FEDERATION_PLAN_V3.md`

### Architectural decision

Free tiers are **optimization surfaces**, not correctness dependencies.

Preferred order:

```text
cache
→ deduplicate
→ reuse
→ batch
→ async queue
→ authorized user-owned resource
→ suitable free/low-cost provider
→ paid burst only when necessary
```

### Important correction

The old federation concept must **not** treat account multiplication as an unlimited quota multiplier.

Do not build production correctness around:

- rotating multiple accounts solely to multiply quotas
- stealth keep-alives
- fake browser interaction to defeat idle policies
- CAPTCHA/anti-abuse circumvention
- turning interactive notebook free tiers into hidden permanent worker fleets

Multiple resources are valid when they represent legitimate ownership, tenant, security, environment, or provider-supported separation.

### Provider roles

```text
Firebase / CDN
  → static frontend and delivery

Cloudflare
  → edge routing, cache, validation, lightweight logic

Render
  → lean control plane / API

Supabase
  → durable state and memory

Upstash
  → hot cache, locks, queue/rate limiting where appropriate

GitHub Actions
  → repository-native CI/build/test work

Kaggle
  → optional batch/research workloads

Colab
  → optional interactive/admin research; never a required production worker
```

### Quota rule

All quota values must be treated as **provider-versioned configuration**, not hard-coded architectural guarantees.

---

## 3. Missing Services Integration — Reconciled

Source: `docs/plans/MISSING_SERVICES_INTEGRATION_PLAN_V4.1.md`

The existing plan correctly emphasizes:

- secret management
- Eternal Brain / pgvector
- multi-model routing
- resilience
- observability

But implementation should be driven by current code evidence rather than the plan's historical “missing” label.

Before implementing any listed item:

```text
inspect current code
→ confirm missing
→ check existing equivalent
→ measure need
→ implement only if still required
```

Do not create duplicate services when the capability already exists elsewhere.

---

## 4. Production Upgrade — Reconciled

Source: `docs/plans/PRODUCTION_UPGRADE_PLAN.md` and `docs/PRODUCTION_READINESS_PLAN_V3.md`

Enterprise targets such as 99.99% uptime or sub-100ms P95 are **future targets**, not current guarantees.

Free-tier production work should prioritize:

1. startup correctness
2. authentication/security correctness
3. tenant isolation
4. DB indexes/query efficiency
5. connection pooling where justified
6. websocket/resource caps
7. graceful degradation
8. observability
9. rollback/readiness
10. measured load testing

Kubernetes/microservices should not be introduced merely because an old plan contains them. Introduce them only after measured bottlenecks justify the additional maintenance/cost.

---

## 5. Storage and Memory

Source: `docs/FREE_TIER_STORAGE_PLAN.md`

The Eternal Brain should follow:

```text
hot working state
→ recent episodic state
→ validated semantic/procedural knowledge
→ compressed/archive artifacts
→ delete disposable data
```

Do not store every raw intermediate artifact indefinitely.

The memory system should optimize for:

- retrieval quality
- provenance
- confidence
- verification
- reuse
- storage efficiency

---

## 6. Resource-as-Capability

This is now a first-class architectural rule.

When a user/admin legitimately connects a service, SupremeAI should inspect:

```text
what it can do
what permissions exist
what limits exist
what it costs
what data boundary applies
```

Then register usable capabilities without taking ownership of the user's resource.

Example:

```text
User connects GitHub
   ↓
inspect authorized repo/actions capabilities
   ↓
repository-native task?
   ↓
use GitHub-native execution where appropriate
   ↓
verify
   ↓
return result
```

A user's resource must never silently become shared infrastructure for another tenant.

---

## 7. External Implementation Discovery

For any task requiring new implementation:

```text
Estimate missing capability
   ↓
search internal capability/memory/docs
   ↓
search known implementation registry
   ↓
if worthwhile → external discovery
   ↓
license + provenance + security + compatibility + maintenance review
   ↓
reuse/adapt/compose
   ↓
only then create missing code
```

This is the principal mechanism for reducing greenfield implementation over time.

---

## 8. Cost Intelligence

Every execution path should eventually expose:

```text
estimated_cost
actual_cost
latency
quota_pressure
maintenance_cost
risk
verification_history
```

The cheapest path is **not automatically the path with $0 provider price**.

A free service that requires fragile manual operation or creates unacceptable reliability risk may be more expensive operationally than a small paid burst.

Therefore optimize for:

> **minimum sustainable total cost of ownership.**

---

## 9. Self-Evolution

SupremeAI's learning loop:

```text
real problem
 ↓
capability gap
 ↓
reuse/discovery/delegation analysis
 ↓
execution
 ↓
verification
 ↓
lesson candidate
 ↓
confidence + provenance evaluation
 ↓
quarantine if uncertain
 ↓
governed promotion
 ↓
future reuse
```

A failed execution is data, not automatically knowledge.

---

## 10. Implementation Priority

### P0 — Correctness and security

- verify current production blockers
- tenant isolation
- secret handling
- authentication
- DB integrity
- migration correctness

### P1 — Brain decision loop

- bootstrap brain
- L1/L2 discovery
- discovery-first methodology
- resource/authorization discovery
- verification

### P2 — Efficiency

- semantic cache
- task deduplication
- artifact hashing
- batch execution
- quota-aware admission
- backpressure

### P3 — External capability ecosystem

- MCP capability registry
- GitHub-native workflows
- approved browser delegation
- external provider adapters
- L3 reusable implementation discovery

### P4 — Self-evolution

- lesson promotion
- capability creation
- sandbox validation
- rollback
- routing optimization from historical outcomes

### P5 — Scale validation

- concurrency tests
- queue stress tests
- provider failure tests
- quota exhaustion tests
- cache/reuse measurements
- heavy-task admission tests

---

## 11. Acceptance Criteria

Do not declare this architecture “complete” because the documents exist.

Demonstrate with tests that:

- similar dev tasks increasingly reuse existing capability
- every dev task has access to reusable-implementation discovery
- expensive external discovery is avoided when internal evidence is sufficient
- `generate_new_code` is a fallback
- provider failure does not destroy core task state
- user authorization boundaries are enforced
- repeated work is deduplicated
- queue/backpressure prevents overload
- new knowledge is not promoted without verification
- the system can operate without any single optional provider
- free-tier changes do not require an architectural rewrite

---

## 12. Plan Governance

When a new plan is added to `docs/`:

1. identify which existing plan it supersedes
2. inspect current code before marking work “missing”
3. avoid duplicate implementations
4. record assumptions and external limits
5. define verification criteria
6. assign an owner/status
7. reconcile it into this master plan

This prevents plan sprawl from becoming an architecture problem.

---

## 13. Concrete Actionable Steps (Tracking)

> **Note:** These are the actionable execution steps mapped from the reconciled plan above.


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
