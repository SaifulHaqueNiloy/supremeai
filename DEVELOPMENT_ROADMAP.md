# SupremeAI 2.0 — Comprehensive Development Roadmap
> **Date:** 2026-08-19
> **Status:** Active — Phase 0 (Foundation & Store Consolidation) 100% Complete; Phase 1 (Technical Debt Reduction & Memory Encapsulation) 100% Complete; Phase 2 (Performance, WS Delta Engine & Alembic CI Gate) Active
> **ভাষা:** Bangla/Banglish (Simple Language); headers English

---

## 1. Executive Summary (কারেন্ট অবস্থা)

SupremeAI 2.0 হলো একটি **self-learning AI infrastructure** (Universal Agent Platform) যার
কোর আর্কিটেকচার এখন solid: unified **FastAPI backend (~318 routes, 85 route files)** + **React/Vite Studio
frontend** (admin + user portal), **VS Code Extension (100% thin client)**, ছোট `tools/mobile`
(Flutter) ও `tools/desktop` (Electron) client, এবং **$0-cost** infra (Render + Firebase +
Supabase/pgvector + Redis + Infisical + Cloudflare)।

**যা সম্পন্ন (Done):**
- Stabilization Gate বন্ধ (10টি P0/P1 blocker ফিক্সড, কোড-লেভেল ভেরিফাইড)।
- CI 11 → 6 workflows, 100% SHA-pinned actions (0 `@v`)।
- Tier-0 Fast-Path, Skill Validation, Multi-Needle Retrieval, Scalable Agent Orchestration
  (চারটি Needle-2 feature) implemented + টেস্টেড (24/24, 14/14, 46/46)।
- RBAC bypass, WS token leak, PII/OTP log leak, brand direct-call fix সম্পন্ন।
- Type-gen pipeline (Pydantic → TS/Dart) deterministic বানানো হয়েছে।
- Admin Session Restore + Skills Tab 405 Fix — 3টি frontend/backend bug ফিক্সড (session restore via JWT
  exp-check, apiInterceptor auto-logout scoped to `/api/admin`+`/api/skills` paths, GET `/skills/search`
  endpoint যোগ)। Hard Test: Playwright E2E login→OTP→dashboard ✅।
- OpenAPI drift gate CI job যোগ + Render-এ ~90 env key reconciled (env drift gate live)।
- **Phase 0 M0.2 Store Consolidation (100% Done):** ৯টি ফ্র্যাগমেন্টেড Zustand স্টোর একীভূত করে
  `useSupremeStore` স্লাইস প্যাটার্নে একত্রিত করা হয়েছে (`dashboardSlice`, `customerSlice`,
  `sessionCockpitSlice`, `ideSlice`, `coreSlice`, `authSlice`, `adminSlice`, `workspaceSlice`,
  `workspaceSettingsSlice`), এবং পুরোনো ৯টি স্টোর ফাইলকে backward-compatible shim বানানো হয়েছে।
  Frontend Vite build 0 errors, ESLint 0 errors 0 warnings, Vitest 72/72 tests passing ✅।
- **Phase 0 M0.3 Realtime Swarm & WS Bridge (100% Done):** `SwarmPubSub` ও `realtime_dashboard.py`
  ব্রিজের জন্য ডেডিকেটেড টেস্ট স্যুট `backend/tests/api/test_realtime_dashboard.py` (4/4 passed) ✅।
- **Phase 1 M1.1 Dependencies Unification (100% Done):** `backend/api/dependencies.py` সেন্ট্রাল DI layer হিসেবে অ্যাক্টিভ।
- **Phase 1 M1.2 Structured Error Handling & Logging (100% Done):** API রাউটগুলোতে থাকা জেনেরিক
  `except Exception:` ব্লকগুলো নির্দিষ্ট ডোমেন এক্সেপশন (`jwt.PyJWTError`, `json.JSONDecodeError`)
  ও স্ট্রাকচার্ড লগিং দিয়ে সুরক্ষিত করা হয়েছে (`auth.py`, `admin_auth.py`, `simulator.py`, `byoc_api.py`,
  `cdc_webhooks.py`, `tenant_admin.py`, `session_takeover.py`) ✅।
