# SupremeAI 2.0 - Architecture Overview

## Introduction

SupremeAI 2.0 is a multi-cloud AI orchestration platform built on FastAPI with a React/Vite frontend. It targets zero-cost operation through aggressive free-tier utilization across multiple AI providers, while maintaining enterprise-grade security through the AutonoGuard Engine.

## Core Philosophy

- **Database-Driven Logic:** Hardcoded configurations are deprecated. Settings and rules are managed dynamically through Firestore.
- **Zero Operating Cost:** Through dynamic API routing, CostGuard, and Sandbox Auto-Destroy.
- **Self-Learning and Self-Healing Ecosystem:** Errors trigger self-correcting mechanisms under human oversight.

## 🏗️ Phase 1-4 Evolution

### Phase 1: Security & Configuration Management
- **Security Lockdown:** Implemented strict credential loading to prevent hardcoded secrets.
- **Dynamic Config Proxy:** Replaced hardcoded variables with a Firestore-backed `DynamicConfigProxy`.

### Phase 2: Cost Guard, Self Healer, and Control Tower
- **CostGuard:** Ensures zero-cost operations by acting as a pre-flight checker. It blocks transactions for tenants exceeding their `monthly_limit`.
- **SelfHealerService:** Catches backend failures (like 429 Rate Limits or internal errors) and automatically generates `pending_review` fixes.
- **Cloud Sandbox Orchestrator:** Implements an `auto_destroy_worker` using a TTL (Time-To-Live) mechanism to terminate idle sandboxes.
- **Architectural Control Tower:** A React-based HITL (Human-in-the-loop) dashboard in `apps/studio-client/` at `/architect-tower`.

### Phase 3: Production Lockdown
- **Log Stripping:** Production builds strip console/debugger statements.
- **Error Obfuscation:** Client receives generic error messages; detailed traces restricted to SelfHealerService.
- **HTTPOnly Cookies:** Auth tokens transmitted via secure HTTPOnly cookies, never localStorage.

### Phase 4: Enterprise Hardening — AutonoGuard Integration ✅ COMPLETED

---

## 🔐 AutonoGuard Engine Architecture

The AutonoGuard Engine is SupremeAI's unified autonomous governance layer, integrating JIT OTP, AST Security Scanning, Self-Healing, and IP Churn Detection.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT REQUEST FLOW                          │
│                                                                 │
│   Request → [Rate Limiter] → [IP Churn Check] → [OTP Verify]     │
│            ↓                                                    │
│         [AST Security Scan] ← (if code provided)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AutonoGuard Engine                           │
│  (backend/core/autonoguard_engine.py)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │ JIT OTP Verify  │    │ IP Churn Detect  │                     │
│  │                 │    │                 │                     │
│  │ - SHA-256 hash  │    │ - Redis hgetall │                     │
│  │ - Discord webhook│   │ - TTL tracking  │                     │
│  └────────┬────────┘    └────────┬────────┘                     │
│           │                      │                              │
│           └──────────┬───────────┘                              │
│                      │                                          │
│  ┌─────────────────────────────────┐                           │
│  │      Circuit Breaker            │                           │
│  │   failure_threshold=5           │                           │
│  │   recovery_timeout=60s           │                           │
│  └─────────────┬───────────────────┘                           │
│                │                                               │
│  ┌────────────────────┐    ┌────────────────────┐             │
│  │ Error Remediation  │    │ Immune System Scan │             │
│  │                    │    │                    │             │
│  │ - Qdrant vector DB │    │ - AST validation   │             │
│  │ - Circuit breaker  │    │ - Sandbox escape   │             │
│  └────────────────────┘    └────────────────────┘             │
│                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **AutonoGuardEngine** | `backend/core/autonoguard_engine.py` | Main orchestration class |
| **OTP Router** | `backend/core/otp_router.py` | JIT OTP delivery (Discord/Email) |
| **Rate Limiter** | `backend/core/rate_limiter.py` | Request throttling |
| **Reliability Controller** | `backend/core/reliability_controller.py` | Failure persistence |
| **Error Remediator** | `backend/core/error_remediation.py` | Self-healing lookup |
| **Immune Scanner** | `backend/core/immune_system.py` | AST security scanning |
| **Circuit Breaker** | `backend/core/resilience/circuit_breaker.py` | Failure cascade prevention |
| **Error Event Bus** | `backend/core/messaging/event_bus.py` | Structured error telemetry |

