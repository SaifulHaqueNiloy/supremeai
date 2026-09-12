


<!-- ============================================================ -->
<!-- Merged Source: docs/01-overview.md -->
<!-- ============================================================ -->

# 01 — Overview

## What SupremeAI Is

SupremeAI is an **autonomously orchestrated AI task-execution platform**. The repository describes itself as "SupremeAI 2.0 — Universal Self-Learning AI Agent": a governed, model-agnostic system designed to solve real user problems by discovering, composing, reusing and — only when genuinely necessary — creating capabilities. The same machinery that serves users is intended to operate, test, repair, learn from and safely improve SupremeAI itself.

The platform consists of a FastAPI backend (`backend/`, Poetry package `supremeai-backend` v2.0.0), a React 19 single-page application (`frontend/`, package `supremeai-studio-client` v2.0.0), five shared TypeScript packages (`packages/`), a VS Code extension (`tools/vscode-extension/`), an MCP Control Tower (`infrastructure/mcp-control-plane/`), a Docusaurus documentation site (`apps/docs/`), and an extensive operational toolbelt (`scripts/`, `tools/`).

Three ideas define the product:

1. **Capability before construction.** A new user request is not automatically a new engineering project. The system inspects its existing capability surface first.
2. **Provider sovereignty.** External LLM providers (Gemini, OpenAI, Groq, DeepSeek, OpenRouter, Ollama, Moonshot, Together, Hugging Face, NVIDIA) are replaceable processing engines behind adapters — never the identity of the system.
3. **Zero-cost posture.** The entire deployment strategy is engineered around free tiers (Render free instances, Supabase, Firebase Hosting, Cloudflare Workers, Upstash) with explicit quota guards and keep-alive automation.

## The Constitution

The root README codifies eleven governing principles. They are worth knowing because they explain *why* the code is structured the way it is:

| # | Principle | Meaning in code |
|---|-----------|-----------------|
| 1 | Eternal Brain | Durable identity accumulates in memory/learning systems (`backend/memory/`, `backend/learning/`), not in any single LLM provider |
| 2 | Capability Sovereignty | Capabilities are composable and replaceable; provider details live behind adapters (`backend/services/llm/providers.py`) |
| 3 | Reuse Before Creation | Discover → Reuse → Compose → Adapt → Extend → Create; enforced by `core.orchestration.Orchestrator` and the capability registry |
| 4 | Dynamic Discovery | Prefer registries and runtime metadata over hard-coded inventories (`core/agent_registry.json`, ecosystem `capability_registry`) |
| 5 | Verification Before Trust | Generate → Execute → Verify → Trust; unverified results are not "done" (`backend/verification/`, health checks, self-healer) |
| 6 | Policy Before Power | Observe → Analyze → Risk → Permission → Approval → Act → Verify → Audit (`ecosystem/governance`, `ecosystem/approval_workflow`, HITL WebSocket) |
| 7 | Reversible Evolution | Autonomous changes preserve evidence, tests, risk assessment and rollback (`tools/autonomy/tools/deploy_guard.py`, `agent_change_budget.py`) |
| 8 | Graceful Degradation | A single provider/account failure must not destroy the task (circuit breakers, fallback chains, `SUPABASE_ALLOW_DB_DEGRADATION`) |
| 9 | Provider Agnostic, User Loyal | Users ask for outcomes; the provider stack may change invisibly (litellm gateway with per-task model maps) |
| 10 | One System, Many Execution Surfaces | Web app, VS Code extension, MCP servers, workers and microservices share one task/capability machinery with different scopes (`SUPREMEAI_SERVICE_ROLE`) |
| 11 | Memory Must Compound | Task → Result → Experience → Memory → Better Future Planning (`memory/unified_db_manager.py`, `learning/experience.py`) |

## The Capability-Composition Model

When a goal arrives, the orchestrator resolves it through a decision sequence rather than a hard-coded pipeline:

```mermaid
flowchart TD
    A[New User Goal] --> B[Understand the problem]
    B --> C[Discover required capabilities]
    C --> D{Where does the<br/>capability live?}
    D -->|Exists| E[Existing capability<br/>agents / MCP / tools / adapters]
    D -->|Specified| F[Planned / near-ready<br/>planning corpus + skills]
    D -->|Missing| G[External capability<br/>provider / marketplace / build]
    E --> H[Compose a plan]
    F --> H
    G --> H
    H --> I[Policy / permission gate]
    I --> J[Execute]
    J --> K{Verified?}
    K -->|Yes| L[Deliver honestly]
    K -->|No| M[Retry / repair / failover]
    M --> J
    L --> N[Capture reusable experience<br/>into memory]
```