- **Phase 1 M1.3 Memory Layer Encapsulation (100% Done):** `backend/memory/__init__.py` সেন্ট্রাল এক্সপোর্ট,
  `UnifiedDBManager` (`delete_record`, `health_check`), `sqlite_store.py` KV storage, `cloud_postgres_store.py`
  অফলাইন রেজিলিয়েন্স এবং `test_unified_db_manager.py` (15/15 memory tests passed) ✅।
- **Phase 1 M1.4 & M2.3 Database Indexing & Alembic CI Gate (100% Done):** হট-পাথ ইনডেক্সিং (`api_keys`, `api_key_events`, `system_alerts`, `code_proposals`), `api_key_tables.py` অটোমেটেড ইনিশিয়ালাইজেশন এবং GitHub Actions CI পাইপলাইনে `alembic upgrade head --sql` স্কিমা ড্রাফট প্রিভেনশন গেট যুক্ত করা হয়েছে ✅।
- **Phase 1 M1.5 & M1.6 Hygiene & Tracking (100% Done):** `tools/vscode-extension/` ডিরেক্টরিতে ০টি মৃত `.java`
  ফাইল নিশ্চিত এবং `docs/audit_reports/AUDIT_FIX_TRACKER.md` তৈরি সম্পন্ন।
- **Phase 2 M2.1 Frontend Code-Splitting & Granular Chunking (100% Done):** `vite.config.ts`-এ ডায়নামিক ভেন্ডর চাঙ্কিং (`vendor-react`, `vendor-motion`, `vendor-icons`, `vendor-charts`, `vendor-flow`, `vendor-firebase`) এবং `App.tsx`-এ অন-ডিমান্ড `React.lazy` রাউটিং যুক্ত করে ইনিশিয়াল এন্ট্রি বান্ডেল ৩৯৬.৯৭ kB থেকে ৬৫.৬৭ kB (gzip: ২২.৪৫ kB)-এ নামিয়ে **৮৩% সাইজ রিডাকশন** অর্জন করা হয়েছে। Vitest স্যুট ১০০% পাসিং (৭২/৭২) ✅।
- **Phase 2 M2.2 WebSocket Delta Stream Engine (100% Done):** `DashboardWebSocketManager`-এ `compute_metric_delta` ইঞ্জিন সংযুক্ত করে লাইভ মেট্রিক্সের ডেল্টা স্ট্রিমিং ও ব্যান্ডউইথ অপটিমাইজেশন সম্পন্ন ✅।
- **Infisical & Boot Resilience (100% Done):** `scripts/check_env_health.py`-এ Machine Identity ভ্যালিডেশন এবং `backend/main.py`-এ লগিং প্রায়োরিটি ও এন্ট্রি পয়েন্ট টেস্ট (`backend/tests/test_main_entrypoint.py`) সম্পন্ন ✅।
- **Phase 3 M3.1 Full Backend Test Coverage Expansion (100% Done):** `test_public_and_preferences.py`, `test_byoc_and_cloud_mesh.py`, `test_core_resilience_and_guards.py` স্যুট তৈরি, মিসিং `cdc_webhooks` রাউটার ইন্টিগ্রেশন এবং ৫৭৬টি ব্যাকএন্ড ইউনিট/ইন্টিগ্রেশন টেস্ট (৫৭৬ Passed, ০ Failed) নিশ্চিত করা হয়েছে ✅।
- **Phase 5 AI Evolution Blueprints (100% Done):** `BLUEPRINT-SELF-EVOLVING-MEMORY.md` (`BLUEPRINT-MEM-001`)
  এবং `BLUEPRINT-CONTEXT-GRAPH-ORGANIZER.md` (`BLUEPRINT-GRAPH-002`) তৈরি ও রোডম্যাপে সংযুক্ত।

