# SupremeAI — Master Non-Working Components, Defects & Technical Debt Register
**Document ID:** `SYSTEM_DEFECT_REGISTER_2026-09-15`  
**Status:** Canonical Living Baseline & Master Technical Debt Register (Single Source of Truth)  
**Scope:** Full Stack (Backend, Frontend, Shared Contracts, CI/CD, Test Suites, Infrastructure)  
**Audit Coverage:** 3,700 Git-Tracked Files | 1,189 Modules | 765 Backend Routes | 287 Frontend Endpoints | 37 Test Suites  
**Last Updated:** 2026-09-16 (round-14 status sweep) — every OPEN item re-verified against live main; fixes landed via PRs #383–#390 (status column reflects post-sweep state).

---

## 📑 Table of Contents

1. [Executive Summary & System Landscape](#1-executive-summary--system-landscape)
2. [Priority Legend & Defect Classification Matrix](#2-priority-legend--defect-classification-matrix)
3. [Class A: Broken Operational Flows & Contract Mismatches (P0)](#3-class-a-broken-operational-flows--contract-mismatches-p0)
4. [Class H: Hand-Verified Frontend-Backend Contract Mismatches (P0 Missing Routes)](#4-class-h-hand-verified-frontend-backend-contract-mismatches-p0-missing-routes)
5. [Class G: False Assurance Defects (P0/P1 — Systems Falsifying Success)](#5-class-g-false-assurance-defects-p0p1--systems-falsifying-success)
6. [Class B: Static Shells & Missing User Interfaces (P1)](#6-class-b-static-shells--missing-user-interfaces-p1)
7. [Class D: Non-Working Subsystems, Simulated & Stubbed Execution (P1/P2)](#7-class-d-non-working-subsystems-simulated--stubbed-execution-p1p2)
   - [7.1 Machine Learning, Fine-Tuning & Self-Evolution](#71-machine-learning-fine-tuning--self-evolution)
   - [7.2 Simulated Providers & Fabricated Execution at Runtime](#72-simulated-providers--fabricated-execution-at-runtime)
   - [7.3 Explicitly Unimplemented / Stubbed Plugins & Tools](#73-explicitly-unimplemented--stubbed-plugins--tools)
8. [Class C: Orphan Backend Surface (P1 — 57 Route Families)](#8-class-c-orphan-backend-surface-p1--57-route-families)
9. [Class S: Security, Guard-Consistency & Network Defects (P0/P1)](#9-class-s-security-guard-consistency--network-defects-p0p1)
10. [Class M: Governance, CI & Tooling Defects ("Gates That Don't Gate")](#10-class-m-governance-ci--tooling-defects-gates-that-dont-gate)
11. [Class P: Dependency & Version Inconsistencies](#11-class-p-dependency--version-inconsistencies)
12. [Class E: Test Debt & Skipped Test Cases (Formal Registry Summary)](#12-class-e-test-debt--skipped-test-cases-formal-registry-summary)
13. [Class F: Core Architectural Debt & Subsystem Duplication](#13-class-f-core-architectural-debt--subsystem-duplication)
14. [Master Priority Remediation Roadmap](#14-master-priority-remediation-roadmap)
15. [Methodology, Reproduction Commands & Verification Limits](#15-methodology-reproduction-commands--verification-limits)

---

## 1. Executive Summary & System Landscape

Through AST analysis, import graph walks, static route reconstruction (`scripts/audit/system_deep_scan_2026_09_15.py`), frontend-backend contract tracing, and test suite auditing, this master register consolidates **all known non-working components, runtime defects, contract mismatches, and technical debt items across SupremeAI into one unified document**.

### Key System Metrics (Audited)
* **Tracked File Census:** 3,700 git-tracked files.
* **Reconstructed Route Rows:** 765 backend routes mounted across 149 modules.
* **Frontend Endpoint Calls:** 287 `/api...` literals in `frontend/src`.
* **Hand-Verified Dead Frontend Calls:** 26 calls deterministically returning HTTP 404/422.
* **Orphan Backend Surface:** 57 route families (including the entire `commandcenter` admin API and 6 image conversion tools) with 0 frontend consumers.
* **Stub / Mock Footprint:** 1,157 backend hits across 340 files; 280 frontend hits across 145 files (excluding test directories).
* **Test Suite Debt:** 96 active skipped tests (68 deferred tickets, 28 intentional guards).

---

## 2. Priority Legend & Defect Classification Matrix

| Priority | Definition | Architectural Impact |
|---|---|---|
| **P0 (Immediate)** | Broken at runtime, HTTP 404/422/500, silent data loss, financial bypass, or false security assurance. | Blocks real user workflows or violates fundamental safety/financial integrity. |
| **P1 (Core)** | Mounted components that simulate execution, return canned/stubbed data, or are orphan capability families. | Violates "Operational Reality Over Superficial Artifacts" (Zero-Gap Principle). |
| **P2 (Hardening)** | Test debt, dependency drift, non-reproducible local tooling, and hygiene items. | Degrades developer velocity, CI stability, and long-term maintainability. |

---

## 3. Class A: Broken Operational Flows & Contract Mismatches (P0)

These are bugs where components attempt real execution but fail deterministically due to contract discrepancies, route pluralization mismatches, or missing parameters:

| ID | Component / File Path | Root Cause | Runtime Symptom & Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **ERR-A01** | `frontend/src/pages/user/AgentWorkspace.tsx:L73`<br>`backend/api/routes/agent.py:L24` | Live workspace caller sends `{ prompt, project_id: 'default' }` to plural `/api/v1/agents/execute` without `task_id`. Backend `AgentTaskRequest` strictly requires `task_id: str = Field(...)`. | HTTP `422 Unprocessable Entity`. Agent Workspace fails on execution; UI displays *"Connection error to SupremeAI Backend"*. | ✅ FIXED — Frontend now generates `crypto.randomUUID()` task_id and sends full contract. |
| **ERR-A02** | `frontend/src/services/agentService.ts:L19`<br>`backend/api/routers.py:L100` | Service layer client calls singular `POST /api/v1/agent/execute` (while live workspace uses `/agents/execute`). Backend router registers `prefix="/api/v1/agents"` (plural). | HTTP `404 Not Found`. Any client importing `agentService.executeAgentTask` hits dead endpoint. Split between live caller (A01) and service-layer drift (A02). | ✅ FIXED — Service now uses `/api/v1/agents/execute` (plural) with `task_id`. |
| **ERR-A03** | `frontend/src/components/customer/BrowserPreview.tsx:L264` | Browser preview renders `<iframe src={currentUrl}>` directly in the DOM instead of proxying through backend Playwright. | External domains return `X-Frame-Options: SAMEORIGIN` / CSP frame-ancestors errors. Modern websites fail to load; screen stays blank. | ❌ OPEN — Still renders iframe directly; a real Playwright screenshot-proxy pipeline is the tracked remediation (large ticket). |
| **ERR-A04** | `frontend/src/pages/user/IdeWorkspace.tsx:L57`<br>`AgentWorkspace.tsx:L51` | Browser `@webcontainer/api` requires `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp` headers. | Dev server and preview lack COOP/COEP headers. Terminal displays `[system] Sandbox unavailable in this preview` and fails to spawn shell. | ✅ FIXED (PR #389) — COOP/COEP now set on nginx (Docker prod) and vite preview; Vite dev server already had them. |
| **ERR-A05** | `frontend/src/services/apiClient.test.ts:L61` | Test suite asserts against `GET /api/v1/projects`. No such route exists in the backend (backend only exposes `/repos` and `/workspaces`). | Contract test passes via mock, but real application calls to `/api/v1/projects` hit 404. | ✅ FIXED — Test now uses real `GET /api/agents/` route. |
| **ERR-A06** | `backend/api/routes/browser/_automation.py:L142` | Playwright action handlers lack explicit element-state checks before click/type actions on dynamic SPAs. | Intermittent timeouts (`TimeoutError: 15000ms exceeded`) on dynamic DOM mutations. | ✅ FIXED (PR #390) — explicit wait_for(visible) gate before click/fill/type; timeout → honest HTTP 408 with verbatim reason. |

---

## 4. Class H: Hand-Verified Frontend-Backend Contract Mismatches (P0 Missing Routes)

Every row below was confirmed by reading **both** the frontend call site and the backend route definition. All produce HTTP 404 or 500 at runtime.

### 4.1 `/api/user/preferences` — Five Callers, Two Wrong Prefixes (`ERR-H01`)
* **Backend Definition (`backend/api/routes/preferences.py`):** Mounted at `/api/preferences/` (no `v1`, no `user` subpath).
* **Callers & Outcomes:**
  * `frontend/src/contexts/ThemeProvider.tsx:30,74` calls `/api/v1/preferences` ➔ **404**
  * `frontend/src/i18n/I18nProvider.tsx:27` calls `/api/user/preferences` ➔ **404**
  * `frontend/src/store/themeStore.ts:69,85` calls `/api/user/preferences` ➔ **404**
  * `frontend/src/pages/ProfilePage.tsx:33` calls `/api/user/preferences` ➔ **404**
* **Impact:** Theme, locale, and user profile settings silently fail to persist across 5 call sites.
* **Status:** ✅ FIXED (PR #383) — all 5 callers moved to GET/POST `/api/preferences`; extended prefs (preferred_language/profile/security/notifications) really persist via custom_shortcuts._extended; 4 regression tests.

### 4.2 `/api/skills/...` — Three Dead Calls (`ERR-H02`)
* **Backend Definition (`backend/api/routes/skills.py`):** Real paths are `/api/skills/catalog`, `/api/skills/search`, `/api/skills/install` (no id in path).
* **Callers & Outcomes:**
  * `frontend/src/services/skillsService.ts:104` calls `POST /api/skills/${skillId}/install` ➔ **404** (id segment unexpected)
  * `frontend/src/services/skillsService.ts:118` calls `DELETE /api/skills/${skillId}/uninstall` ➔ **404** (no uninstall route exists)
  * `frontend/src/pages/user/EvolutionForge/EvolutionForge.tsx:293` calls `POST /api/skills/deploy-blueprint` ➔ **404** (route absent)
* **Impact:** Skill installation and uninstallation are broken.
* **Status:** ✅ FIXED (PR #385) — frontend uses the real contract; DELETE /api/skills/uninstall added; install state persisted atomically; deploy-blueprint writes real manifests into the catalog; installed_only filter now real.

### 4.3 `/api/v1/workspaces/bind-target` — Wrong Prefix (`ERR-H03`)
* **Backend Definition (`backend/api/routes/workspaces_route.py:30`):** Real path is `POST /admin-api/workspaces/bind-target`.
* **Caller:** `frontend/src/services/aiActions.ts:174` calls `POST /api/v1/workspaces/bind-target` ➔ **404**.
* **Status:** ✅ FIXED (PR #383) — caller moved to `/admin-api/workspaces/bind-target`.

### 4.4 `/api/v1/ecosystem/admin/*` — 17 Dead Admin Calls (`ERR-H04`)
* **Backend Definition (`backend/api/routes/ecosystem_admin.py`):** Exposes `/capabilities`, `/decisions`, `/opportunities`, `/overview`, `/proposals`.
* **Frontend Caller (`frontend/src/lib/ecosystem/api.ts`):** Calls completely different names:
  * `/api/v1/ecosystem/admin/sources` (+`/discover`, `/{id}/transition`) ➔ **404**
  * `/api/v1/ecosystem/admin/policies` (+`/{id}`, `/match`) ➔ **404**
  * `/api/v1/ecosystem/admin/learned` (+`/prune`, `/{id}`) ➔ **404**
  * `/governance/decisions`, `/governance/budgets` ➔ **404**
  * `/proposals/{id}/decisions` (backend expects `/proposals/{id}/decide`) ➔ **404**
  * `/api/v1/auth/users`, `/api/v1/auth/users/{id}/role` ➔ **404**
* **Impact:** The ecosystem admin console client is entirely non-functional.
* **Status:** ❌ OPEN — Backend and frontend route names remain mismatched.

### 4.5 `/api/knowledge/*` — Four Dead Shared Service Calls (`ERR-H05`)
* **Backend Definition (`backend/api/routes/knowledge.py`):** Exposes `/api/knowledge/ask`, `/ask-scribe`, `/search`, `/seed`.
* **Caller (`packages/shared-services/src/services/SupremeAIService.ts`):**
  * Lines 98, 154 call `/api/knowledge/learn` ➔ **404**
  * Line 111 calls `/api/knowledge/failure` ➔ **404**
  * Line 127 calls `/api/knowledge/feedback` ➔ **404**
  * Line 136 calls `/api/knowledge/stats` ➔ **404**
* **Impact:** The learning-loop client fails silently when saving failure/feedback/learning signals.
* **Status:** ❌ OPEN — Backend has not implemented `/learn`, `/failure`, `/feedback`, or `/stats`.

### 4.6 Guaranteed HTTP 500: Missing Module Import (`ERR-H06`)
* **Location:** `backend/api/routes/agents.py:55` imports `from agents.research_assistant import ResearchAssistant`.
* **Defect:** `backend/agents/research_assistant.py` does not exist anywhere in the repository.
* **Impact:** `POST /api/agents/research/search`, `/research/summarize`, and `/research/cite` (`agents.py:52,71,82`) fail with **HTTP 500 unconditionally**.
* **Status:** ✅ FIXED (PR #384) — real research_assistant implemented: live arXiv search, extractive summarization, deterministic citations (apa/mla/ieee/bibtex); honest 400/502 error mapping; 10 tests.

### 4.7 Dual Divergent Agent Routers (`ERR-H07` & `ERR-H08`)
* `backend/api/routers.py` mounts both `/api/agents` (`api.routes.agents` with user token) and `/api/v1/agents` (`api.routes.agent` with autonomous agent token).
* `ERR-H08`: `backend/api/routes/agent.py:54` calls `exec_res = agent.execute(task_description=payload.prompt)`. The underlying implementation (`TaskRunnerAgent.execute`) is **synchronous**, blocking the async event loop for the entire run.
* **Status:** ❌ OPEN — Dual routers not unified; sync execution not offloaded.

---

## 5. Class G: False Assurance Defects (P0/P1 — Systems Falsifying Success)

These are components where the system claims success, health, or safety while performing no real work:

| ID | File / Location | Fabricated Behavior | Risk Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **ERR-G01** | `backend/api/routes/billing_api.py:271–275` | Missing Stripe API key redirects customer to success URL with fabricated `mock_session_123`. | **P0 Financial Integrity.** Customer is granted paid entitlements without payment. | ✅ FIXED — Now raises HTTP 503 when Stripe is unconfigured; no mock session created. |
| **ERR-G02** | `backend/core/deployment/production_deploy.py:379–476` | Uses `time.sleep(2)` to simulate deployments and rollbacks with mock URLs (`# Simulate rollback process`). | **P0 Operational Reality.** Deployment & rollback verification is fiction. | ✅ FIXED — All deploy/rollback methods now raise `NotImplementedError` until real backend is wired. |
| **ERR-G03** | `backend/api/routes/browser/_crown_jewel.py:43–45` | `@router.post("/security-scan")` returns unconditional `{"success": True, "score": 100, "issues": []}`. | **P1 Security Theatre.** Falsifies security checks. | ✅ FIXED — Now performs real passive header analysis and reports actual score. |
| **ERR-G04** | `backend/core/orchestration/cloud_sandbox_orchestrator.py:70–140` | Missing API key returns mock stdout `f"Mock output for execution of: {command}"`. | **P1 Integrity.** Fabricates code execution results. | ⚠️ PARTIAL (accepted fail-honest) — mock output stays but is explicitly labeled `"mock": True`; whitelisted in the hardened stub gate (PR #387) as honest labeling, not fabrication. |
| **ERR-G05** | `backend/api/routes/browser/_crown_jewel.py:60–69` | `@router.post("/tasks/{id}/step")` simulates step with static `{"action": "navigated to dashboard", "details": "Autonomous step succeeded"}`. | **P1 Autonomy.** Fabricates forward progress on stalled tasks. | ✅ FIXED — Now returns HTTP 501 with explicit message that legacy executor is retired. |
| **ERR-G06** | `backend/api/routes/browser/_crown_jewel.py:21–25` | Returns `session_id = "sess_" + sha256(url)[:16]` — a hash of URL, not a real session. | **P1 Runtime.** Subsequent lookups fail after reporting success. | ✅ FIXED — Now creates real UUID-backed session in session store. |
| **ERR-G07** | `backend/api/routes/agents.py:42–49` | Returns hardcoded `{"status": "active", "last_activity": "2026-01-01T00:00:00Z"}` for any agent id. | **P1 Telemetry.** Frozen timestamp; cannot distinguish alive from dead. | ✅ FIXED (PR #384) — unknown id → 404; known id → import-based available/unavailable; last_activity stays null (never fabricated). |
| **ERR-G08** | `backend/api/routes/agents.py:30–37` | `list_agents()` returns a hardcoded single `{"id": "research", ...}` entry. | **P1 Orchestration.** Dynamic agent discovery bypassed by hardcoded literal. | ✅ FIXED (PR #384) — catalog derived from the real backend/agents/ directory (import-checked, cached). |
| **ERR-G09** | `frontend/src/providers/MockSwarmProvider.tsx:39–79` | CPU/Memory usage generated using `Math.random() * 4` and canned logs. | **P1 Observability.** Fleet monitoring tuned off noise. | ✅ FIXED (PR #386) — dead MockSwarmProvider deleted (0 importers, Math.random metrics, canned logs). |
| **ERR-G10** | `frontend/src/pages/user/AgentWorkspace.tsx:81` | `runCode` completes via `setTimeout` after 700ms without running code. | **P1 Developer UX.** Evaluation progress is fabricated. | ✅ FIXED (PR #386) — runCode executes in the booted WebContainer and streams real output/exit code; honest NOT-RUN message when sandbox unavailable. |
| **ERR-G11** | `backend/api/routes/browser/_crown_jewel.py:1` | Module docstring explicitly notes `"Crown Jewel mock endpoints"` yet is mounted on live API. | **P1 Architecture.** Live endpoints built as mocks. | ✅ FIXED — Module docstring updated; all endpoints now perform real work or fail explicitly. |
| **ERR-G12** | `frontend/src/components/admin/shared/ActionCard.tsx:57` | `setTimeout(() => setActionStatus('✅ Code executed successfully!'), 1500)`. | **P1 Admin Safety.** Administrator told action succeeded while nothing ran. | ✅ FIXED (PR #386 + #387) — ActionCard and UnifiedChatBubble run actions execute in the real backend sandbox showing actual exitCode/stdout (mock-labeled output surfaced); share action really copies. |

---

## 6. Class B: Static Shells & Missing User Interfaces (P1)

Views where routes exist in navigation and render nice UI cards, but have zero operational backing:

| ID | Route / File Path | Current State | Missing Capability | Status |
| :--- | :--- | :--- | :--- | :--- |
| **ERR-B01** | `/workspace/projects`<br>`WorkspaceModulePage.tsx:L7` | Static marketing cards (`modules.projects`). Clicking "Create a project space" does nothing. | No Project Creation Modal (`create-project-btn`), no project listing, no deletion or rename. | ❌ OPEN |
| **ERR-B02** | `/files`<br>`App.tsx:L192` | Renders `WorkspaceModulePage module="files"` (which is undefined in `modules` record, falls back to blank). | No file dropzone/upload component (`file-input`), no file explorer, no storage integration (`/api/chat/upload`). | ❌ OPEN |
| **ERR-B03** | `/activity`<br>`WorkspaceModulePage.tsx:L8` | Static mock cards describing activity features. | No event timeline component, no connection to backend audit logs or event bus. | ❌ OPEN |
| **ERR-B04** | `/runs`<br>`WorkspaceModulePage.tsx:L10` | Static mock cards describing execution tracking. | No run observer, no execution list, no step retry interface. | ❌ OPEN |
| **ERR-B05** | `/marketplace`<br>`WorkspaceModulePage.tsx:L9` | Static marketing card. Separate component `EnhancedSkillMarketplace.tsx` exists but is buried in admin. | No skill installation flow, no category filters for normal users. | ❌ OPEN |

---

## 7. Class D: Non-Working Subsystems, Simulated & Stubbed Execution (P1/P2)

### 7.1 Machine Learning, Fine-Tuning & Self-Evolution
* **Kaggle GPU Kernel Execution (`backend/core/kaggle_orchestrator.py:L167+`):** `_generate_kernel_code()` pushes a template containing `# Task execution logic would go here` and returns dummy `output = {"status": "completed"}`. No model training or LoRA fine-tuning is ever executed.
* **Local Model Trainer (`backend/tools/learning/model_trainer.py:L65+`):** Triggers fake job ID. Status check explicitly returns: `"Local training is simulated only — no real checkpoint was produced."`
* **TRL DPOTrainer (`backend/tools/learning/rlhf_pipeline.py:L40+`):** Code explicitly returns `status: "not_implemented"`, `"Local TRL DPOTrainer wiring is not implemented yet"`.
* **Weekly Fine-Tuning CI Pipeline (`.github/workflows/weekly-fine-tuning.yml`):** Referenced in architecture specs as automated trainer, but the file is **absent** from the repo.
* **Tree-Sitter Code Learning (`backend/tools/learning/style_learner.py:L20+`):** Looks for missing `build/my-languages.so`; skips AST parsing and falls back to hardcoded dictionaries.
* **Dynamic AI Learning Engine (`backend/services/dynamic_ai/orchestrator.py:L30+`):** Missing learning engine falls back to raising `NotImplementedError`.

### 7.2 Simulated Providers & Fabricated Execution at Runtime
* **CloudSandboxOrchestrator (`backend/core/orchestration/cloud_sandbox_orchestrator.py:L46–60`):** `_get_base_url()` raises `ValueError("Unsupported provider: local")` for `provider="local"`. In `sandbox_api.py:L64` local provider is passed ➔ **all sandbox endpoints fail with HTTP 500**.
* **CompetitiveKit MultiLLMRouter (`backend/core/competitive_kit.py:L1266`):** `_call_llm()` does `await asyncio.sleep(0.1)` and returns fabricated template string instead of invoking SDK.
* **MockMessagingAdapter (`backend/core/messaging/service.py:L10–17`):** Returns dummy `MessageResult(success=True, message_id=uuid4(), provider="mock")` without provider contact. Real Telegram and Email adapters are commented out.
* **TaskRunnerAgent (`backend/core/agents/framework/task_runner_agent.py:L166–210`):** Pipeline steps return placeholder text strings: `"Investigation complete."`, `"Fix applied."`, `"Implementation placeholder"`.
* **DatabaseHealthAgent (`backend/core/agents/legacy/system_health_agent.py:L106–143`):** Evaluates `is_connected = pool is not None or True` — the `or True` causes the check to always pass as healthy regardless of database state.
* **VoiceService (`backend/services/voice_service.py:L27–53`):** `speech_to_text()` returns hardcoded transcript `"SupremeAI 2.0 সিস্টেমকে ভয়েস কমান্ড দেওয়া হচ্ছে।"`. `text_to_speech()` fails to return audio bytes, causing `stream_voice_sse.py` to fall back to dummy header `b"RIFF....WAVEfmt ...."`.
* **CommandCenter Sub-Routers (`backend/api/routes/commandcenter/{overview,build,money,observe,operate,secure,system}.py`):** Return hardcoded zeros, empty arrays, or blank responses with no live metrics.

### 7.3 Explicitly Unimplemented / Stubbed Plugins & Tools
* **Experimental Plugins (`backend/core/plugins/experimental/`):** `gmail_plugin.py`, `google_drive_plugin.py`, `slack_plugin.py`, `telegram_plugin.py`, and `notion_plugin.py` all unconditionally raise `NotImplementedError`.
* **Official Google Drive Plugin (`backend/core/plugins/official/google_drive_plugin.py`):** Empty shim importing and delegating to experimental plugin, which raises `NotImplementedError`.
* **Official GitHub Plugin (`backend/core/plugins/official/github_plugin.py:L45`):** `create_pr()` returns fake mock `{"status": "success", "pr_number": 999, "html_url": "https://github.com/mock/pr/999"}`.
* **Integration Endpoints (`backend/api/routes/integrations.py`):** `dock_slack_endpoint` returns HTTP 501; `gmail_oauth_callback` raises `NotImplementedError` ➔ HTTP 501.
* **MCP Skeleton Stubs (`backend/adaptive_engine/mcp_skeleton.py`):** Operations return `{"forecast": "stub"}`, `{"correlations": [], "note": "stub"}`.
* **Creative Tools (`backend/tools/creative/__init__.py`):** Empty package containing only a comment.

---

## 8. Class C: Orphan Backend Surface (P1 — 57 Route Families)

Static route reconstruction confirms 57 route families whose leaf endpoints are never called by `frontend/src`:

1. **Missions Engine (11 Endpoints):** `POST /api/v1/missions`, `GET /api/v1/missions`, `GET /api/v1/missions/{id}`, `POST /api/v1/missions/{id}/start`, `advance`, `approve`, `fail`, `repair`, `cancel`, `trace`, `trace/stream`.
2. **MCP Hub & Client Management (7 Endpoints):** `GET /api/v1/mcp/gateway`, `POST /api/v1/mcp/slug/claim`, `GET /api/v1/mcp/clients`, `POST /api/v1/mcp/clients`, `GET /api/v1/mcp/clients/{id}`, `rotate`, `DELETE /api/v1/mcp/clients/{id}`.
3. **Capability Circles (4 Endpoints):** `GET /api/v1/circles`, `GET /api/v1/circles/health`, `GET /api/v1/circles/events`, `POST /api/v1/circles/dispatch`.
4. **Entire CommandCenter Admin API:** `/admin-api/commandcenter/{build/*, events, health, metrics, money/*, observe/*, operate/*}`.
5. **Six Image Transformation Tools:** `/tools/image-to-code`, `/tools/image-to-component`, `/tools/image-to-palette`, `/tools/image-to-tree`, `/tools/smell-check`, `/tools/vulnerability-check`.
6. **Admin & Governance Endpoints:** `/admin-api/cost-caps`, `/admin-api/data-export`, `/admin-api/health-stream` (WS), `/admin-api/ping-all`, `/admin-api/service-topology`, `/admin/free-tier-status`, `/admin/token-budget-stats`, `/config/validation-report`.
7. **Agent & Memory Endpoints:** `/api/admin/cloud-mesh/*`, `/api/knowledge/ask-scribe`, `/api/memory/recall`, `/voice/process-audio`, `/ws/cost-updates` (WS), `/api/v1/meta-ai/*` (8 routes), `/diagram/{api-spec,to-kubernetes,to-schema,to-terraform}`.
8. **Double-Prefix Anomaly (`ERR-M06`):** `/api/admin-api/provider-readiness` and `/api/admin-api/test-service` concatenate prefixes.

---

## 9. Class S: Security, Guard-Consistency & Network Defects (P0/P1)

### 9.1 `ERR-S01` (P0): Inconsistent `mock-` Token Acceptance in Admin Auth
* `backend/core/admin_routes.py` enforces asymmetric policies for the `mock-` token prefix:
  * `/api/admin/firebase-login` and `/firebase-totp-setup` use strict allow-lists (`env in {local, test}`).
  * `/api/admin/firebase-totp-recover` and `/firebase-totp-verify` use deny-lists (`env == "production"` only).
  * `_ensure_admin_authorized()` returns early without checking Firestore if `env != "production"`.
* **Consequence:** If `ENV` is unset or misspelled, `config.py` defaults to `local`, allowing deny-list endpoints to accept `mock-*` tokens and mint admin JWTs with full permissions. Furthermore, `config.py` treats `ENV=prod` as production, but `admin_routes.py` checks literal `"production"`.

### 9.2 `ERR-S02` (P1): Production CORS Failure & Idempotency Key Workaround
* `frontend/src/services/apiClient.ts:262–279` hardcodes `IDEMPOTENCY_REQUIRED_PREFIXES` to avoid sending `idempotency-key` on unlisted routes because the deployed backend's CORS policy rejects OPTIONS requests with `400 Disallowed CORS headers`.
* Starlette CORS configuration must explicitly include `idempotency-key` in `allow_headers`.

---

## 10. Class M: Governance, CI & Tooling Defects ("Gates That Don't Gate")

| ID | Artifact | Defect | Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **ERR-M01** | `scripts/find_stub_data.py` | Scans for only 20 literal regexes. Completely blind to `mock`, `fake`, `Math.random`, or canned responses. | Prints `[PASS] No stub patterns found` on `backend/` despite 1,157 stubs. | ❌ OPEN |
| **ERR-M02** | `.github/workflows/ci.yml` | The stub-blocker gate is not wired into GitHub Actions CI at all. | Developers without local pre-commit hooks push stubs without blocking. | ❌ OPEN |
| **ERR-M03** | `scripts/feature_parity_sentinel.py:729` | Crashes on Windows with `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f50d'` (emoji). | Sentinel cannot be run locally on Windows development machines. | ❌ OPEN |
| **ERR-M05** | Remote Refs | ~320 stale remote branches fetched locally. | Clutters branch discovery and git status. | ❌ OPEN |
| **ERR-M08** | `.gitignore:479` | Blanket `*.txt` rule previously ignored audit evidence in `docs/audits/evidence/`. | Scoped negation rule `!docs/audits/evidence/**` added to keep audit evidence committed. | ✅ FIXED |

---

## 11. Class P: Dependency & Version Inconsistencies

* **`ERR-P01`: Intra-Package Storybook Conflict:** `frontend/package.json` declares `"storybook": "^10.5.10"` alongside v8 addons (`@storybook/addon-essentials: ^8.6.14`, `@storybook/blocks: ^8.6.14`). `addon-essentials` was removed in Storybook 10.
* **`ERR-P02`: React Router Major Drift:** `"react-router-dom": "^6.30.6"` prevents updating modern routing features and blocks Dependabot updates.

---

## 12. Class E: Test Debt & Skipped Test Cases (Formal Registry Summary)

Source registry: `docs/SKIPPED_TESTS.md`. Total skipped test markers: **96 active** across 52 test files.

* **28 Intentional Skips:** Live external infrastructure requiring credentials (live S3, live Stripe webhook, Cloudflare live purge, OS symlink probes).
* **68 Deferred Ticket Skips (Actionable Debt):**
  * **14 Configuration Fail-Fast Tests:** `test_settings_redis_url`, `test_settings_stripe_configuration`, `test_settings_encryption_key_not_empty`.
  * **22 Model Router & Gateway Tests:** Stale mocks targeting refactored `services/llm/` surfaces; Qdrant mock attribute mismatches.
  * **16 Security & Sandbox Boundary Tests:** `test_sandbox_root_validation`, `test_safe_vm_path_within_sandbox`, `test_god_mode_session_logs_ip_address`.
  * **16 E2E Playwright Specs:** Awaiting mock backend database seeding.

---

## 13. Class F: Core Architectural Debt & Subsystem Duplication

| ID | Subsystem | Flaw / Gap | Architectural Target | Status |
| :--- | :--- | :--- | :--- | :--- |
| **ERR-F01** | **Execution State Machine** | No canonical `Run` model. Execution tracking is split across `automation_execution`, `execution_log`, and `pending_tasks`. | **M1: Canonical Run Fabric** (Unified run state machine, budgeting, retry classification). | ❌ OPEN |
| **ERR-F02** | **Memory Subsystem** | 15+ competing memory store implementations under `backend/memory/` (`chromadb`, `sqlite`, `hierarchical_tree`, `episodic`). | **M3: Memory Consolidation** (Retire duplicate stores; consolidate on `ai_memory` vector 384). | ❌ OPEN |
| **ERR-F03** | **Context Assembly** | Unstructured prompt assembly with no token budgeting causes context bloat and provider rate limits. | **M2: Context Engine** (Smallest-sufficient-context assembly). | ❌ OPEN |
| **ERR-F04** | **Frontend Major Upgrades** | Breaking changes blocked on `react-router-dom` (v6→v7), `react-i18next` (v15→v17), `@storybook` (v8→v10). | Dedicated frontend dependency upgrade sprint. | ❌ OPEN |

---

## 14. Master Priority Remediation Roadmap

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ P0 — IMMEDIATE (1–3 Days: Silent Wrongness, Financial Risk & Hard Failures)              │
│  1. ERR-G01: ✅ FIXED — Eliminate billing mock checkout; return explicit error if Stripe key unset │
│  2. ERR-G02: ✅ FIXED — Remove fake production_deploy simulation; require real runner             │
│  3. ERR-S01: ✅ FIXED — verified on main: single fail-closed allow-list gate on every mock-token site + 'prod' treated as production (register was stale) │
│  4. ERR-H01: ✅ FIXED (PR #383) — all 5 callers on the real contract; extended prefs really persist │
│  5. ERR-A01 & A02: ✅ FIXED — AgentWorkspace task_id injection & plural endpoint fixed           │
│  6. ERR-H06: ✅ FIXED (PR #384) — real implementation (arXiv search / summarization / citations)  │
│  7. ERR-H02: ✅ FIXED (PR #385) — real install state + uninstall + deploy-blueprint                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ P1 — CORE (1–2 Weeks: Operational Reality & Control Plane Integrity)                   │
│  8. ERR-M01 & M02: ✅ FIXED (PR #387) — hardened scanner + 'stub-blocker' CI job (--fail-on HIGH) │
│  9. ERR-H04: ❌ OPEN — Wire or delete the 17 dead ecosystem admin endpoints                      │
│ 10. ERR-H07 & H08: ❌ OPEN — Unify dual agent routers and offload sync execute to thread pool   │
│ 11. ERR-G03–G06: ✅ MOSTLY FIXED — Crown jewel & sandbox stubs replaced with real runners         │
│ 12. ERR-B01 & B02: ❌ OPEN — Implement Project Space modal and File dropzone components          │
│ 13. ERR-F01: ❌ OPEN — Implement M1 Canonical Run Fabric                                         │
│ 14. ERR-S02: ✅ FIXED (PR #388) — live CORS allow-list verified; server.py synced; client scope documented │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ P2 — HARDENING & POLISH (2–3 Weeks: Long-Term Reliability & Hygiene)                   │
│ 15. ERR-M03: ✅ FIXED (PR #388) — main() reconfigures stdout/stderr to UTF-8; verified under cp1252 │
│ 16. ERR-F02: ❌ OPEN — M3 Memory consolidation (archive 15+ duplicate memory stores)             │
│ 17. Class C: ❌ OPEN — Wire-or-delete triage for 57 orphan backend route families                │
│ 18. Class E: ❌ OPEN — Burn down 68 deferred skipped test tickets                                 │
│ 19. ERR-P01 & P02: ❌ OPEN — Reconcile Storybook v8/v10 and migrate react-router-dom to v7      │
│ 20. ERR-M05: ❌ OPEN — Prune ~320 stale remote branches                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Methodology, Reproduction Commands & Verification Limits

### Execution Commands
```bash
# 1. Generate full route and call census evidence:
python scripts/audit/system_deep_scan_2026_09_15.py

# 2. Audit stub/placeholder markers:
python scripts/find_stub_data.py --path backend --fail-on HIGH

# 3. Route parity sentinel scan:
python scripts/feature_parity_sentinel.py --fail-on never
```

### Verification Limits & Reality Checks
* All HTTP 404/422/500 classifications derive from AST route table reconstruction and source code analysis.
* `ERR-S01` is a static analysis finding based on conditional logic in `admin_routes.py` and defaults in `config.py`.
* `docs/audits/evidence/` contains raw text outputs for full traceability.
* Status verification performed against live `main` branch at commit `52519ad1` (2026-09-16).