This is why SupremeAI's capability coverage is much larger than its count of polished user-facing features: a capability may exist in code, be exposed through one of the seven+ MCP servers, be reachable through a provider adapter, run in a dedicated microservice, or already be specified in the planning corpus and only need final wiring.

## How a User Problem Is Solved (Runtime Path)

A concrete request — say a chat message — travels this path in the current code:

1. **Ingress.** The React app (`frontend/src/services/chatService.ts`) POSTs to `/api/chat/stream`. The backend `create_app()` factory (`backend/core/app_builder.py`) passes the request through its 16-layer middleware chain (request context, security headers, validation, tenant extraction, auth, rate limiting, …).
2. **Routing.** The chat router hands the prompt to the **Brain** (`backend/brain/`): `ModelRouter` selects the best available provider; `core/llm/llm_gateway.py` executes through litellm with a semantic cache, fallback chain, `CostGuard` budget enforcement and per-task model maps (e.g. coding → `groq/llama-3.3-70b-versatile`, general chat → `gemini/gemini-2.0-flash`).
3. **Capability resolution.** `core/orchestration/orchestrator.py` decomposes intent (`decompose_intent()`) and executes a skill chain over the `EvolutionSkillGraph`, composing existing tools (`backend/tools/` — code, media, browser, MCP, knowledge, security, …) instead of inventing new ones.
4. **Verification & governance.** Results pass health/verification layers; high-impact actions require HITL approval over `/ws/hitl` or the approval workflow. The **Budget Guardian** subprocess (`scripts/orchestrator/auto_budget_guardian.py`) halts execution fail-closed if cost limits are breached.
5. **Delivery & learning.** Streams return via SSE (with WebSocket fallback shims), and outcomes are written to memory (`memory/episodic_memory.py`, `long_term_memory.py`) and analyzed by the learning loop (`learning/outcome_analyzer.py`) so future planning improves.

## The Self-Evolution Loop

SupremeAI treats its own codebase and operations as a target for the same governed execution machinery:

- **Observation:** `agents/SentinelAgent` (heartbeat monitor, anomaly detector, alert router), `agents/InternetMonitorAgent`, performance metrics tables (`models/` `performance_metrics`, `system_alerts`).
- **Diagnosis:** `tools/gap_miner/` (read-only project intelligence), `scripts/advanced_analysis/` (21 static analyzers run in CI), `pyerrorfix/` (error detection/auto-fix engine).
- **Planning & patching:** `tools/autonomy/` (self-heal loop, deploy guard, change budget — read-only/plan-first by default), `tools/solution_synthesizer/` (diagnosis → sandbox → verified patch, dry-run by default, `--apply` required).
- **Verification:** regression scanners, mutation testing, test synthesizer, coverage gates (`scripts/ci/coverage_quality_gate.py` with tiered policy).
- **Deployment safety:** blue-green/canary deploy scripts, `pre_deploy_check.sh` nine-step gate, rollback paths.
- **Knowledge compounding:** `tools/knowledge/` (tool knowledge cards injected into `ai_memory`), `tools/knowledge_squeezer/` (multi-model distillation with adversarial audit), `evolution/` (fitness evaluator, canary manager, benchmark runner).

## Product Surfaces

| Surface | Entry point | Audience |
|---------|-------------|----------|
| **Studio web app** | `frontend/src/App.tsx` — user workspace (`/workspace/*`), IDE, AI Studio, swarm map, evolution forge | End users |
| **Admin console** | `/admin/*` — OTP/TOTP step-up, ~30 panels (model router, security, CI/CD visualizer, cost auditor) | Administrators |
| **AETHEL Command Center** | `frontend/src/commandcenter/` — module-grouped ops cockpit (DECK/OPERATE/BUILD/OBSERVE/SECURE/MONEY/SYSTEM) with WebSocket realtime | Administrators |
| **VS Code extension** | `tools/vscode-extension/` v6.0.0 — 31 commands, chat, swarm/trio pipelines, admin & customer dashboards | Developers |
| **MCP servers** | `backend/tools/mcp/mcp_server.py` + 6 siblings, plus `infrastructure/mcp-control-plane/` | AI clients / ops |
| **REST + WebSocket API** | 398 paths (checked-in `backend/openapi.json`), 10 WS endpoints with SSE fallbacks | Integrators |
| **Docs site** | `apps/docs/` (Docusaurus, English + Bengali) | Everyone |

## Design Values Worth Knowing Before You Contribute