- **Phase 3 M3.2 E2E Integration & Synthetic Benchmark Scenarios (100% Done):** ডেমো এজেন্ট সোয়ার্ম (Swarm DAG, concurrency, circuit breaker trip/recovery), কস্ট গার্ড এক্সিড ব্রিচ সিমুলেশন (multi-tier budget caps, Redis fail-safe $0 cost degradation), এবং JIT OTP পূর্ণাঙ্গ লাইফসাইকেল ভ্যালিডেশন (multi-channel dispatch, email fallback, escalation token, brute-force lock, replay prevention) ইঞ্জিন, CLI রানার এবং Pytest/Vitest স্যুট সম্পন্ন ✅।
- **Phase 3 M3.5 Accessibility & Degraded-State UI Resilience (100% Done):** axe-core ও vitest-axe স্বয়ংক্রিয় এক্সেসিবিলিটি অডিট স্যুট (LoginPage, RegisterPage, QuickPresets, DashboardShell, ChatPanel - ০টি ভায়োলেশন) এবং ৫০৩ ডাউনটাইম, ৪০২ কস্ট গার্ড লিমিট, ৪২৯ থ্রটলিং ও ২০২ JIT-OTP ইন্টারসেপশনের জন্য ডেডিকেটেড ডিগ্রেডেড-স্টেট রেজিলিয়েন্স টেস্ট (১৩/১৩ টেস্ট ফাইল, ৮৯/৮৯ টেস্ট পাস) নিশ্চিত করা হয়েছে ✅।

**যা চলছে / পরবর্তী ফোকাস:**
- Phase 4: Production Polish & CI/CD Staging Gate verification.

---

## 2. Current Architecture (বর্তমান আর্কিটেকচার)

### 2.1. Deployment Topology (Monorepo, $0 cost)
```
Render (Web Service, Poetry/Docker)  → supremeai-backend (FastAPI + ASGI)
Render (Static Site)                 → supremeai-frontend (Vite build)
Firebase Hosting (2 targets)         → app + admin
Supabase (PostgreSQL + pgvector)     → app DB + AI vector memory (ai_memory)
Upstash/Redis                        → cache, PubSub, rate-limit
Infisical Vault                      → secrets
Cloudflare Workers / Firebase        → edge cache, pings
```

### 2.2. Backend (Python 3.11 / FastAPI)
| Layer | ফাইল / ফোল্ডার | কথা |
|---|---|---|
| Entry | `backend/main.py`, `core/app.py`, `core/app_builder.py` | env bootstrap, graceful shutdown, lazy app factory |
| Config | `core/config*.py`, `core/universal_rules.py`, `core/feature_flags.py` | Pydantic Settings, secrets, global rules (~24KB) |
| Routing | `api/routers.py`, `api/routes/` (85 files incl. __init__), `api/v1/` | 318+ routes |
| Security | `core/security/*`, `core/cost_guard.py`, `core/autonoguard_engine.py` | JWT/RBAC, cost enforcement, anti-hacking |
| LLM | `core/llm_gateway.py`, `core/advanced_model_router.py`, `services/llm/` | LiteLLM multi-provider, tier-0 fast-path, semantic cache |
| Memory | `memory/` → `__init__.py`, `unified_db_manager`, `supabase_store`, `sqlite_store`, `cloud_postgres_store`, `chromadb_store`, `rag_pipeline` | Encapsulated unified vector & relational matrix |
| Agents | `agents/` (autonomous_agent, sentinel, insight_mage, churn_prophet, ...) | specialized agent catalog |
| Engine | `engine/` (smart_router, tree_of_thought, debate_engine, cost_optimizer, tool_forge, ...) | reasoning/evolution |
| Workers | `workers/` (celery_app, chaos_worker), `queue/task_router.py` | background tasks |
| DB | `models/` (SQLAlchemy), `alembic/`, `db_repository.py` | ORM + migrations |

### 2.3. Frontend (React 19 / Vite 7 / TypeScript strict)
- **Portals:** admin (`VITE_PORTAL_TYPE=admin`) + user (`user`), same package.
- **Command Center:** `src/commandcenter/` — kit (UI primitives) + modules
  (observe, operate, build, secure, money, system, deck). সব P0–P9 module built।
- **State:** Unified `useSupremeStore` (12 slices in `src/store/slices/`) — legacy 9 store files
  are 100% transparent backward-compatible shims.
