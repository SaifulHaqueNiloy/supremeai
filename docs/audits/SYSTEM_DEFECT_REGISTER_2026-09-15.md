r # SupremeAI — Comprehensive System Error, Defect & Technical Debt Register
**Document ID:** `SYSTEM_DEFECT_REGISTER_2026-09-15`  
**Status:** Living Baseline  
**Scope:** Full Stack (Backend, Frontend, Shared Contracts, CI/CD, Test Suites)  
**Total Modules Audited:** 1,189 Modules | 707 Backend Routes | 236 Frontend Endpoints | 37 Test Suites

---

## Executive Summary

Through static analysis, import graph walks, endpoint parity checking (`feature_parity_sentinel.py`), runtime audits (`M0_G_QA_SPEC_COMPLETION.md`), and contract tracing between `frontend/src` and `backend/api`, all known issues across SupremeAI have been categorized into 6 distinct defect classes:

1. **Class A: Broken Operational Flows & Contract Mismatches** (Runtime crashes, 404/422 failures, dead executions)
2. **Class B: Static Shells & Missing User Interfaces** (Frontend marketing shells with no backend actions)
3. **Class C: Orphan Backend APIs** (Real, functional backend engines with zero frontend exposure)
4. **Class D: Stubs, Mocks & Simulated Responses** (Hardcoded mock responses masking missing integrations)
5. **Class E: Test Debt & Skipped Test Cases** (96 total skipped tests, 68 deferred tickets)
6. **Class F: Core Architectural Debt & Subsystem Duplication** (Run fabric gaps, memory fragmentation, version drift)

---

## 1. Class A: Broken Operational Flows & Contract Mismatches (P0)

These are bugs where components attempt real execution but fail deterministically due to contract discrepancies, route pluralization mismatches, or missing parameters.

| ID | Component / File Path | Root Cause | Runtime Symptom & Impact |
| :--- | :--- | :--- | :--- |
| **ERR-A01** | `frontend/src/pages/user/AgentWorkspace.tsx:L73` & `backend/api/routes/agent.py:L24` | Frontend sends `{ prompt, project_id: 'default' }` without `task_id`. Backend `AgentTaskRequest` strictly requires `task_id: str = Field(...)`. | HTTP `422 Unprocessable Entity`. Agent Workspace fails on execution; UI displays *"Connection error to SupremeAI Backend"*. |
| **ERR-A02** | `frontend/src/services/agentService.ts:L19` & `backend/api/routers.py:L100` | Frontend calls `POST /api/v1/agent/execute` (singular). Backend router registers `prefix="/api/v1/agents"` (plural). | HTTP `404 Not Found`. Any client using `agentService.executeAgentTask` cannot reach the route. |
| **ERR-A03** | `frontend/src/components/customer/BrowserPreview.tsx:L264` | Browser preview renders `<iframe src={currentUrl}>` directly in the DOM instead of proxying through backend Playwright. | External domains return `X-Frame-Options: SAMEORIGIN` / CSP frame-ancestors errors. Modern websites fail to load; screen stays blank. |
| **ERR-A04** | `frontend/src/pages/user/IdeWorkspace.tsx:L57` & `AgentWorkspace.tsx:L51` | Browser `@webcontainer/api` requires `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp` headers. | Dev server and preview lack COOP/COEP headers. Terminal displays `[system] Sandbox unavailable in this preview` and fails to spawn shell. |
| **ERR-A05** | `frontend/src/services/apiClient.test.ts:L61` | Test suite asserts against `GET /api/v1/projects`. No such route exists in the backend (backend only exposes `/repos` and `/workspaces`). | Contract test passes via mock, but real application calls to `/api/v1/projects` hit 404. |
| **ERR-A06** | `backend/api/routes/browser/_automation.py:L142` | Playwright action handlers lack explicit element-state checks before click/type actions on dynamic SPAs. | Intermittent timeouts (`TimeoutError: 15000ms exceeded`) on dynamic DOM mutations. |

---

## 2. Class B: Static Shells & Missing User Interfaces (P1)

These are views where navigation routes exist and render nice visuals, but are non-functional static marketing cards with zero operational capabilities.

