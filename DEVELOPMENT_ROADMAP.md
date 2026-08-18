# SupremeAI 2.0 — Comprehensive Development Roadmap
> **Date:** 2026-08-19
> **Status:** Active — Phase 0/Phase 1 (Command Center Live + Technical Debt Reduction) in progress
> **ভাষা:** Bangla/Banglish (Simple Language); headers English

---

## 1. Executive Summary (কারেন্ট অবস্থা)

SupremeAI 2.0 হলো একটি **self-learning AI infrastructure** (Universal Agent Platform) যার
কোর আর্কিটেকচার এখন solid: unified **FastAPI backend (~318 routes)** + **React/Vite Studio
frontend** (admin + user portal), **VS Code Extension (100% thin client)**, ছোট `apps/mobile`
(Flutter) ও `apps/desktop` (Electron) client, এবং **$0-cost** infra (Render + Firebase +
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
- Zustand store consolidation সেশন ১: `themeStore` ডিলিট (0 consumers); `useWorkspaceSettingsStore` →
  `useWorkspaceStore`-এ ম্যার্জ (toggleIntegration syncs `activeIntegrations` + `integrations[].enabled`)।
  Store count 11 → 9।

**যা চলছে / বাকি (এই রোডম্যাপে অ্যাড্রেস করা হয়েছে):**
- Command Center-এর mock panels → real backend data মাইগ্রেশন।
- 6টি বাকি Zustand store consolidation (API-shape mismatch এজন্য deferred);
  2টি সম্পন্ন (themeStore deleted, useWorkspaceSettingsStore merged)।
- SwarmPubSub → WebSocket/SSE real-time bridge।
- Full backend test suite CI-তে রান করা (আংশিক; 373 test file, 244 passed + 2 skip,
  `test_headless_terminal_agent.py` = FF)।
- Secrets rotation অসম্পূর্ণ + Render-এ ~90 important/optional key missing।
- একাধিক কোড-কোয়ালিটি debt (ডুপ্লিকেট module, bare `except`, memory store ভগ্ন)।

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
| Routing | `api/routers.py`, `api/routes/` (84 file), `api/v1/` | 318+ route |
| Security | `core/security/*`, `core/cost_guard.py`, `core/autonoguard_engine.py` | JWT/RBAC, cost enforcement, anti-hacking |
| LLM | `core/llm_gateway.py`, `core/advanced_model_router.py`, `services/llm/` | LiteLLM multi-provider, tier-0 fast-path, semantic cache |
| Memory | `memory/` → supabase_store, sqlite_store, chromadb_store, cloud_postgres_store, unified_db_manager, rag_pipeline | vector memory (pgvector) |
| Agents | `agents/` (autonomous_agent, sentinel, insight_mage, churn_prophet, ...) | specialized agent catalog |
| Engine | `engine/` (smart_router, tree_of_thought, debate_engine, cost_optimizer, tool_forge, ...) | reasoning/evolution |
| Workers | `workers/` (celery_app, chaos_worker), `queue/task_router.py` | background tasks |
| DB | `models/` (SQLAlchemy), `alembic/`, `db_repository.py` | ORM + migrations |

### 2.3. Frontend (React 19 / Vite 7 / TypeScript strict)
- **Portals:** admin (`VITE_PORTAL_TYPE=admin`) + user (`user`), same package.
- **Command Center:** `src/commandcenter/` — kit (UI primitives) + modules
  (observe, operate, build, secure, money, system, deck). সব P0–P9 module built, কিন্তু
  data এখনো অনেক জায়গায় mock/hardcoded।
- **State:** একাধিক Zustand store — `useSupremeStore` (520 lines), `adminStore`, `authStore`,
  `dashboardStore`, `customerStore`, `sessionCockpitStore`,
  `useWorkspaceStore`, `useIdeStore`, `useStore`। (`themeStore` ডিলিট,
  `useWorkspaceSettingsStore` → `useWorkspaceStore`-এ ম্যার্জ করা হয়েছে — 11 → 9 stores)。
- **Data:** React Query (queryClient), axios + apiInterceptor, services/ সুইট
  (admin, agent, auth, chat, skills, storage, sandbox, ...)।
- **Realtime:** `services/realtime/WebSocketManager.ts`, SSE bridges, SwarmProvider।

### 2.4. Clients (Thin Client Philosophy)
- **VS Code Extension** (`tools/vscode-extension/`) — providers/services AI routing শুধু backend-এর
  মাধ্যমে; কোনো 3rd-party LLM key client-এ নেই (OpenRouter fallback রিমুভড)। ⚠️ root-এ
  dead **Java** files (`AdminMetricsController.java` ইত্যাদি, 22টি) পড়ে আছে → M1.5 cleanup দরকার।
- **Mobile (Flutter)** (`tools/mobile/` — root এ `apps/mobile/` ছিল, সরিয়ে নেওয়া হয়েছে) — খুব thin;
  direct Gemini call রিমুভড, এখন backend route-এর মাধ্যমে। Overall আর্কাইভ-কাছাকাছি।
- **Desktop (Electron)** (`tools/desktop/` — root এ `apps/desktop/` ছিল, সরিয়ে নেওয়া হয়েছে;
  `frontend/main.js` + `preload.cjs`) — `electron:build` script + electron-builder config আছে;
  live backend REST/WS wiring প্রায় না থাকায় partial।
- **Apps directory** — `apps/` ফোল্ডার বর্তমানে খালি; mobile/desktop client `tools/`-এ সরিয়ে নেওয়া হয়েছে।

---
---

## 3. Key Functionalities (মূল ফিচারসমূহ)

| Area | Functionality |
|---|---|
| AI Orchestration | Multi-provider LLM routing (LiteLLM), Tier-0 deterministic fast-path, semantic cache, model failover, cost guard |
| Eternal Brain | pgvector vector memory, RAG pipeline, episodic + long-term memory, multi-needle contextual retrieval |
| Agent System | Autonomous agent, sentinel, specialized agent catalog (insight_mage, churn_prophet, vulnerability_prophet), parallel executor, skill management |
| Developer Platform | VS Code extension (chat, code review, code gen, security scan, self-healing), sandbox (microvm/docker), byoc, code validator |
| Admin Command Center | Live metrics, logs, events, health map, traffic monitor, agents/tasks/sessions/tenants, model router UI, cost/billing, security/audit, approvals, config, feature flags, backups, deploy gate |
| User Portal | Chat/streaming, sessions, voice, media, files (tenant-scoped), skills marketplace |
| Business/Billing | Stripe payments, billing plans, usage/cost reporting, escrow, wallet, transaction ledger |
| Autonomy/Evolution | Auto-healer, auto-remediation, feedback loop, self-reflection, evolution pipeline, cost optimizer, debate engine |
| Observability | Health checks, OpenTelemetry, telemetry, error bus/remediation, CI report ingestion |
| Security | JWT/RBAC, anti-hacking, honeypot, prompt firewall, SSRF guards, secrets vault, rate limits, audit log, OTP/JIT approval |

---

## 4. Technical Debt Inventory (প্রমাণ-ভিত্তিক)

### 🔴 P1 — ক্রিটিক্যাল debt (রোডম্যাপে আগে ফিক্স)
1. **Mock/hardcoded dashboard data** — admin Command Center-এর অনেক panel এখনো mock
   (REAL_TESTING_LOG-এ ডকুমেন্টেড: dead props `gcpHealth`/`cloudStats`, mock Deploy/
   Report/Restart buttons, hardcoded CPU 42%/Mem 68% ইত্যাদি)।
2. **Secrets rotation অসম্পূর্ণ + Render-এ ~90 important/optional key missing** — CI gate pass
   করছে কিন্তু production feature degrade (KNOWN_ISSUES P1)।
3. **Infisical Universal Auth 401** — `verify_infisical_env.py` এখন INFISICAL_TOKEN fallback-এ
   চলে; machine identity আসলে register করা হয়নি।
4. **Full backend test suite CI-তে শেষ হয়নি** — 373টি test file; চলতি রানে interruptions
   (কিছু FF), task_router-এর কোভারেজ একসময় 0% ছিল।

### 🟠 P2 — Medium debt
5. **একাধিক Zustand store** — ৯টি store file (`themeStore` deleted, `useWorkspaceSettingsStore`
   merged into `useWorkspaceStore`); উল্লেখযোগ্য duplication + inconsistent state।
6. **Duplicate/parallel modules** — `backend/core/app.py` vs `app_builder.py` (ভালো, কিন্তু
   confusion); `backend/api/deps.py` (36 lines) vs `dependencies.py` (172 lines) ফাংশনালি
   overlapped; `memory/`-এ chroma/sqlite/supabase/cloud_postgres store আলাদা।
---

## 5. Development Roadmap (অগ্রাধিকারভিত্তিক Phases)

> **একটি গাইডিং নীতি (Per AGENTS.md):** প্রতিটি phase শেষে `LESSONS_LEARNED.md`,
> `CHECKPOINT.md`, `FEATURE_TRACKING_LOG.md` / `REAL_TESTING_LOG.md` আপডেট করতে হবে
> (বাংলায়), এবং যেকোনো fix "Hard Test" (real API + log + browser) দিয়ে verify করতে হবে।
> Zero-repeat-error, atomic commit, no-drift policy মেনে কাজ হবে।

---

### Phase 0 — Foundation Completion (Command Center Live) | 🎯 2–3 weeks

**লক্ষ্য:** চলমান Phase-1 (Command Center) শেষ করা — mock → real data, store একত্রীকরণ,
real-time bridge, এবং প্রতিটি P1 debt ফিক্স।

**Milestones:**
- M0.1: Admin Command Center-এর প্রতিটি module-এ backend endpoint সংযুক্ত; `grep`-এ
  0 mock/hardcoded value। (effort ~3d) *(অংশিক — Admin Session Restore + Skills 405 সম্পন্ন;
  `/api/chat/history` GET endpoint এখনো নেই)*
- M0.2: 9টি Zustand store → 1 unified `useSupremeStore` (slice pattern)। (effort ~2d)
  *(2টি সম্পন্ন: `themeStore` deleted, `useWorkspaceSettingsStore` merged; 6টি বাকি
  API-shape mismatch জন্য deferred)*
- M0.3: SwarmPubSub → WebSocket/SSE bridge লাইভ; <1s metric update। (effort ~2d) *(pending)*
- M0.4: Render-এ ~90 missing env key ভেরিফাই + populate; secrets rotation সম্পূর্ণ;
  Infisical machine identity register (401 মুছে)। (effort ~2d) *(আংশিক — env drift gate live,
  OpenAPI gate যোগ, কিন্তু Infisical 401 + full rotation বাকি)*
- M0.5: Full backend suite CI-তে green — flaky tests বিচ্ছিন্ন + retry/বাগ fix। (effort ~1.5d)
  *(373 test file, 244 passed + 2 skip; `test_headless_terminal_agent.py` = FF)*

**Technical requirements:**
- Frontend: React Query + `useSupremeStore` slices; `WebSocketManager.ts` + SSE bridges;
  Pydantic-derived TS types (type_gen pipeline)।
- Backend: `api/routes/commandcenter/*` endpoints (many exist), WS `command_center.py`,
  seeded supabase for admin metrics।
- Infra: Render env vars, Infisical vault machine identity, `secrets_registry.yaml`/allowlist sync।

**Risks & mitigations:**
- ⚠️ Live data exposure (mock-এ degraded UI) → phase gate-এ fallback `EmptyState` + degraded test।
- ⚠️ Store refactor breaks many consumers → atomic per-slice migration + affected-only tests।
- ⚠️ Render/secret key loss → live API verify (dead-ID fallback এড়ানো, LESSON recorded)।

**Exit criteria:** Admin dashboard 100% live; `grep -rn "useDashboardStore|useAdminStore"` → 0;
CI full suite green; secrets verified on live Render/Infisical; browser E2E (login→OTP→each module) pass।

---

### Phase 1 — Technical Debt Reduction & Refactoring | 🎯 2–3 weeks

**লক্ষ্য:** Duplication/legacy cleanup, docs ↔ code sync, error-handling standardization —
product behavior না বদলে maintainability বাড়ানো।

**Milestones:**
- M1.1: `backend/api/deps.py` vs `dependencies.py` একীভূত; একটি সুস্পষ্ট DI/overrides layer। (~1d) *(pending)*
- M1.2: Bare `except Exception:` → structured logging + `core.error_bus`/`error_remediation`-এ
  রুট; enforced by `ruff` rule। (~2d) *(pending — 4 clauses per CHECKPOINT)*
- M1.3: `memory/` store হিসেবে single manager (`unified_db_manager`) করে client
  select (pgvector/sqlite) encapsulate; dead chroma store deprecate। (~2d) *(pending)*
- M1.4: OpenAPI spec auto-generate commit + **CI drift gate** (app.openapi() vs committed
  spec) + Pydantic→TS/Dart auto-check। (~1–2d) *(✅ DONE — drift gate CI job live)*
- M1.5: VS Code extension থেকে dead Java files (22টি) সরানো; `.gitignore`/`.vscodeignore` সঠিক।
  `python-jose` → PyJWT migration (bonus)। (~1d) *(pending)*
- M1.6: Repo hygiene — `__pycache__`, htmlcov, `.coverage`, `.secrets/`, `.venv_ci`
  বিচ্ছেদ/ignore। (~0.5d)

**Technical requirements:** Ruff rule config, pytest for legacy-catch removal, PyJWT
migration tests, CI drift check step (deterministic gen), OpenAPI generation script।

**Risks & mitigations:**
- ⚠️ Refactor line-change → regression → full suite + affected gate обязателен।
- ⚠️ Memory-store abstraction → vector-dimension/embedding mismatch → seeded golden tests।
- ⚠️ Spec auto-gen diff noise → determinism (no timestamp headers) enforced (LESSON)।

**Exit criteria:** Duplicate modules gone; `except Exception:` count নাটকীয়ভাবে কম;
docs/spec in sync (drift gate green); repo clean; backend + frontend builds && tests green।

---
7. **Bare `except Exception:`** — অনেক স্থানে unstructured error handle; structured logging/
   error bus-এ মাইগ্রেট করা দরকার।
8. **API-swagger.yaml grossly incomplete** — শুধু `/health` documented (60+ routers-এর বিরুদ্ধে);
   OpenAPI drift gate নেই।
9. **Docs ↔ code drift** — cost_guard docstring-এ tier routing overstatement; type-gen
   determinism ঠিক হয়েছে কিন্তু CI auto-check এখনো নেই।
10. **VS Code extension root-এ dead Java files** — 22টি `.java` ফাইল → (M1.5) cleanup +
    `.gitignore`/`.vscodeignore` সঠিক। *(pending)*

### 🟡 P3 — Low-priority / housekeeping
11. **Mobile (Flutter) ও Desktop (Electron)** — মূলত un-wired; partial thin client।
12. **`python-jose` deprecated** → PyJWT migration banc (pyproject-এ commented TODO)।
13. **Accepted-risk CVEs** — `ecdsa` (no upstream fix), litellm python cap hack; প্রতিটি
    audit cycle-এ re-check।
---

### Phase 2 — Performance & Scalability Engineering | 🎯 3–4 weeks

**লক্ষ্য:** Frontend deliverability + backend throughput/latency, Zero-cost পরিসীমায়।

**Milestones:**
- M2.1: Frontend code-splitting (React.lazy per module), tree-shaking, bundle <250KB gz
  initial / <900KB gz total। (~2d)
- M2.2: Large lists virtualization (extend DataTable to all >50-row tables); WS payload
  diffing (2s delta, 30s full snapshot)। (~2d)
- M2.3: Backend query optimization — key-table indexing, pgvector index (IVFFlat/HNSW),
  N+1 elimination; Redis cache for hot read paths + semantic cache। (~3d)
- M2.4: Async/queue hardening — task route, circuit breakers, retry with exponential
  backoff, DB connection pooling (asyncpg + pgbouncer)। (~3d)
- M2.5: Uvicorn multi-worker (config-driven) + graceful shutdown verification; startup_time
  & p95 baseline। (~1d)
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
- M3.1: Backend coverage → **80% target** (baseline ~15% subset / 244 pass); CI coverage gate। (~4d)
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

**Milestones:**
- M5.1: Memory/intelligence — knowledge→self-training loop (memory write-back, style/pattern
  learning); pgvector store hardening। (~3w)
- M5.2: Agent orchestration scale — parallel executor, swarm (non-P2P), skill auto-generation। (~2w)
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
| Backend suites in CI | আংশিক (244 pass) | Full green | 80%+ coverage |
| Admin mock data | ~70% | 0% | 0% |
| Zustand stores | 11 files | 1 unified | 1 unified |
| CI workflows | 6 (SHA-pinned) | stay green | green + E2E |
| Bundle (initial gz) | baseline | <250KB | <250KB |
| Cost | $0 | $0 | $0 |
| Docs/spec drift | manual | CI gate | CI gate |

---

## 8. Immediate Next Steps (7 Tasks)

1. **M0.4** — Render missing keys + Infisical 401 (prod-health visibility)।
2. **M0.1** — wire highest-traffic admin panel (Command Deck) to live endpoint।
3. **M0.2** — consolidate top 3 stores into `useSupremeStore`।
4. **M0.3** — bridge SwarmPubSub→WebSocket for live logs/metrics।
5. **M0.5** — quarantine + fix flaky backend tests; full suite green in CI।
6. **M2.3** — add missing DB indexes (alembic) for top query paths।
7. **M1.4** — add OpenAPI + type-gen drift CI gate (prevents silent breaks)।

---

*Generated: 2026-08-18 | Next review: end of Phase 0 | Owner: Principal AI Engineer (monorepo)*
- ⚠️ Coverage gate blocking merging → start "fail-on-degradation" slow (warning → hard)।
- ⚠️ Flaky E2E in CI → retry policy + trace artifacts + quarantine list।
- ⚠️ Over-instrumenting → payload/overhead → sampled telemetry।

**Exit criteria:** Coverage 80%+; E2E suite stable green; key reliability tests passing;
observability dashboards live; axe 0 issues।

---
14. **Repo hygiene** — root-এ `.secrets/`, `.venv_ci`, `__pycache__`, `.coverage`, htmlcov
    ইত্যাদি artifact; `.gitignore` + cleanup দরকার।
15. **Frontend bundle/quality gates absent** — code-splitting, virtualization, WS payload
    diffing, axe-core, Playwright smoke বাকি (commandcenter TODO P9)।

---