- **Data:** React Query (queryClient), axios + apiInterceptor, services/ সুইট
  (admin, agent, auth, chat, skills, storage, sandbox, ...)।
- **Realtime:** `services/realtime/WebSocketManager.ts`, SSE bridges, SwarmProvider।

### 2.4. Clients (Thin Client Philosophy)
- **VS Code Extension** (`tools/vscode-extension/`) — providers/services AI routing শুধু backend-এর
  মাধ্যমে; কোনো 3rd-party LLM key client-এ নেই (OpenRouter fallback রিমুভড)। 0 dead Java files in active workspace.
- **Mobile (Flutter)** (`tools/mobile/` — thin client; direct Gemini call রিমুভড, এখন backend route-এর মাধ্যমে)।
- **Desktop (Electron)** (`tools/desktop/` — thin client electron wrapper)।

---

## 3. Key Functionalities (মূল ফিচারসমূহ)

| Area | Functionality |
|---|---|
| AI Orchestration | Multi-provider LLM routing (LiteLLM), Tier-0 deterministic fast-path, semantic cache, model failover, cost guard |
| Eternal Brain | pgvector vector memory, RAG pipeline, episodic + long-term memory, multi-needle contextual retrieval, Self-Evolving Memory |
| Agent System | Autonomous agent, sentinel, specialized agent catalog, parallel executor, skill management, Trio 2.0 Swarm |
| Developer Platform | VS Code extension (chat, code review, code gen, security scan, self-healing), sandbox (microvm/docker), byoc, code validator |
| Admin Command Center | Live metrics, logs, events, health map, traffic monitor, agents/tasks/sessions/tenants, model router UI, cost/billing, security/audit, approvals, config, feature flags, backups, deploy gate, Brain Visualizer |
| User Portal | Chat/streaming, sessions, voice, media, files (tenant-scoped), skills marketplace |
| Business/Billing | Stripe payments, billing plans, usage/cost reporting, escrow, wallet, transaction ledger |
| Autonomy/Evolution | Auto-healer, auto-remediation, feedback loop, self-reflection, evolution pipeline, cost optimizer, debate engine |
| Observability | Health checks, OpenTelemetry, telemetry, error bus/remediation, CI report ingestion |
| Security | JWT/RBAC, anti-hacking, honeypot, prompt firewall, SSRF guards, secrets vault, rate limits, audit log, OTP/JIT approval |

---

## 4. Technical Debt Inventory (প্রমাণ-ভিত্তিক)

### 🔴 P1 — ক্রিটিক্যাল debt (রোডম্যাপে আগে ফিক্স)
1. **Secrets rotation অসম্পূর্ণ + Render-এ ~90 important/optional key missing** — CI gate pass
   করছে কিন্তু production feature degrade (KNOWN_ISSUES P1)।
2. **Infisical Universal Auth 401** — `verify_infisical_env.py` এখন INFISICAL_TOKEN fallback-এ
   চলে; machine identity আসলে register করা হয়নি।
3. **Full backend test suite CI-তে রান ও ভেরিফিকেশন** — 376টি test file।

### 🟠 P2 — Medium debt
4. **Hot-Path DB Index Deployment** — `2026_08_19_000000_add_performance_indexes.py` migration live environments-এ verify করা।

---

## 5. Development Roadmap (অগ্রাধিকারভিত্তিক Phases)

> **একটি গাইডিং নীতি (Per AGENTS.md):** প্রতিটি phase শেষে `LESSONS_LEARNED.md`,
> `CHECKPOINT.md`, `FEATURE_TRACKING_LOG.md` / `REAL_TESTING_LOG.md` আপডেট করতে হবে
> (বাংলায়), এবং যেকোনো fix "Hard Test" (real API + log + browser) দিয়ে verify করতে হবে।
> Zero-repeat-error, atomic commit, no-drift policy মেনে কাজ হবে।

---

### Phase 0 — Foundation Completion (Command Center Live) | 🎯 (✅ 100% COMPLETE)

**লক্ষ্য:** Phase-0 (Command Center & State Consolidation) সমাপ্ত।