- **Free tier is a first-class constraint.** Render free instances have ~512 MB RAM and sleep after ~15 minutes idle; the backend hard-enforces a single uvicorn worker in production, `LOW_MEMORY_MODE` exists, and four keep-alive mechanisms ping services on schedules. PRs are checked by `scripts/ci/check_free_tier_limits.py`.
- **Cost is governed, not assumed.** `CostGuard` runs inside the LLM gateway; `MAX_COST_PER_TASK` is enforced; the orchestrator halts on budget-guardian failure.
- **Plan-first autonomy.** Autonomous tools (`tools/autonomy`, `tools/solution_synthesizer`) are read-only/dry-run by default; applying changes requires explicit flags and approvals.
- **Bilingual codebase.** Bengali comments, i18n locales (`en|bn|es|zh` in `frontend/src/i18n/`) and Bengali docs (`README_BANGLA.md`, `apps/docs/docs/bangla-guide.md`, admin token strings `packages/design-tokens/src/admin.bn.json`) are intentional; CI runs a Bengali i18n completeness checker.
- **Honesty over polish.** Degraded modes must report degraded status (e.g. `worker_service.py` reports degraded when Celery/Redis are absent rather than pretending health).



<!-- ============================================================ -->
<!-- Merged Source: docs/03-getting-started.md -->
<!-- ============================================================ -->

# 03 — Getting Started

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | Backend runtime (`python_version = 3.11` in backend `pyproject.toml`) |
| Poetry | 2.4.1 | Pinned in CI (`poetry.lock` is authoritative) |
| Node.js | 24+ | `engines: node >=24.0.0`, `.nvmrc` = `24` |
| pnpm | 10.15.0+ | `packageManager: pnpm@10.15.0` (Corepack recommended) |
| PostgreSQL | 15/16 | Only if running a local DB instead of Supabase (`pgvector/pgvector:pg15` image in prod compose) |
| Redis | 7 | Optional locally — backend degrades gracefully (`QUEUE_BACKEND_PRIORITY=asyncio,redis,celery,pubsub`) |
| Docker | — | Optional, for the compose-based setup |

## 1. Clone and Install

```bash
git clone https://github.com/SaifulHaqueNiloy/supremeai.git
cd supremeai

# JavaScript workspace (frontend, packages, vscode extension)
corepack enable
pnpm install

# Python backend
cd backend
poetry install --with dev          # add --with browser for Playwright tooling
                                   # add --with ml for torch/sentence-transformers
```

## 2. Configure Environment

Copy the template and fill in what you need (see [04-Configuration](04-configuration.md) for the full reference):

```bash
cp .env.example .env
```

Minimum for a functioning local backend:

```bash
# One LLM provider key is enough — the model router picks whichever is present
GEMINI_API_KEY=...                 # free tier friendly (default model gemini/gemini-2.0-flash)

# Database — either Supabase or local Postgres
DATABASE_URL=postgresql://postgres:supremeai@localhost:5432/supremeai
# SUPABASE_URL=... SUPABASE_KEY=... (enables Supabase client + schema bootstrap)

# Auth secrets (dev; production enforces strength and fail-fast)
JWT_SECRET=dev-secret-change-me-0123456789abcdef
ENCRYPTION_KEY=...                 # generate: python scripts/setup_kms.sh
SUPREMEAI_ADMIN_PASSWORD_HASH=...  # bcrypt hash for the admin login

ENV=local
PORT=8080
```

The settings object (`backend/core/config.py`) reads `.env` from `../.env`, `.env`, `/etc/secrets/.env`, and `/etc/secrets/render.env` (the latter two are Render secret-file mounts). Config validation runs at startup and **exits with code 1** on missing production-critical values — in `ENV=local` you get warnings instead.

## 3. Run the Backend

```bash
# From repo root (turbo script):
pnpm backend:dev
# equivalent to: cd backend && poetry run uvicorn core.app:app --reload

# or from backend/:
poetry run python main.py          # reload enabled only when ENV=local
```

- Base URL: `http://localhost:8080`
- Swagger UI: `http://localhost:8080/docs` · ReDoc: `http://localhost:8080/redoc`
- OpenAPI JSON: `http://localhost:8080/api/v1/openapi.json`
- Liveness: `http://localhost:8080/api/v1/health/live`
- Production hard-enforces **1 uvicorn worker** (512 MB Render constraint) — do not raise `UVICORN_WORKERS` in production.

Optional role-based runs (same image, filtered routers):

```bash
SUPREMEAI_SERVICE_ROLE=scraper poetry run uvicorn services.scraper.main:app --port 8082
SUPREMEAI_SERVICE_ROLE=worker  poetry run python worker_service.py     # Celery supervisor
```