### Data Flow

1. **Request Arrival:** Request hits endpoint with admin credentials
2. **IP Churn Check:** `detect_ip_churn()` queries Redis for IP history
3. **OTP Verification:** If churn detected or no bypass, `verify_jit_otp()` checks SHA-256 hash
4. **Security Scan:** If code provided, `scan_for_threats()` validates via AST
5. **Self-Healing:** On error, `heal_error()` triggers remediation lookup
6. **Event Emission:** All events flow through `error_event_bus`

---

## 🧠 The Brain (Backend)

- **Framework:** FastAPI (Python)
- **AI Engine:** Google Gemini 1.5 Pro (Generative AI)
- **Streaming:** Native WebSockets (`wss://`) for token-by-token generation.
- **Agentic Tools:** Autonomous tool calling (Database Search, System Health, Code Execution).
- **Security:** AutonoGuard Engine + Constitutional Enforcement

### AI Provider Stack

| Provider | Model | Rate Limit | Purpose |
|----------|-------|----------|---------|
| Groq | llama3-70b-8192 | 28 RPM | General chat, fallback |
| DeepSeek | deepseek-coder | Unlimited | Code generation |
| OpenAI | gpt-4o-mini | 19 RPM | Reasoning tasks |
| Google | gemini-1.5-pro | 9 RPM | Heavy reasoning |

### Hallucination Defense Layers

1. **Input Sanitizer** — Clean and validate all inputs
2. **Generation Monitor** — Track output quality metrics
3. **Factual Verifier** — Cross-reference claims
4. **AST Validator** — Code security scanning
5. **Consensus Scorer** — Multi-model agreement scoring
6. **Error Pattern DB** — Historical fix patterns via Qdrant

---

## 💻 Command Center (Web)

- **Tech Stack:** Pure Vanilla HTML/CSS/JS (Zero framework overhead for maximum speed).
- **Features:** Real-time CI/CD Job Sync, Interactive Hacker-style Terminal, 1-Click Quick Actions

### CI/CD Pipeline (GitHub Actions)

- **Matrix Builds:** Automatically builds Android APK, Windows EXE, and VS Code VSIX concurrently.
- **Security:** Integrated GitHub CodeQL Semantic Security Analysis on every push.

---

## 📱 Supreme Workspace (Mobile)

- **Tech Stack:** Flutter & Dart (Provider + HTTP + WebSocket Channel).
- **Features:** Real-time AI chat stream, System Monitoring, God Mode enforcement

---

## 🔧 Infrastructure

| Service | Provider | Cost | Purpose |
|---------|----------|------|---------|
| Cloud Run | GCP Always Free | $0 | Primary backend compute |
| Firebase | Google Free Tier | $0 | Authentication + Hosting |
| Render | Free 750h/month | $0 | Backup backend |
| Upstash Redis | Free Tier | $0 | Session state + rate limiting |
| Cloudflare Workers | Free Tier | $0 | Load balancing |

---

## 📡 API Architecture

```
/api/v1/
├── admin/          → AutonoGuard OTP protected
├── billing/        → Stripe integration + CostGuard
├── orchestrate/    → JIT OTP + IP Churn check
├── skills/         → AST scanned code execution
├── system/         → Rate limited + Admin only
└── chat/           → Standard rate limiting
```

---

## 🔒 Security Architecture

### Authentication Flow
```
Client → JWT Token → /auth/login → Token stored in HTTPOnly cookie
                     ↓
              Middleware extracts sub claim
                     ↓
              Per-request tenant isolation
```

### JIT OTP Enforcement
```
Sensitive Op Request → AutonoGuard.can_bypass_otp()
                              ↓
                    ANTI_HACKING_ENABLED check
                              ↓
                    detect_ip_churn() → is_churn?
                              ↓ Yes              ↓ No
                        request_jit_otp()   Proceed + Cache Bypass
                              ↓
                       verify_jit_otp()
```

---

*Architecture documented by AutonoGuard Architect — Last updated: 2026-07-20*