**Milestones:**
- M0.1: Admin Command Center live endpoints connected & verified (Brain Visualizer, Live Logs, Metrics, Events SSE) ✅
- M0.2: 9 Zustand Stores Consolidation into unified `useSupremeStore` via slice pattern with backward-compatible shims (Vite build 0 errors, ESLint 0 errors 0 warnings, Vitest 72/72 passed) ✅
- M0.3: SwarmPubSub → WebSocket/SSE bridge verified (`test_realtime_dashboard.py` 4/4 passed) ✅
- M0.4: Render OpenAPI drift gate CI job live + env keys reconciled ✅
- M0.5: Admin Dashboard backend test suites green (48/48 passed) ✅

---

### Phase 1 — Technical Debt Reduction & Refactoring | 🎯 (✅ CORE COMPLETE)

**লক্ষ্য:** Duplication/legacy cleanup, docs ↔ code sync, error-handling standardization, memory layer encapsulation।

**Milestones:**
- M1.1: `backend/api/dependencies.py` একীভূত ও সেন্ট্রাল DI layer হিসেবে নিশ্চিত ✅
- M1.2: Bare `except Exception:` → typed exceptions (`jwt.PyJWTError`, `json.JSONDecodeError`) + structured logging routes-এ সম্পন্ন ✅
- M1.3: `memory/` unified manager (`unified_db_manager.py`) encapsulation, package exports (`__init__.py`), KV persistence & health check (15/15 memory tests passed) ✅
- M1.4: OpenAPI spec auto-generate commit + **CI drift gate** (app.openapi() vs committed spec) ✅
- M1.5: VS Code extension dead Java files cleanup (0 dead Java files in active workspace) ✅
- M1.6: `docs/audit_reports/AUDIT_FIX_TRACKER.md` তৈরি ও ৪-এজেন্ট প্রটোকলে ট্র্যাক ✅

---

### 🟡 P3 — Low-priority / Housekeeping
- **Mobile (Flutter) + Desktop (Electron)** — `tools/mobile/` এবং `tools/desktop/` ক্লায়েন্টকে Thin Client ফিলোসফি অনুযায়ী backend-এ কানেক্ট করা। *(Phase 4-এ শিডিউলড)*
- **Accepted-risk CVEs** — `ecdsa` (upstream fix নেই) ও LiteLLM python cap; অডিট সাইকেলে নিয়মিত চেক।

---

### Phase 2 — Performance & Scalability Engineering | 🎯 3–4 weeks

**লক্ষ্য:** Frontend deliverability + backend throughput/latency, Zero-cost পরিসীমায়।

**Milestones:**
- M2.1: Frontend code-splitting (React.lazy per module), tree-shaking, bundle <250KB gz
  initial / <900KB gz total। (~2d)
- M2.2: Large lists virtualization (extend DataTable to all >50-row tables); **WS payload
  diffing (2s delta streaming implemented via `compute_metric_delta`)** ✅
- M2.3: Backend query optimization & Migration Gate — 6 Alembic migrations verified, hot-path indexes (`api_keys`, `api_key_events`, `system_alerts`) added & **`alembic upgrade head --sql` CI verification gate active** ✅
- M2.4: Async/queue hardening — task route, circuit breakers, retry with exponential
  backoff, DB connection pooling (asyncpg + pgbouncer)। (~3d)
- M2.5: Uvicorn boot resilience & entrypoint test — logging priority, graceful shutdown & `test_main_entrypoint.py` (4/4 passed) ✅
- M2.6: Lightweight load test (scripts/Playwright) — RPS, p95, error-rate regression guard। (~1d)

**Technical requirements:** Vite build-analyze tooling, `@tanstack/react-virtual`, Redis
(Upstash/Render), SQLAlchemy query profiling, pgvector tuning, `uvicorn --workers` +
import-string (already), optional k6-as-script (workflow নয়)।

**Risks & mitigations:**
- ⚠️ Index/DDL changes on Supabase free tier → timing + cost cap; off-peak + rollback
  migration (alembic)।
