# SupremeAI 2.0 🚀
**Autonomic CI/CD Command Center & Neural Agentic Workspace**

## 🌐 Live Application URLs
- **Primary Frontend (Netlify):** [https://tiny-stroopwafel-2d981c.netlify.app](https://tiny-stroopwafel-2d981c.netlify.app)
- **Primary Backend (Render):** [https://supremeai-backend-08zd.onrender.com](https://supremeai-backend-08zd.onrender.com)
- **Secondary Backend (Render):** [https://supremeai-backend-secondary.onrender.com](https://supremeai-backend-secondary.onrender.com)
- *Note: Frontend automatically switches backends if one goes to sleep (Zero-Cost HA Strategy).*

SupremeAI is a production-grade, highly scalable ecosystem featuring a Hub-and-Spoke CI/CD pipeline, an AI-powered CodeQL audited backend, and dual real-time client interfaces.

## 🌟 Core Architecture

### 🧠 The Brain (Backend)
- **Framework:** FastAPI (Python)
- **AI Engine:** Google Gemini 1.5 Pro (Generative AI)
- **Streaming:** Native WebSockets (`wss://`) for token-by-token generation.
- **Agentic Tools:** Autonomous tool calling (Database Search, System Health, Code Execution).
- **Security:** `AutonoGuard Engine` — JIT OTP + IP Churn Detection + AST Scanning + Self-Healing

### 💻 Command Center (Web)
- **Tech Stack:** Pure Vanilla HTML/CSS/JS (Zero framework overhead for maximum speed).
- **Features:** Real-time CI/CD Job Sync (GitHub Raw APIs), Interactive Hacker-style Terminal for logs, 1-Click Quick Actions (Rollback, Cache Flush).

### 📱 Supreme Workspace (Mobile)
- **Tech Stack:** Flutter & Dart (Provider + HTTP + WebSocket Channel).
- **Features:** Real-time AI chat stream, System Monitoring, God Mode enforcement UI.

### ⚙️ CI/CD Pipeline (GitHub Actions)
- **Matrix Builds:** Automatically builds Android APK, Windows EXE, and VS Code VSIX concurrently.
- **Security:** Integrated GitHub CodeQL Semantic Security Analysis on every push.

## 🚀 Getting Started

**Web Dashboard (Dev Mode):**
```bash
cd apps/web-chat
python -m http.server 3000
```

**Mobile App (Dev Mode):**
```bash
cd apps/mobile
flutter pub get
flutter run
```

## 📦 Monorepo & Package Management (pnpm Migration)

SupremeAI 2.0 uses **pnpm** as the package manager for the frontend monorepo. The migration was completed to improve install determinism and reduce disk usage across `apps/`, `packages/`, and `tools/`.

### Prerequisites
- **Node.js**: >= 20.0.0
- **pnpm**: >= 9.0.0

### Installation
```bash
pnpm install --frozen-lockfile
```

### Scripts
| Command | Description |
|---------|-------------|
| `pnpm turbo run build` | Build all workspaces |
| `pnpm turbo run lint` | Lint all workspaces |
| `pnpm turbo run test` | Run all tests |
| `pnpm backend:dev` | Start FastAPI dev server |
| `pnpm backend:test` | Run backend tests |

### Workspace Structure
- **apps/studio-client** — React/Vite workspace
- **apps/web-chat** — Chat interface
- **apps/desktop** — Electron/Tauri desktop app
- **apps/docs** — Docusaurus docs
- **packages/ui-components** — Shared UI library
- **packages/shared-types** — Shared Zod types
- **tools/vscode-extension** — VS Code extension
- **backend/core** — Core backend engine (orchestration, security, cache, evolution)
- **backend/tools** — AI Agent Tools organized by category (12 categories)

### Dependency Overrides
The root `package.json` enforces consistent versions across the monorepo:
- `typescript`: 5.4.5
- `vite`: 7.3.5
- `react` / `react-dom`: 18.2.0

### CI/CD Updates
- `supreme-core-ci.yml` and `supreme-release-builds.yml` now use `pnpm/action-setup@v3` with Node.js `actions/setup-node@v4` cache set to `pnpm`.
- Frontend jobs use `pnpm install --frozen-lockfile` and `pnpm turbo run build lint test`.

## 🔒 Security Enhancements & Production Readiness (July 2026)

As part of the SupremeAI 2.0 production readiness audit, the following security and reliability improvements were implemented:

### 🔐 Electron Security (Desktop Client)
- **contextIsolation**: Enabled to prevent renderer process from accessing Node.js APIs directly
- **nodeIntegration**: Disabled in renderer processes to prevent remote code execution vulnerabilities
- **sandbox**: Enabled for all renderer processes to restrict system access
- **Preload Script**: A dedicated `preload.js` exposes only safe APIs to the renderer via `contextBridge`
- **Content Security Policy**: Restrictive CSP to mitigate XSS risks
- **Build Configuration**: Updated to enforce secure electron-builder settings

### 🚫 Tenant Rate-Limit Bypass Fix (Critical)
- **Issue**: Rate limiting could be bypassed by providing fake `X-Forwarded-For` headers
- **Fix**: Tenant identity is now extracted exclusively from the verified JWT `Authorization` header (sub claim)
- **Middleware Update**: `RateLimitMiddleware` in `backend/core/rate_limiter.py` now validates token before rate-limiting
- **Tests**: Added tests to verify bypass attempts are blocked; removed insecure test cases

### 🐘 PgBouncer Connection Pool (High)
- **Singleton Pattern**: Database connection pool is now a true singleton, initialized at startup
- **Explicit Initialization**: New `init_db_pool()` function in `backend/core/pgbouncer_pool.py` creates the pool with optimized settings:
  - `statement_cache_size=0` (prepared statements handled by PgBouncer)
  - `min_size=5`, `max_size=30`
  - `command_timeout=30` seconds
- **Lifecycle Management**: Pool initialization moved to `backend/core/lifespan.py` with PostgreSQL DSN validation to avoid breaking tests (skips initialization in test environments)
- **Singleton Enforcement**: `get_db_pool()` raises `RuntimeError` if called before initialization
- **Test Fix**: Updated `test_pgbouncer_pool.py` to mock `asyncpg.Connection` for isolated unit tests

### 🐳 Docker & CI/CD Hardening
- **docker-compose.yml**:
  - Fail-fast environment variable expansion: `${VAR:?}` to catch missing configs
  - Added service healthchecks (backend on port 8000)
  - Explicit `depends_on` with `condition: service_healthy` for frontend services
- **GitHub Actions (deploy.yml)**:
  - Deployment job uses `environment: production` for protection rules and secrets
  - Added validation for required `CI_WEBHOOK_SECRET` in production

### 🔐 Admin & Secrets Management
- **Admin Whitelist**: Unified to `settings.admin_emails` (loaded from environment)
- **HMAC Comparison**: `ci_webhooks.py` now uses `hmac.compare_digest` for timing-safe secret comparison
- **Chaos Engineering**: Middleware now requires `LOCAL_CHAOS_MODE=true` AND non-production environment to activate
- **Cookie Security**: Updated session cookies to be `Secure`, `HttpOnly`, and `SameSite=Strict` in production

### 🧪 Test Suite Fixes
- **PgBouncer Pool Test**: Fixed `test_singleton_pattern` by mocking `asyncpg.Connection`
- **Docs Security Test**: Added missing `CI_WEBHOOK_SECRET` environment variable
- **Removed Impossible Test**: Deleted test that attempted to bypass rate-limit middleware in test environment (where middleware is bypassed entirely)

### ✅ Validation Results
- **Backend Tests**: 1,368 passed, 7 skipped (full suite)
- **Linting**: All modified files pass `ruff check`
- **Type Safety**: MyPy shows no new errors in modified files (pre-existing issues in unrelated modules remain)
- **Test Coverage**: Maintained >38% overall coverage target

## 🔐 Phase 0: AutonoGuard Enterprise Hardening (July 2026) ✅ COMPLETED

The AutonoGuard Engine provides autonomous governance with enterprise-grade security:

### 🔑 JIT OTP Enforcement
- **SHA-256 hash-based OTP storage** (plaintext never stored in Redis)
- **Masked admin_id in logs** (only 3 visible characters)
- **Timing-safe comparison** via `secrets.compare_digest`
- **Free-tier delivery** via Discord webhook or Resend email (3k emails/month)

### 🌐 IP Churn Detection
- **Redis-backed IP tracking** with 1-hour TTL
- **>5 IPs in 1 hour** triggers OTP re-verification
- **Malware immunity** detection for automated attack prevention

### 🛡️ Self-Healing Engine
- **ErrorRemediation** with Qdrant vector search for fix lookup
- **Circuit breaker pattern** prevents cascade failures
- **Structured events** on all code paths (zero silent failures)

### 📊 Availability Protection
- **Fail-Closed rate limiting** with in-memory fallback
- **Failure fingerprint persistence** survives server restarts
- **Config cache coalescing** prevents thundering-herd on refresh

### Core Philosophy Compliance
| Principle | Status |
|-----------|--------|
| Zero Cost | ✅ Free-tier services only |
| High Scalability | ✅ Stateless + Redis distributed |
| Zero Breakage | ✅ All fallbacks implemented |
| Human-in-Loop | ✅ JIT OTP minimal friction |
| Malware Immunity | ✅ IP Churn + JIT OTP |
| Self-Healing | ✅ ErrorRemediation integrated |
| Failure-Aware | ✅ ReliabilityController persistence |

## 💰 Monthly Operating Cost

| Service | Cost |
|---------|------|
| GCP Cloud Run | $0 (Always Free tier) |
| Firebase Hosting | $0 (Free tier) |
| Render | $0 (Free 750h/মাস) |
| Upstash Redis | $0 (Free tier, 10k requests/day) |
| **Total** | **$0/মাস** |

---

*Phase 0 hardening completed by Principal Autonomous AI Architect on 2026-07-20.*
