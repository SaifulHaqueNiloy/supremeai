---
id: browser-automation-core
subject: "SupremeAI Browser Automation — Canonical Plan"
document_role: architecture
planning_authority: CircleName.BROWSER
canonical: candidate
status: active
evidence_state: partial
disposition: retain
last_verified: 2026-09-17
supersedes: []
superseded_by: []
---

# SupremeAI Browser Automation — Canonical Plan

**plan_id:** PLAN-AUTOMATION-BROWSER-001  
**title:** SupremeAI Browser Automation Architecture  
**status:** active  
**version:** 3.0.0  
**last_verified:** 2026-09-17  

---

## Evolution History

| Stage | Version | Date | Summary |
|-------|---------|------|---------|
| **Stage 1** | v1 | ? | Initial Browser Plan |
| **Stage 2** | v2 | ? | Evaluation |
| **Stage 3** | v3.0.0 | 2026-09-17 | Current Architecture — EAOL + Dual Channel Integration |

---

## 1. Executive Summary

Browser automation is a **compatibility fallback mechanism** within the SupremeAI ecosystem, not the architectural foundation. It provides:

- Headless browser automation for web-based tasks
- Authentication persistence for user sessions
- Anti-detection and stealth capabilities
- Integration with the External Agent Orchestration Layer (EAOL)

---

## 2. Core Architecture

### 2.1 Integration Hierarchy

```
Control Tower
     ↓
 EAOL (External Agent Orchestration Layer)
     ↓
Capability Registry → Resource Registry → Integration Registry
     ↓
Runtime Selector
     ↓
Native API → MCP → Browser (fallback)
```

### 2.2 Key Principles

1. **Browser is fallback, not foundation**
2. **On-demand sessions only** — 40 integrations ≠ 40 active sessions
3. **Session isolation** — each task gets isolated browser context
4. **Credential persistence ≠ Session persistence**

---

## 3. Current Implementation

### 3.1 Authentication Persistence Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Cloud Vault | Encrypted credential store | Long-term session persistence |
| Device/Local | `SecureCredentialStore` | Local development |
| Session-only | Ephemeral storage | Isolated task execution |
| User-provided | Per-run authorization | Manual credential entry |

### 3.2 Core Components

**Session Manager** — Manages browser lifecycle:
- Creates isolated contexts on demand
- TTL and inactivity expiration
- Automatic cleanup and revocation

**Stealth Engine** (`browser_stealth.py`):
- `navigator.webdriver = undefined`
- Real user-agent pool spoofing
- Canvas/WebGL fingerprint noise injection
- DOM resource stripping (blocks images, fonts)

**Human Emulation** (`playwright_browser_agent.py`):
- Bezier curve mouse movement
- Human-like typing cadence (30-100ms per key)
- Cross-model verification via `cross_verify_prompt()`

---

## 4. Integration Points

### 4.1 EAOL Browser Capability

From `EXTERNAL_AGENT_ORCHESTRATION_LAYER_PLAN.md`:

```yaml
Browser Session Manager:
  - On-demand session creation
  - Isolated contexts per task
  - TTL/inactivity controls
  - Secure cookie encryption (AES)
  - Session reuse when safe and policy-permitted
```

### 4.2 Dual-Channel Zero-Cost Integration

From `dual_channel_zero_cost_browser_and_distributed_worker.md`:

The browser supports two execution channels:

**Channel 1: Server-Side Stealth Pool**
- Serverless browser processes on Render/Cloudflare
- Anti-bot, stealth, and DOM-strip already implemented
- Ideal for authenticated web execution

**Channel 2: Client-Side P2P Edge**
- Browser as distributed worker grid
- Local resource utilization (CPU/GPU)
- Residential IP advantage
- Web Worker + WebAssembly/WebGPU execution

---

## 5. Security Requirements

1. **Tenant isolation** — sessions never cross tenant boundaries
2. **Least privilege** — minimal permissions per session
3. **Encrypted credentials** — never in logs or artifacts
4. **Session expiration** — enforced TTL
5. **No credential exposure** — external workers cannot access secrets

---

## 6. Code Evidence

| Component | Path | Lines | Status |
|-----------|------|-------|--------|
| Browser Agent | `backend/tools/browser/playwright_browser_agent.py` | Live | ✅ |
| Stealth Module | `backend/tools/browser/browser_stealth.py` | Live | ✅ |
| Session Manager | `backend/services/browser/session_manager.py` | Live | ✅ |
| API Endpoints | `backend/api/routes/browser.py` | 59 endpoints | ✅ |

---

## 7. Verification Evidence

- Browser smoke tests (environment-dependent)
- Cross-model verification tests
- Quota/routing tests (integration with EAOL)
- Security isolation tests

---

## 8. Remaining Work

| Item | Priority | Estimated |
|------|----------|-----------|
| Unified browser contract | P1 | In progress |
| Worker isolation boundary | P1 | Pending |
| Staging runtime evidence | P2 | Pending |

---

## 9. References

- `EXTERNAL_AGENT_ORCHESTRATION_LAYER_PLAN.md` — EAOL baseline
- `dual_channel_zero_cost_browser_and_distributed_worker.md` — Dual-channel strategy
- `UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN.md` — Ecosystem contracts
- `PLAN_TO_CODE_TRACEABILITY_MATRIX.md` — Traceability

---

## 10. Supersedes

- ` EXTERNAL_AGENT_ORCHESTRATION_LAYER_PLAN.md` (archived)
- `dual_channel_zero_cost_browser_and_distributed_worker.md` (consolidated)