## 4. Run the Frontend

```bash
cd frontend
pnpm dev                           # Vite dev server on http://localhost:5173
```

Dev proxy (from `frontend/vite.config.ts`): `/api`, `/admin-api` and `/auth` are proxied to the resolved backend URL — precedence `VITE_API_URL || VITE_BACKEND_URL || VITE_USER_BACKEND || RENDER_SERVICE_URL`. Missing backend URL **fails the production build** (`process.exit(1)`); for local dev the proxy simply points at `http://localhost:8080` if unset.

Frontend quality loop:

```bash
pnpm test        # vitest run
pnpm typecheck   # tsc --noEmit (strict)
pnpm lint        # eslint
pnpm quality     # all three, strict mode
```

## 5. Run Everything with Docker Compose

`docker-compose.yml` is profile-based:

```bash
# Core API + frontend only (default profile)
docker compose up

# With local Postgres + Redis
docker compose --profile local up

# Scraper microservice
docker compose --profile scraper up

# Everything: core, worker, scraper, mcp control plane, frontend, db, redis
docker compose --profile full up
```

| Service | Port | Notes |
|---------|------|-------|
| `core` | 8080 | Builds `backend/Dockerfile` (multi-stage python:3.11-slim, non-root user, `CMD ["python","main.py"]`) |
| `frontend` | 3000 | nginx serving the Vite build; proxies `/api/`, `/admin-api/`, `/ws` to `http://backend:8080` |
| `db` | 5432 | postgres:16-alpine (`POSTGRES_DB=supremeai`) |
| `redis` | 6379 | redis:7-alpine |
| `worker` | 8081 | `worker_service.py` (profiles `workers`/`full`) |
| `scraper` | 8082 | Playwright/Chromium isolated from the core image |
| `mcp` | 3771 | MCP Control Tower (`infrastructure/mcp-control-plane/Dockerfile`) |

The production compose file (`docker-compose.production.yml`) additionally brings up Prometheus, Grafana, Alertmanager and an OpenTelemetry collector with resource limits and healthchecks.

## 6. Verify the Install

```bash
python scripts/verify_capabilities.py    # capability matrix smoke test (exit 0 = pass)
bash scripts/check_app_boots.sh          # boot smoke check
curl localhost:8080/api/v1/health/live   # {"status":"ok",...}
```

The startup log should show the lifespan sequence: config validation → reliability controller → service init → orchestrator mounted → Supabase bootstrap (if configured) → background agents started.

## 7. Optional Components

- **MCP Control Tower** (`infrastructure/mcp-control-plane/`): TypeScript MCP server exposing render/firebase/supabase/redis/infisical/cloudflare/github adapters. Local dev: see `mcp_config.local.json`; deployed as `supremeai-mcp-tower` via its own `render.yaml`.
- **Backend MCP servers** (`backend/tools/mcp/`): stdio servers — e.g. `python tools/mcp/mcp_server.py` ("supremeai-knowledge-graph", requires Neo4j creds) — for connecting Claude/other MCP clients to SupremeAI capability data.
- **VS Code extension**: open `tools/vscode-extension/`, `pnpm install`, `pnpm compile`, press **F5** to launch an Extension Development Host (details in [11-VS Code Extension](11-vscode-extension.md)).
- **Docs site**: `cd apps/docs && pnpm install && pnpm start` (Docusaurus on :3000).
- **Keep-alive**: `node scripts/keepalive.js` pings `BACKEND_URL/api/v1/health` every 5 minutes if you run the backend on a sleeping free tier.

## Troubleshooting First Steps

| Symptom | Check |
|---------|-------|
| Backend exits immediately at boot | Config validation output — usually missing `JWT_SECRET` / `ENCRYPTION_KEY` / `SUPREMEAI_ADMIN_PASSWORD_HASH` in prod mode |
| `poetry install` fails on lock | Run `poetry check --lock`; CI pins Poetry 2.4.1 and fails on drift |
| Frontend build fails with missing backend URL | Set `VITE_API_URL` — production builds fail fast by design |
| LLM calls fail with `OLLAMA_URL` error | Ollama is fail-fast (no localhost fallback) — unset it or point it at a live server |
| Redis connection errors | Expected on free tier — queue priority falls back to asyncio; set `REDIS_REQUIRED_FOR_PRODUCTION=false` for dev |
| WS dashboard won't connect | Check `VITE_WS_BASE_URL` / scheme swap (https→wss) in `frontend/src/utils/api.ts` |