| ID | Route / File Path | Current State | Missing Capability |
| :--- | :--- | :--- | :--- |
| **ERR-B01** | `/workspace/projects`<br>`WorkspaceModulePage.tsx:L7` | Static marketing cards (`modules.projects`). Clicking "Create a project space" does nothing. | No Project Creation Modal (`create-project-btn`), no project listing, no deletion or rename. |
| **ERR-B02** | `/files`<br>`App.tsx:L192` | Renders `WorkspaceModulePage module="files"` (which is not even defined in `modules` record, falls back to empty). | No file dropzone/upload component (`file-input`), no file explorer, no storage integration (`/api/chat/upload`). |
| **ERR-B03** | `/activity`<br>`WorkspaceModulePage.tsx:L8` | Static mock cards describing activity features. | No event timeline component, no connection to backend audit logs or event bus. |
| **ERR-B04** | `/runs`<br>`WorkspaceModulePage.tsx:L10` | Static mock cards describing execution tracking. | No run observer, no execution list, no step retry interface. |
| **ERR-B05** | `/marketplace`<br>`WorkspaceModulePage.tsx:L9` | Static marketing card. Separate component `EnhancedSkillMarketplace.tsx` exists but is buried in admin. | No skill installation flow, no category filters for normal users. |

---

## 3. Class C: Orphan Backend APIs (P1 - 22 Endpoints)

These are functional backend routes fully implemented, registered, and verified in test suites, but completely disconnected from the frontend interface.

### 3.1 Missions Engine (11 Endpoints)
* `POST /api/v1/missions` — Create autonomous multi-step mission
* `GET /api/v1/missions` — List active and historical missions
* `GET /api/v1/missions/{id}` — Get single mission state & checkpoints
* `POST /api/v1/missions/{id}/start` — Start execution engine
* `POST /api/v1/missions/{id}/advance` — Step through mission tasks
* `POST /api/v1/missions/{id}/approve` — HITL policy approval gate
* `POST /api/v1/missions/{id}/fail` — Fail-safe termination
* `POST /api/v1/missions/{id}/repair` — Self-healing / repair executor
* `POST /api/v1/missions/{id}/cancel` — Graceful mission abort
* `GET /api/v1/missions/{id}/trace` — Complete execution trace history
* `GET /api/v1/missions/{id}/trace/stream` — Real-time Server-Sent Events (SSE) telemetry trace

### 3.2 Model Context Protocol (MCP) Hub & Client Management (7 Endpoints)
* `GET /api/v1/mcp/gateway` — Gateway discovery & capability registry
* `POST /api/v1/mcp/slug/claim` — Tenant slug claiming for external MCP clients
* `GET /api/v1/mcp/clients` — List authorized MCP desktop & IDE clients
* `POST /api/v1/mcp/clients` — Provision new MCP client with scoped access
* `GET /api/v1/mcp/clients/{id}` — Client status, heartbeat & permission audit
* `POST /api/v1/mcp/clients/{id}/rotate` — Zero-downtime secret token rotation
* `DELETE /api/v1/mcp/clients/{id}` — Immediate token revocation

### 3.3 Federated Capability Circles (4 Endpoints)
* `GET /api/v1/circles` — Topology of active capability circles (C1–C6)
* `GET /api/v1/circles/health` — Aggregate circle health status
* `GET /api/v1/circles/events` — Cross-circle telemetry event stream
* `POST /api/v1/circles/dispatch` — Central MCP router command dispatch

---

## 4. Class D: Stubs, Mocks & Simulated Responses (P1/P2)

These are components where fake data, random mathematical generators, or static strings are returned instead of live runtime results.

| ID | File & Line Number | Mocked Data / Logic | Real System Needed |
| :--- | :--- | :--- | :--- |
| **ERR-D01** | `frontend/src/pages/PublicPages.tsx:L57` | `responseFor(input)` returns 4 canned strings via regex matching. | Connect to backend `/api/stream/chat` or free-tier light LLM router. |
| **ERR-D02** | `backend/api/routes/browser/_crown_jewel.py:L48` | `capture_screenshot()` returns a hardcoded 1x1 pixel blank transparent PNG base64 string. | Call `PlaywrightBrowserAgent.screenshot()` to capture the real viewport. |
| **ERR-D03** | `backend/api/routes/browser/_crown_jewel.py:L28` | `ai_action()` returns static string: `"This is a mock summary for..."`. | Pass page DOM text to `ModelRouter` for real contextual AI summary. |
| **ERR-D04** | `frontend/src/components/admin/InteractiveChatTab.tsx:L233` | Hardcoded switch-case shell simulating `help`, `status`, `system-check`, `neofetch`. | Wire to backend system diagnostics API / task gateway. |
| **ERR-D05** | `frontend/src/components/dashboard/AgentExecutionTelemetryCockpit.tsx:L75` | Static file array: `setFiles(['src/', 'components/...'])`. | Connect to repository file tree scanner endpoint (`/api/repos/tree`). |
| **ERR-D06** | `frontend/src/providers/MockSwarmProvider.tsx:L39` | CPU usage and Memory usage generated using `Math.random() * 4`. | Wire to backend `/api/v1/system/health` or Render telemetry metrics. |
| **ERR-D07** | `frontend/src/services/api/microserviceMonitor.ts:L15` | Fallback mock object for `fetchJavaWorkerHealth`. | Expose real microservice health probe or retire dormant monitor. |
| **ERR-D08** | `frontend/src/lib/llm.router.ts:L16` | Client-side SDK calls stubbed with `console.log`. | Wire through backend `/api/v1/stream` proxy. |