- ⚠️ WS diffing bug → stale UI → degraded-state fallback + snapshot refresh guard।
- ⚠️ Multi-worker in-memory state inconsistency → Redis-backed shared store; enable
  only when needed।

**Exit criteria:** Load test stable p95 নন free-tier quota ছাড়া; bundle targets met; cache
hit-rate measurable; zero regressions in full suite।

---

### Phase 3 — Test, Observability & Reliability Hardening | 🎯 2–3 weeks

**লক্ষ্য:** Confidence বাড়ানো — coverage, e2e, observability, failover।

**Milestones:**
- M3.1: Backend coverage → **80% target** (baseline ~15% / 244 pass + 2 skip, 373 test files); CI coverage gate। (~4d)
- M3.2: High-value integration/e2e — auth→OTP→deck→module, session streaming, cost guard
  hard test, admin login (Playwright)। (~3d)
- M3.3: OpenTelemetry standardized logging/tracing; error bus full telemetry events। (~2d)
- M3.4: Reliability plane — provider failover chain, circuit breaker for external deps,
  rollback monitor, chaos tests। (~2d)
- M3.5: axe-core accessibility (0 known) + degraded-state (WS/SSE fail) UI tests। (~1d)

**Technical requirements:** pytest-cov, Playwright config/trace, OpenTelemetry FastAPI
instrumentation (already dep), feature flags, REAL_TESTING_LOG tracking।

**Risks & mitigations:**
---

### Phase 4 — Multi-Client Distribution (Thin Clients) | 🎯 2–3 weeks
*(Prerequisite: Phase 0/Foundations; per one-mega-feature rule)*

**Milestones:**
- M4.1: Electron desktop live wiring — backend REST/WS; reuse shared React components
  (`packages/ui-components`). (~2d)
- M4.2: VS Code extension production hardening — OAuth flow, streaming reliability,
  self-healing coverage. (~2d)
- M4.3: Mobile thin client — backend base-url env handling, remove residual direct AI
  call, WS auth-handshake standardization. (~1–2d)

**Technical requirements:** `packages/ui-components` reuse, `dotenv`/config per client,
same JWT auth surface, versioned API-contract verification.

**Risks & mitigations:**
- ⚠️ Client-scope creep → hold each client to thin-client protocol.
- ⚠️ Desktop cross-platform packaging drift → CI release builds (supreme-release-builds.yml)।

**Exit criteria:** Desktop + mobile + extension run against live backend; zero 3rd-party AI
key on any client; brand-exclusive UX।

---

### Phase 5 — AI Evolution & Platform Scale | 🎯 3–5 weeks (long-term, sequential)

**লক্ষ্য:** Eternal Brain growth, agent orchestration scale, multi-tenancy, cost optimization।

