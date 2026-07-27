# SupremeAI 2.0

Welcome to SupremeAI 2.0, an advanced AI-powered platform for autonomous intelligence solutions.

## Features

- **Adaptive Learning Engine**: Continuously learns and improves from interactions
- **Multi-Agent Collaboration**: Advanced agent interconnection system
- **Robust Infrastructure**: Cloud-native architecture with auto-scaling capabilities
- **Comprehensive Monitoring**: Real-time performance and health monitoring
- **Retry Handler**: Resilient retry mechanism with exponential backoff and jitter

## Retry Handler

The system includes a sophisticated retry handler that provides:

- Exponential backoff with jitter to prevent thundering herd problems
- Configurable retry parameters
- Support for both async and sync functions
- Budget-based retry limiting to prevent system overload
- Full Bangla localization for all messages and comments

To use the retry handler in your code:

```python
from backend.core.retry_handler import retry_handler

@retry_handler(max_retries=3, delay=1.0, backoff=2.0)
async def my_unreliable_function():
    # Your code here
    pass
```

See [RETRY_HANDLER_DOCS.md](backend/core/RETRY_HANDLER_DOCS.md) for detailed documentation.

## Installation

### Prerequisites
- **Node.js**: >= 20.0.0
- **pnpm**: >= 9.0.0
- **Python**: >= 3.10
- **Google Cloud SDK** (optional, for GCP deployment)

### Quick Start

**1. Clone the repository:**
```bash
git clone https://github.com/SaifulHaqueNiloy/supremeai.git
cd supremeai
```

**2. Install dependencies:**
```bash
# Install frontend dependencies
pnpm install --frozen-lockfile

# Install backend dependencies (from backend/ directory)
cd backend
pip install -r requirements.txt
cd ..
```

**3. Configure environment:**
```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit backend/.env with your API keys
# Required: GEMINI_API_KEY, OPENAI_API_KEY, FIRESTORE_CREDENTIALS
```

**4. Run the services:**

```bash
# Backend (FastAPI)
cd backend
uvicorn main:app --reload --port 8000
# Access API docs at http://localhost:8000/docs

# Frontend (Web Chat)
cd apps/web-chat
python -m http.server 3000
# Access at http://localhost:3000

# Mobile App (Flutter)
cd apps/mobile
flutter pub get
flutter run
```

For detailed setup instructions, see [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md).

---

## 🌐 Live Application URLs
- **Primary Frontend (Netlify):** [https://tiny-stroopwafel-2d981c.netlify.app](https://tiny-stroopwafel-2d981c.netlify.app)
- **Primary Backend (Render):** [https://supremeai-backend-08zd.onrender.com](https://supremeai-backend-08zd.onrender.com)
- **Secondary Backend (Render):** [https://supremeai-backend-secondary.onrender.com](https://supremeai-backend-secondary.onrender.com)
- *Note: Frontend automatically switches backends if one goes to sleep (Zero-Cost HA Strategy).*

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

For detailed architecture documentation, see [docs/SUPREMEAI_MASTER_BLUEPRINT.md](docs/SUPREMEAI_MASTER_BLUEPRINT.md).

---

## 📦 Monorepo & Package Management (pnpm Migration)

SupremeAI 2.0 uses **pnpm** as the package manager for the frontend monorepo. The migration was completed to improve install determinism and reduce disk usage across `apps/`, `packages/`, and `tools/`.

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

---

## 🏛️ Architecture & Philosophy

For deep-dive architecture documentation, system design principles, and implementation philosophy, see:
- **[SUPREMEAI_MASTER_BLUEPRINT.md](docs/SUPREMEAI_MASTER_BLUEPRINT.md)** — Complete system architecture and design decisions
- **[docs/architecture-overview.md](docs/architecture-overview.md)** — High-level architecture overview

---

## 🔒 Security & Phases

For comprehensive security audits, phase implementations, and compliance reports, see:
- **[PHASE0_AUDIT_REPORT.md](PHASE0_AUDIT_REPORT.md)** — AutonoGuard Enterprise Hardening (July 2026) ✅ COMPLETED
- **[BANGLA_SECURITY_AUDIT_REPORT.md](BANGLA_SECURITY_AUDIT_REPORT.md)** — Bengali security audit details
- **[docs/SECURITY.md](docs/SECURITY.md)** — Security policies and procedures

### Phase 0: AutonoGuard Enterprise Hardening (July 2026) ✅ COMPLETED

The AutonoGuard Engine provides autonomous governance with enterprise-grade security:

#### 🔑 JIT OTP Enforcement
- **SHA-256 hash-based OTP storage** (plaintext never stored in Redis)
- **Masked admin_id in logs** (only 3 visible characters)
- **Timing-safe comparison** via `secrets.compare_digest`
- **Free-tier delivery** via Discord webhook or Resend email (3k emails/month)

#### 🌐 IP Churn Detection
- **Redis-backed IP tracking** with 1-hour TTL
- **>5 IPs in 1 hour** triggers OTP re-verification
- **Malware immunity** detection for automated attack prevention

#### 🛡️ Self-Healing Engine
- **ErrorRemediation** with Qdrant vector search for fix lookup
- **Circuit breaker pattern** prevents cascade failures
- **Structured events** on all code paths (zero silent failures)

#### 📊 Availability Protection
- **Fail-Closed rate limiting** with in-memory fallback
- **Failure fingerprint persistence** survives server restarts
- **Config cache coalescing** prevents thundering-herd on refresh

#### Core Philosophy Compliance
| Principle | Status |
|-----------|--------|
| Zero Cost | ✅ Free-tier services only |
| High Scalability | ✅ Stateless + Redis distributed |
| Zero Breakage | ✅ All fallbacks implemented |
| Human-in-Loop | ✅ JIT OTP minimal friction |
| Malware Immunity | ✅ IP Churn + JIT OTP |
| Self-Healing | ✅ ErrorRemediation integrated |
| Failure-Aware | ✅ ReliabilityController persistence |

---

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

*SupremeAI 2.0 — Production-ready, zero-cost, self-healing AI infrastructure.*