---

## 5. Class E: Test Debt & Skipped Test Cases (P2)

Registry source: `docs/SKIPPED_TESTS.md`. Total skipped tests: **96**.

### 5.1 Intentional Skips (28 Tests)
Live cloud dependencies requiring paid credits or hardware unavailable in CI (e.g. live AWS S3, Stripe Live Webhook verification, Cloudflare live DNS purge).

### 5.2 Deferred Ticket Skips (68 Tests - Actionable Debt)
* **Configuration Fail-Fast Tests (14 Tests):**
  * `test_settings_redis_url`, `test_settings_stripe_configuration`, `test_settings_supabase_key_validation`
* **Model Router & Integration Fallback Tests (22 Tests):**
  * Provider quota tracking, Ollama local fallbacks, circuit breaker timeout edges
* **Security & Auth Boundary Tests (16 Tests):**
  * Tenant isolation edge cases, token expiration races, session invalidation
* **E2E Playwright Specs (16 Tests):**
  * Converted from `test.fixme` during M0-G, but waiting on mock backend seeds for complete automated runs.

---

## 6. Class F: Core Architectural Debt & Subsystem Duplication (P0/P1)

High-level architecture gaps tracked in `UNIFIED_NEXT_ROADMAP_2026-09-15.md`:

| ID | Subsystem | Current Flaw | Target Milestone Solution |
| :--- | :--- | :--- | :--- |
| **ERR-F01** | **Execution Architecture** | No canonical `Run` model. Executions are fragmented across `automation_execution`, `execution_log`, and `pending_tasks`. | **M1: Canonical Run Fabric** (Unified state machine, budgeting, retry classification). |
| **ERR-F02** | **Memory Subsystem** | 15+ competing store implementations under `backend/memory/` (`chromadb`, `sqlite`, `hierarchical_tree`, `episodic`, etc.). | **M3: Memory Consolidation** (Retire uncalled stores, keep `ai_memory` Phase-C vector 384 as sole authoritative store). |
| **ERR-F03** | **Context Assembly** | No structured L0/L1/L2 metadata or context budgeter. Unbounded prompts cause token waste and context bloat. | **M2: Context Engine** (Smallest-sufficient-context assembly). |
| **ERR-F04** | **Frontend Major Version Drift** | Dependabot PRs blocked due to breaking changes in `react-router-dom` (v6→v7), `react-i18next` (v15→v17), `@storybook` (v8→v10). | Dedicated frontend dependency upgrade & migration sprint. |

---

## Master Priority Remediation Matrix

```text
┌────────────────────────────────────────────────────────────────────────┐
│ P0 IMMEDIATE (Next 1-3 Days)                                           │
│ 1. ERR-A01: Fix AgentWorkspace task_id injection (eliminate 422 error) │
│ 2. ERR-A02: Add singular/plural alias (/agent/execute & /agents/...)   │
│ 3. ERR-D01: Wire Homepage Guest Chat to real backend stream            │
│ 4. ERR-B01 & ERR-B02: Add Project Modal & File Dropzone                │
├────────────────────────────────────────────────────────────────────────┤
│ P1 CORE (1-2 Weeks)                                                    │
│ 5. ERR-F01: Build M1 Canonical Run Fabric                              │
│ 6. ERR-C01-C03: Connect 22 Orphan APIs (Missions & MCP UI)              │
│ 7. ERR-D02 & ERR-D03: Replace browser mock screenshot with Playwright  │
├────────────────────────────────────────────────────────────────────────┤
│ P2 POLISH & HARDENING (2-3 Weeks)                                      │
│ 8. ERR-F02: M3 Memory Consolidation (archive duplicate stores)         │
│ 9. ERR-E02: Burn down 68 Deferred Skipped Tests                        │
│ 10. ERR-F04: Upgrade frontend libraries to resolve Dependabot drift    │
└────────────────────────────────────────────────────────────────────────┘
```