**Core Blueprints:**
- 📜 [BLUEPRINT-SELF-EVOLVING-MEMORY.md](file:///f:/supremeai%20backup/docs/architecture/BLUEPRINT-SELF-EVOLVING-MEMORY.md) — Semantic Clustering, Deduplication & Decay for pgvector ($0 Cost).
- 📜 [BLUEPRINT-CONTEXT-GRAPH-ORGANIZER.md](file:///f:/supremeai%20backup/docs/architecture/BLUEPRINT-CONTEXT-GRAPH-ORGANIZER.md) — Entity Graph Matrix connecting Sessions, Agents, Skills & BrainVisualizer.

**Milestones:**
- M5.1: Self-Evolving Memory Storage — knowledge→self-training loop, semantic clustering, auto-deduplication, access decay (pgvector store hardening per BLUEPRINT-MEM-001)। (~3w)
- M5.2: Context Graph Engine & Brain Visualizer Bridge — multi-hop context reasoning, dynamic graph API & visualizer sync per BLUEPRINT-GRAPH-002; parallel executor & skill auto-generation। (~2w)
- M5.3: Multi-tenancy isolation scale — per-tenant quota, rate-limit, audit, row-level security। (~2w)
- M5.4: Cost optimization — semantic-cache hit-rate target, Tier-0 broaden, cost-quality
  routing tuning। (~1w)

**Risks & mitigations:**
- ⚠️ P2P/federated training তাত্ত্বিকভাবে $0-tier-এ অসম্ভব (feasibility audit) →
  **vector-guided evolution** ব্যবহার।
- ⚠️ Self-modifying code → hard gates + approved-only mutation (anti-hacking default on)।

**Exit criteria:** Memory auto-ingestion measurable; swarm/orchestration load-tested; tenant
isolation audit clean; cost/hr trend down।

---

## 6. Dependency / Sequencing Map

```
Phase 0 (Foundation) ──► Phase 1 (Refactor) ──► Phase 2 (Performance)
      │                                                   │
      └─────────────┬─────────────────────────────────────┘
                    ▼
           Phase 3 (Reliability) ──► Phase 4 (Clients) ──► Phase 5 (AI Evolution)
```

**Key dependency:** Phase 0 ও Phase 1 atomic commits দিয়ে overlap করা যায়; Phase 2
(perf) Phase 3 (reliability)-এর নম্বর আগে নয়। Phase 5 strictly last (no scope split)।

---

## 7. Success Metrics & Definition of Done

| Metric | কারেন্ট | Phase 0 target | Final Production Target |
|---|---|---|---|
| Backend suites in CI | আংশিক (244 pass + 2 skip, 373 test file) | Full green | 80%+ coverage |
| Admin mock data | ~70% | 0% | 0% |
| Zustand stores | 9 files (2 consolidated) | 1 unified | 1 unified |
| CI workflows | 6 (SHA-pinned) | stay green | green + E2E |
| Bundle (initial gz) | baseline | <250KB | <250KB |
| Cost | $0 | $0 | $0 |
| Docs/spec drift | CI gate live (M1.4 done) | CI gate | CI gate |

---

## 8. Immediate Next Steps (7 Tasks)

1. **M0.4** — Render missing keys + Infisical 401 (prod-health visibility) — *(আংশিক: env drift gate live,
  but 90 keys still missing + Infisical 401 active per KNOWN_ISSUES)*
2. **M0.1** — wire highest-traffic admin panel (Command Deck) to live endpoint — *(আংশিক: Admin Session
  Restore + Skills 405 fix সম্পন্ন; মোক panels এখনো বাকি)*
3. **M0.2** — consolidate remaining 6 stores into `useSupremeStore` — *(2টি সম্পন্ন: themeStore deleted,
  useWorkspaceSettingsStore merged; 6টি API-shape mismatch জন্য deferred)*
4. **M0.3** — bridge SwarmPubSub→WebSocket for live logs/metrics — *(pending)*
5. **M0.5** — quarantine + fix flaky backend tests; full suite green in CI — *(pending; 373 test file)*
6. **M2.3** — add missing DB indexes (alembic, 6 versions exist) for top query paths — *(pending)*
7. ✅ **M1.4** — OpenAPI + type-gen drift CI gate — **DONE** (drift gate CI job live)

---

*Generated: 2026-08-19 | Next review: end of Phase 0 | Owner: Principal AI Engineer (monorepo)*
- ⚠️ Coverage gate blocking merging → start "fail-on-degradation" slow (warning → hard)।
- ⚠️ Flaky E2E in CI → retry policy + trace artifacts + quarantine list।
- ⚠️ Over-instrumenting → payload/overhead → sampled telemetry।

**Exit criteria:** Coverage 80%+; E2E suite stable green; key reliability tests passing;
observability dashboards live; axe 0 issues।

---
14. **Repo hygiene** — root-এ `.secrets/` (allowlisted), `.venv_ci`, `__pycache__`, `.coverage`,
    `htmlcov`, `playwright-report/`, `test-results/`, `.mypy_cache/`, `.ruff_cache/` ইত্যাদি
    artifact; `.gitignore` + cleanup (M1.6) দরকার। ২২টি dead Java file (tools/vscode-extension/) cleanup।
15. **Frontend bundle/quality gates absent** — code-splitting (✅ via `WorkspaceViewport.tsx`
    `React.lazy`), virtualization (`@tanstack/react-virtual` যোগ দরকার), WS payload
    diffing, axe-core, Playwright smoke (implementation_plan.md রেফারেন্স)।

---