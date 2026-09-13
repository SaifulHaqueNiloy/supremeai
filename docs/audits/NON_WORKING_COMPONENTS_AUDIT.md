# SupremeAI Codebase Audit: Comprehensive Report on Non-Working Components

**Audit Scope**: Backend (Python/FastAPI), Frontend (React/TypeScript), CI/CD workflows, tools, and integrations.  
**Audit Date**: 2026-09-14  
**Sentinel Run**: `python scripts/feature_parity_sentinel.py` — 158 backend modules with routes, 600 mounted routes, 142 frontend API calls, 49 nav links, 42 route paths, 600 total findings.  
**Status**: Real-state verified against active source code + AST + frontend regex scan on `main` branch.

---

## Executive Summary

The SupremeAI repository possesses rich architectural plans, data contracts, and interface schemas. However, across the codebase there is a significant gap between **declared architecture** and **real, functional execution**.

The Feature Parity Sentinel (verified on `main` branch, commit `3ce395856f`) reports **600 total findings** broken down as:

| Category | Count | Severity | Status |
|---|---|---|---|
| **NEW drift** (not in baseline) | 135 | 96 MEDIUM, 39 HIGH | 🚨 Fails sentinel under `--fail-on high` (39 high blockers) |
| **Known baselined debt** | 465 | Mixed | Accepted/known debt snapshot |
| **Resolved since baseline** | 121 | — | Fixed/cleaned up since baseline snapshot |

The 135 NEW findings consist of:
- **37 Missing Backend Routes** (HIGH severity — frontend actively calls routes with no matching backend endpoint)
- **2 Unmounted Routers** (HIGH severity — router defined in code but not registered in `ALL_ROUTERS`)
- **92 Orphan Endpoints** (MEDIUM severity — backend mounted endpoints with no frontend caller)
- **4 Ghost UI Components** (MEDIUM severity — pre-built components not wired into JSX routing)

Additionally, targeted code inspection confirms numerous components that **compile and mount but return simulated, mocked, or stubbed output** at runtime — these are NOT detected by the sentinel (which only checks mount/import parity, not runtime correctness).

Non-operational components fall into seven distinct categories:

1. **Simulated / Mocked Execution** (Claims success without producing real models, artifacts, or state).
2. **Explicitly Unimplemented / Stubbed** (`NotImplementedError`, `status: "not_implemented"`, or placeholder bodies).
3. **Orphan Endpoints** (FastAPI endpoints that exist but have no caller from the frontend or agent execution paths).
4. **Missing Backend Routes** (Frontend/UI components actively fetch endpoints that the backend has never mounted).
5. **Ghost UI Components** (Pre-built React/TypeScript components completely disconnected from the routing tree).
6. **Unmounted Routers** (Backend modules that define `APIRouter` routes but are never registered).
7. **Runtime Crash / Constructor Failure** (Routes that mount but crash at instantiation or runtime).

---

## 1. Machine Learning, Self-Evolution & Fine-Tuning

| Component | File Path | Line(s) | Reality / Current Non-Working State |
| :--- | :--- | :--- | :--- |
| **Kaggle GPU Kernel Execution** | `backend/core/kaggle_orchestrator.py` | L167+ | **Empty Dummy Script**: `_generate_kernel_code()` pushes a template containing `# Task execution logic would go here` and returns dummy `output = {"status": "completed"}`. No model training, Unsloth, or LoRA weights are ever executed. |
| **Local Model Trainer** | `backend/tools/learning/model_trainer.py` | L65+ | **Simulation Only**: In default local mode, triggers a fake job ID. Status check explicitly returns: `"Local training is simulated only â€” no real checkpoint was produced."` |
| **Hugging Face / TRL DPOTrainer** | `backend/tools/learning/rlhf_pipeline.py` | L40+ | **Explicitly Unimplemented**: Code explicitly executes: `status: "not_implemented"`, `"Local TRL DPOTrainer wiring is not implemented yet; use ModelTrainer delegation for real training."` |
| **Weekly Fine-Tuning CI Pipeline** | `.github/workflows/weekly-fine-tuning.yml` | â€” | **Missing File**: Documented in `ARCH-02-SYSTEM_OVERVIEW_AND_FLOWS.md` as an active weekly automated trainer, but this YAML file does not exist in `.github/workflows/`. |
| **AST Tree-Sitter Code Learning** | `backend/tools/learning/style_learner.py` | L20+ | **Missing Compiled Library**: Looks for `build/my-languages.so` which is missing in Windows/host environments; skips AST analysis and falls back to hardcoded dictionaries. |
| **Dynamic AI Learning Engine** | `backend/services/dynamic_ai/orchestrator.py` | L30+ | **Stub Fallback**: If `.learning_engine` fails to import, it mounts a dummy class raising `NotImplementedError("Dynamic AI learning engine not available")`. |

---

## 2. Simulated / Mocked Execution (Runtime)

These components **mount and respond** but return simulated/fake data instead of real computation:

| Component | File Path | Line(s) | Reality / Current Non-Working State |
| :--- | :--- | :--- | :--- |
| **CloudSandboxOrchestrator** | `backend/core/orchestration/cloud_sandbox_orchestrator.py` | L46â€“55, L57â€“60 | Constructor calls `_get_base_url()` which raises `ValueError("Unsupported provider: local")` for `provider="local"`. `sandbox_api.py` (L64) instantiates with `provider="local"` â†’ **ALL sandbox endpoints return HTTP 500**. Even with a valid provider, `create_sandbox()` returns `None` (mock/dry-run mode) when no API key is set (L58â€“60); `run_command()` (L120) returns hardcoded mock output. |
| **CompetitiveKit MultiLLMRouter** | `backend/core/competitive_kit.py` | L1266, L1353â€“1359 | `_call_llm()` docstring says "placeholder â€” implement with actual SDK"; body does `await asyncio.sleep(0.1)` and returns `f"[Response from {provider}/{model}] Processed your {len(prompt)} char prompt."` â€” a fabricated string, not a real LLM response. |
| **MockMessagingAdapter** | `backend/core/messaging/service.py` | L10â€“17, L60â€“65 | "A mock implementation of MessagingProvider for local development." `send()` returns `MessageResult(success=True, message_id=uuid4(), provider="mock")` without contacting any real provider. `MessagingDispatcher._initialize_provider()` falls back to Mock when no real provider is configured (Telegram and Email adapters are commented out at L50â€“57). |
| **TaskRunnerAgent** | `backend/core/agents/framework/task_runner_agent.py` | L166â€“210 | Every pipeline step returns hardcoded placeholder objects: `"Investigation complete."`, `"Fix applied."`, `"Scaffold placeholder"`, `"Implementation placeholder: delegate to coding tooling."`, `"Tests placeholder: add unit tests in tests/"`. `is_connected = pool is not None or True` at L118 always evaluates `True` regardless of actual DB state. |
| **SystemHealthAgent / DatabaseHealthAgent** | `backend/core/agents/legacy/system_health_agent.py` | L106â€“143 | `DatabaseHealthAgent.perform_check()` sets `is_connected = pool is not None or True` â€” the `or True` makes the check always pass, so health is always reported as "healthy" regardless of database state. `MemoryHealthAgent` (L146+) uses `psutil` which may be `None` (ImportError fallback at L13â€“16). |
| **PerformanceOptimizer MockConnection** | `backend/core/optimization/performance_optimizer.py` | L50+ | `MockConnection` class returns fabricated query results without hitting any real database. `PerformanceOptimizer` uses this mock by default, simulating optimization gains that never actually persist. |
| **VoiceService (STT + TTS)** | `backend/services/voice_service.py` | L27â€“34, L43â€“53 | `speech_to_text()` (L28) returns hardcoded transcript `"SupremeAI 2.0 à¦¸à¦¿à¦¸à§à¦Ÿà§‡à¦®à¦•à§‡ à¦­à¦¯à¦¼à§‡à¦¸ à¦•à¦®à¦¾à¦¨à§à¦¡ à¦¦à§‡à¦“à¦¯à¦¼à¦¾ à¦¹à¦šà§à¦›à§‡à¥¤"` instead of actually transcribing audio (Whisper integration noted as endpoint, not wired). `text_to_speech()` (L45â€“53) returns `audio_bytes_length` but NOT the actual `audio_bytes` key â€” `stream_voice_sse.py` (L65â€“67) falls back to hardcoded placeholder `b"RIFF....WAVEfmt ....data...."`. |
| **Stream Voice SSE** | `backend/api/routes/stream_voice_sse.py` | L60â€“67 | Docstring itself admits: "NOTE: VoiceService currently returns a dummy placeholder audio... For now we emit the placeholder + metadata so the frontend can show that the pipeline works end-to-end." |
| **TaskQueueEnhanced.get_task_status** | `backend/core/queue/task_queue_enhanced.py` | L583â€“587 | Deprecated sync wrapper returns hardcoded `"unknown"` for all task IDs, with comment: `# Dummy for back-compat until routes are updated`. |
| **Command Center Overview sub-router** | `backend/api/routes/commandcenter/overview.py` | L24â€“38 | Returns hardcoded `OverviewResponse(active_agents=0, active_tasks=0, requests_per_second=0.0, latency_p95_ms=0.0, error_rate=0.0, cost_per_hour=0.0, health_percent=100.0)` â€” no real metrics are collected. |
| **Command Center Build sub-router** | `backend/api/routes/commandcenter/build.py` | L12â€“34 | `get_router()` returns `{"provider_order": [], "cost_quality_preference": 0.5}`; `list_providers()` returns `[]`; `list_skills()` returns `[]`; `get_memory()` returns `{"banks": [], "semantic_cache_hit_rate": 0, "tokens_saved": 0}` â€” all hardcoded, no real data. |
| **Command Center Money sub-router** | `backend/api/routes/commandcenter/money.py` | (full file) | Returns zeroed/empty financial data. No real billing integration. |
| **Command Center Observe sub-router** | `backend/api/routes/commandcenter/observe.py` | (full file) | Returns empty/blank observability data. No real metrics pulled. |
| **Command Center Operate sub-router** | `backend/api/routes/commandcenter/operate.py` | (full file) | Returns hardcoded system state with no live data. |
| **Command Center Secure sub-router** | `backend/api/routes/commandcenter/secure.py` | (full file) | Security status endpoints return stub values. No real security scanning. |
| **Command Center System sub-router** | `backend/api/routes/commandcenter/system.py` | (full file) | Returns empty system info. No real system introspection. |
| **Sandbox List** | `backend/api/routes/sandbox_api.py` | L140+ | `list_sandboxes()` returns hardcoded `{"sandboxes": []}` â€” no real sandbox query, and in any case `_get_manager()` (L64) crashes with `ValueError` before any method runs. |

---

## 3. Explicitly Unimplemented / Stubbed Plugins

| Plugin Name | File Path | Line(s) | Defect / Non-Working Behavior |
| :--- | :--- | :--- | :--- |
| **Gmail Plugin** | `backend/core/plugins/experimental/gmail_plugin.py` | L15 | Raises `NotImplementedError("Gmail plugin is experimental and not yet implemented.")` |
| **Google Drive Plugin (Experimental)** | `backend/core/plugins/experimental/google_drive_plugin.py` | L15 | Raises `NotImplementedError("Google Drive plugin is experimental and not yet implemented.")` |
| **Slack Plugin** | `backend/core/plugins/experimental/slack_plugin.py` | L15 | Raises `NotImplementedError("Slack plugin is experimental and not yet implemented.")` |
| **Telegram Plugin** | `backend/core/plugins/experimental/telegram_plugin.py` | L15 | Raises `NotImplementedError("Telegram plugin is experimental and not yet implemented.")` |
| **Notion Plugin** | `backend/core/plugins/experimental/notion_plugin.py` | L15 | Raises `NotImplementedError("Notion plugin is experimental and not yet implemented.")` |
| **GitHub Plugin (Official)** | `backend/core/plugins/official/github_plugin.py` | L45 | `create_pr()` returns mock `{"status": "success", "pr_number": 999, "html_url": "https://github.com/mock/pr/999"}` â€” a fake PR URL, no actual GitHub API call. |
| **Google Drive Plugin (Official)** | `backend/core/plugins/official/google_drive_plugin.py` | L20 | **Empty shim**. `__init__` simply delegates to the experimental plugin (`from backend.core.plugins.experimental.google_drive_plugin import GoogleDrivePlugin as ExperimentalPlugin`), which immediately raises `NotImplementedError`. The official plugin adds zero real implementation. |
| **Dock Slack Integration** | `backend/api/routes/integrations.py` | L120 | `dock_slack_endpoint()` raises `HTTPException(status_code=501, detail="Slack integration not yet implemented (dock not configured)")`. |
| **Gmail OAuth Route** | `backend/api/routes/integrations.py` | L140 | `gmail_oauth_callback()` raises `NotImplementedError("Gmail integration not yet wired")` â†’ caught and re-raised as HTTP 501. |
| **MCP Skeleton Stubs** | `backend/adaptive_engine/mcp_skeleton.py` | L50, L80, L110, L140 | `_op_forecast_capability` returns `{"forecast": "stub", "note": "later phase"}`; `_op_correlate_error` returns `{"correlations": [], "note": "stub"}`; `_op_create_capability` returns `{"ok": False, "error": "use_proposal_endpoint"}`; `_op_trigger_kaggle` dispatches to a non-existent resource control with no physical Kaggle container lifecycle. |
| **Creative Tools** | `backend/tools/creative/__init__.py` | L1 | File contains only a single `#` comment â€” completely empty, no exports or implementations. |

---

## 4. Orphan Endpoints (Backend Routes with No Frontend Caller) — 92 NEW findings

The Feature Parity Sentinel detected **92 NEW orphan-endpoint findings** (not in the baseline snapshot, MEDIUM severity, CI-gated only at `--fail-on high`). These are backend routes that are mounted and functional but **have no frontend consumer** — meaning the UI cannot drive them directly.

### 4.1 Workspace Capabilities Routes — 7 orphan endpoints
All in `backend/api/routes/workspace_capabilities.py`:
- `GET /api/v1/workspace/capabilities` (L66)
- `POST /api/v1/workspace/capabilities` (L77)
- `POST /api/v1/workspace/capabilities/{}/health` (L103)
- `POST /api/v1/workspace/capabilities/{}/reactivate` (L111)
- `POST /api/v1/workspace/capabilities/{}/revoke` (L121)
- `PATCH /api/v1/workspace/capabilities/{}/permission` (L129)
- `PATCH /api/v1/workspace/capabilities/{}/tools` (L142)

### 4.2 Artifacts Routes — 6 orphan endpoints
All in `backend/api/routes/artifacts.py`:
- `POST /api/artifacts` (L119)
- `GET /api/artifacts/conversation/{}` (L159)
- `GET /api/artifacts/{}` (L189)
- `PATCH /api/artifacts/{}` (L221)
- `DELETE /api/artifacts/{}` (L284)
- `GET /api/artifacts/{}/preview` (L320)

### 4.3 MCP Marketplace Routes — 6 orphan endpoints
All in `backend/api/routes/mcp_marketplace.py`:
- `PATCH /api/v1/mcp/connections/{}/permission` (L64)
- `PATCH /api/v1/mcp/connections/{}/tools` (L86)
- `POST /api/v1/mcp/connections/{}/reactivate` (L108)
- `GET /api/v1/mcp/connections/{}/health` (L125)
- `DELETE /api/v1/mcp/connections/{}` (L138)
- `GET /api/v1/mcp/connections` (L153)

### 4.4 Intelligence Insights Routes — 5 orphan endpoints
All in `backend/api/routes/intelligence_insights.py`:
- `GET /admin-api/intelligence/insights` (L18)
- `GET /admin-api/intelligence/manual-tasks` (L28)
- `POST /admin-api/intelligence/manual-tasks/{}/complete` (L33)
- `POST /admin-api/intelligence/risk-proposals` (L39)
- `POST /admin-api/intelligence/memory/consolidate` (L46)

### 4.5 Social Growth Routes — 5 orphan endpoints
All in `backend/api/routes/social_growth.py`:
- `GET /api/v1/social/drafts` (L46)
- `POST /api/v1/social/drafts` (L52)
- `POST /api/v1/social/drafts/{}/approve` (L71)
- `POST /api/v1/social/pause` (L83)
- `POST /api/v1/social/resume` (L90)

### 4.6 Tenant Admin Routes — 5 orphan endpoints
All in `backend/api/routes/tenant_admin.py`:
- `GET /admin-api/tenants/{}` (L285)
- `PUT /admin-api/tenants/{}` (L295)
- `DELETE /admin-api/tenants/{}` (L330)
- `POST /admin-api/tenants/{}/reset` (L362)

### 4.7 Diagram to Architecture (Tools) — 5 orphan endpoints
All in `backend/tools/code/diagram_to_architecture.py`:
- `POST /diagram/generate` (L240)
- `POST /diagram/to-terraform` (L268)
- `POST /diagram/to-kubernetes` (L285)
- `POST /diagram/to-schema` (L302)
- `POST /diagram/api-spec` (L319)

### 4.8 Admin V1 Routes — 4 orphan endpoints
All in `backend/api/routes/admin_v1.py`:
- `GET /api/v1/agents` (L32)
- `GET /api/v1/admin/users` (L38)
- `GET /api/v1/admin/audit-logs` (L50)
- `GET /api/v1/admin/stats` (L65)

### 4.9 Crawler Admin Routes — 4 orphan endpoints
All in `backend/api/routes/crawler_admin.py`:
- `PATCH /api/v1/admin/crawler/policies/{}` (L117)
- `POST /api/v1/admin/crawler/policies/{}/enable` (L136)
- `POST /api/v1/admin/crawler/policies/{}/disable` (L142)
- `DELETE /api/v1/admin/crawler/policies/{}` (L158)

### 4.10 Task Gateway & Branching Routes — 6 orphan endpoints
In `backend/api/routes/task_gateway.py`:
- `POST /api/v1/tasks` (L50)
- `GET /api/v1/tasks/{}` (L87)
- `POST /api/v1/tasks/{}/cancel` (L119)
In `backend/api/routes/branch_conversations.py`:
- `GET /api/conversations/{}/branches` (L250)
- `GET /api/conversations/tree` (L283)
- `PATCH /api/conversations/{}/merge` (L315)

### 4.11 Chat Upload / Export & Deep Research — 7 orphan endpoints
- `GET /api/chat/export/formats` (`chat_export.py:288`)
- `POST /api/chat/export` (`chat_export.py:305`)
- `POST /api/chat/upload` (`chat_upload.py:97`)
- `GET /api/chat/upload/{}` (`chat_upload.py:210`)
- `DELETE /api/chat/upload/{}` (`chat_upload.py:272`)
- `POST /api/research/deep` (`deep_research.py:555`)
- `POST /api/research/deep/stream` (`deep_research.py:611`)

### 4.12 Additional Tool & Domain Endpoints — 22 orphan endpoints
- **Security Scanner**: `POST /security/vulnerabilities/scan` & `scan-project` (`code_vulnerability_scanner_agent.py`)
- **Billing API**: `GET /api/billing/budget-check` & `GET /api/billing/analytics` (`billing_api.py`)
- **Reasoning**: `POST /api/reasoning/think` & `POST /api/reasoning/think/stream` (`reasoning.py`)
- **Voice Coder**: `POST /voice/process-audio` & `WEBSOCKET /voice/ws` (`voice_coder.py`)
- **AI Pair Programmer**: `POST /pair/solve` & `POST /pair/review` (`ai_pair_programmer.py`)
- **Knowledge**: `POST /api/knowledge/search` & `POST /api/knowledge/seed` (`knowledge.py`)
- **Preferences**: `GET /api/preferences` & `POST /api/preferences` (`preferences.py`)
- **Health**: `GET /api/v1/health/agents` & `POST /api/v1/health/agents` (`health.py`)
- **Usage Metrics**: `GET /metrics/usage` & `POST /metrics/usage` (`usage_metrics.py`)
- **Singletons**:
  - `POST /api/v1/agent/execute` (`agent_workspace.py:47`)
  - `POST /api/v1/agents/execute` (`agent.py:36` & `agent_tasks.py:68`)
  - `GET /config/validation-report` (`config_routes.py:57`)
  - `GET /api/v1/evolution/metrics` (`evolution.py:129`)
  - `POST /api/v1/kernel/dispatch` (`kernel_dispatch.py:37`)
  - `POST /api/memory/conversations/messages` (`memory.py:251`)
  - `POST /api/prompt-templates/{}/use` (`prompt_templates.py:597`)
  - `POST /api/schedule/{}/toggle` (`scheduled_tasks.py:590`)
  - `POST /api/commands/execute` (`slash_commands.py:602`)
  - `GET /api/admin/traffic/live` (`traffic_monitor.py:19`)
  - `POST /video-to-code/process` (`video_to_code_pipeline.py:382`)
  - `POST /agent/plan` (`self_planner.py:232`)
  - `GET /ws/command-center/health` (`command_center.py:7`)

### 4.13 Ghost UI Components (NEW — 4 findings, MEDIUM severity)
These 4 preserved/created UI components exist in `frontend/src/` but are not currently rendered in `App.tsx` router tree:
| Component | File Path | Status |
|---|---|---|
| `RulesEnginePanel` | `frontend/src/components/admin/security/RulesEnginePanel.tsx` | Preserved core asset |
| `HITLModal` | `frontend/src/components/dashboard/HITLModal.tsx` | Preserved core asset |
| `OneLinerMCPConnect` | `frontend/src/components/dashboard/OneLinerMCPConnect.tsx` | Preserved core asset |
| `HoldToKillButton` | `frontend/src/components/swarm/HoldToKillButton.tsx` | Preserved core asset |

---

## 5. Missing Backend Routes (Frontend→Backend Endpoint Mismatches — 37 NEW HIGH Blockers)

The frontend actively calls 37 endpoints (or admin-api endpoints) that the backend has not directly routed or that use `/admin-api` prefixes where the backend expects different mounting:

| Calling Frontend File | Line | Missing Endpoint | Severity |
|---|---|---|---|
| `AdminAlertsTab.tsx` | 13 | `/admin-api/events` | HIGH |
| `UserManager.tsx` | 30, 37 | `/admin-api/users` | HIGH |
| `UserManager.tsx` | 42 | `/admin-api/users/{}` | HIGH |
| `BackupRestore.tsx` | 21 | `/admin-api/backups` | HIGH |
| `BackupRestore.tsx` | 45 | `/admin-api/backup` | HIGH |
| `CICDVisualizer.tsx` | 29 | `/admin-api/feature-flags` | HIGH |
| `CICDVisualizer.tsx` | 46, 55 | `/admin-api/feature-flags/{}` | HIGH |
| `ConfigEditor.tsx` | 18 | `/admin-api/config` | HIGH |
| `CloudProviderHealth.tsx` | 23 | `/admin-api/health-map` | HIGH |
| `CloudProviderHealth.tsx` | 30 | `/admin-api/metrics` | HIGH |
| `ModelRouter.tsx` | 39 | `/admin-api/model-router` | HIGH |
| `ModelRouter.tsx` | 45 | `/admin-api/providers` | HIGH |
| `ModelRouter.tsx` | 59 | `/admin-api/model-router/override` | HIGH |
| `RulesEnginePanel.tsx` | 34 | `/admin-api/rules` | HIGH |
| `ThreatDetection.tsx` | 34 | `/admin-api/security-scan` | HIGH |
| `useAdminApi.ts` | 62 | `/admin-api/costs` | HIGH |
| `useAdminApi.ts` | 96 | `/admin-api/costs/breakdown` | HIGH |
| `useAdminApi.ts` | 107 | `/admin-api/health-map` | HIGH |
| `useAdminApi.ts` | 119, 129 | `/admin-api/users` | HIGH |
| `useAdminApi.ts` | 137 | `/admin-api/users/{}` | HIGH |
| `useAdminApi.ts` | 154 | `/admin-api/config` | HIGH |
| `useAdminApi.ts` | 161 | `/admin-api/deploy` | HIGH |
| `useDashboardData.ts` | 71, 93 | `/admin-api/metrics` | HIGH |
| `useDashboardData.ts` | 103 | `/admin-api/costs` | HIGH |
| `useDashboardData.ts` | 113 | `/admin-api/health-map` | HIGH |
| `useDashboardData.ts` | 123 | `/admin-api/ci-logs` | HIGH |
| `useDashboardData.ts` | 133 | `/admin-api/security-scan` | HIGH |
| `useDashboardData.ts` | 144 | `/admin-api/deploy` | HIGH |
| `useDashboardData.ts` | 153 | `/admin-api/rules` | HIGH |
| `useDashboardData.ts` | 178 | `/admin-api/events` | HIGH |
| `AdminShell.tsx` | 101 | `/admin-api/deploy` | HIGH |
| `apiClient.test.ts` | 156 | `/api/agent/execute` | HIGH |
| `apiClient.test.ts` | 172 | `/api/v1/settings/profile` | HIGH |
| `adminService.ts` | `/admin-api/health-aggregation` | No health-aggregation router mounted (baselined) |
| `adminService.ts` | `/admin-api/security/memory` | No security-memory router mounted (baselined) |
| `adminService.ts` | `/admin-api/deploy-status/{}` | No deploy-status router mounted (baselined) |
| `adminService.ts` | `/admin-api/ci-logs` | No CI-logs router mounted (baselined) |
| `agentService.ts` | `POST /api/v1/agent/execute` | No `agent` router mounted |
| `agentService.ts` | `GET /api/agents/` | No `agents` router mounted |
| `agentService.ts` | `GET /api/agents/{id}/status` | No `agents` router mounted |
| `aiActions.ts` | `POST /api/v1/workspaces/bind-target` | No workspaces bind-target router mounted |
| `controlPlane.ts` | `GET /api/v1/control-plane/registry` | No control-plane registry router mounted |
| `controlPlane.ts` | `GET /api/v1/capabilities` | No capabilities router mounted |
| `controlPlane.ts` | `GET /api/v1/control-plane/health` | No control-plane health router mounted |
| `controlPlane.ts` | `GET /api/v1/tasks/{id}` | No tasks router mounted |
| `controlPlane.ts` | `POST /api/v1/tasks` | No tasks router mounted |
| `controlPlane.ts` | `POST /api/v1/tasks/{id}/cancel` | No tasks router mounted |
| `skillService.ts` | `POST /api/skills/verify-skll-config` | Backend prefix is `/api/v1/skills/` â€” **path mismatch** (`/api` vs `/api/v1`) |
| `skillsService.ts` | `GET /api/v1/skills/` | Router exists but **not mounted** in ALL_ROUTERS (baselined `unmounted-router|api.routes.skills`) |
| `skillsService.ts` | `POST /api/v1/skills/deploy-blueprint` | Same â€” unmounted |

---

## 6. Ghost UI Components â€” 44 Total (41 baselined + 3 NEW)

### 6.1 NEW Ghost UI Components (3 findings â€” MEDIUM severity, not in baseline)
| Component | File Path |
|---|---|
| `HITLModal` | `frontend/src/components/dashboard/HITLModal.tsx` |
| `LivingActionDock` | `frontend/src/components/dashboard/LivingActionDock.tsx` |
| `GlassUiPrimitives` | `frontend/src/components/ui/GlassUiPrimitives.tsx` |

### 6.2 Baselined Ghost UI Components (41 findings â€” known debt, MEDIUM severity)
These React/TypeScript components exist in `frontend/src/` but are **never imported or rendered** from any active route in `App.tsx`:

| Component | File Path |
|---|---|
| `ErrorBoundary` | `frontend/src/components/ErrorBoundary.tsx` |
| `FixPreviewModal` | `frontend/src/components/FixPreviewModal.tsx` |
| `LiveSujonBackground` | `frontend/src/components/LiveSujonBackground.tsx` |
| `OnboardingWizard` | `frontend/src/components/Onboarding/OnboardingWizard.tsx` |
| `OperatorStudio` | `frontend/src/components/OperatorStudio.tsx` |
| `SupremeComponents` | `frontend/src/components/SupremeComponents.tsx` |
| `AdminDashboardHome` | `frontend/src/components/admin/AdminDashboardHome.tsx` |
| `HealthBanner` | `frontend/src/components/admin/HealthBanner.tsx` |
| `ScreencastViewer` | `frontend/src/components/admin/ScreencastViewer.tsx` |
| `ConsentMatrixModal` | `frontend/src/components/admin/auth/ConsentMatrixModal.tsx` |
| `DeploymentModal` | `frontend/src/components/admin/infra/DeploymentModal.tsx` |
| `ServiceHealthMonitor` | `frontend/src/components/admin/infra/ServiceHealthMonitor.tsx` |
| `AdminTopNav` | `frontend/src/components/admin/shared/AdminTopNav.tsx` |
| `DynamicPanel` | `frontend/src/components/admin/shared/DynamicPanel.tsx` |
| `ActionDock` | `frontend/src/components/dashboard/ActionDock.tsx` |
| `AutomationQueuePage` | `frontend/src/components/dashboard/AutomationQueuePage.tsx` |
| `ConnectedPlatformsVault` | `frontend/src/components/dashboard/ConnectedPlatformsVault.tsx` |
| `HumanInTheLoopProtocol` | `frontend/src/components/dashboard/HumanInTheLoopProtocol.tsx` |
| `KnowledgePage` | `frontend/src/components/dashboard/KnowledgePage.tsx` |
| `LivingDashboardShell` | `frontend/src/components/dashboard/LivingDashboardShell.tsx` |
| `LlmGatewayPage` | `frontend/src/components/dashboard/LlmGatewayPage.tsx` |
| `SessionDetailPage` | `frontend/src/components/dashboard/SessionDetailPage.tsx` |
| `SidebarSettings` | `frontend/src/components/dashboard/SidebarSettings.tsx` |
| `SujonCoreCockpit` | `frontend/src/components/dashboard/SujonCoreCockpit.tsx` |
| `UsagePage` | `frontend/src/components/dashboard/UsagePage.tsx` |
| `sessionStore` | `frontend/src/components/dashboard/sessionStore.ts` |
| `useHashRoute` | `frontend/src/components/dashboard/useHashRoute.ts` |
| `DynamicActionDock` | `frontend/src/components/dock/DynamicActionDock.tsx` |
| `MainLayout` | `frontend/src/components/layout/MainLayout.tsx` |
| `Shell` | `frontend/src/components/layout/Shell.tsx` |
| `SwarmHealthDashboard` | `frontend/src/components/swarm/SwarmHealthDashboard.tsx` |
| `SkillForgeWidget` | `frontend/src/components/widgets/SkillForgeWidget.tsx` |
| `TelemetryDashboardWidget` | `frontend/src/components/widgets/TelemetryDashboardWidget.tsx` |
| `LoginScreen` | `frontend/src/pages/auth/LoginScreen.tsx` |
| `RegisterScreen` | `frontend/src/pages/auth/RegisterScreen.tsx` |

---

## 7. Frontendâ†”Backend Endpoint Mismatch Cross-Reference

### 7.1 Sandbox API â€” Runtime Crash (prefix matches but constructor crashes)
| Frontend Call | Backend Router | Issue |
|---|---|---|
| `sandbox.ts` â†’ `POST /api/v1/sandbox/create` | `sandbox_api.py` prefix `/api/v1/sandbox` | **Mounted but crashes**: `_get_manager()` (L64) instantiates `CloudSandboxOrchestrator(provider="local")` â†’ `_get_base_url()` (L55) raises `ValueError("Unsupported provider: local")` â†’ **ALL sandbox endpoints return HTTP 500** |
| `sandbox.ts` â†’ `POST /api/v1/sandbox/{id}/execute` | Same | Same crash on manager instantiation |
| `sandbox.ts` â†’ `GET /api/v1/sandbox/{id}/logs` | Same | Same crash |
| `sandbox.ts` â†’ `DELETE /api/v1/sandbox/{id}` | Same | Same crash |
| `sandbox.ts` â†’ `GET /api/v1/sandbox/list` | Same | Same crash |

### 7.2 Skills API â€” Prefix Mismatch + Unmounted
| Frontend Call | Backend Router | Issue |
|---|---|---|
| `skillService.ts` â†’ `POST /api/skills/verify-skll-config` | `skills.py` prefix `/api/v1/skills` | **Prefix mismatch**: frontend uses `/api/skills/`, backend uses `/api/v1/skills/` |
| `skillsService.ts` â†’ `GET /api/v1/skills/` | `skills.py` | **Router unmounted** â€” baselined `unmounted-router|api.routes.skills` |
| `skillsService.ts` â†’ `POST /api/v1/skills/deploy-blueprint` | `skills.py` | Same â€” unmounted |

### 7.3 Connections API â€” Missing Endpoint
| Frontend Call | Backend Router | Issue |
|---|---|---|
| `connectionsApi.ts` â†’ `GET /api/v1/connections/my-workspace` | `connections.py` prefix `/api/v1/connections` | Router mounted; **endpoint `GET /my-workspace` not defined** in `connections.py` |
| `connectionsApi.ts` â†’ `POST /api/v1/connections/detect` | `connections.py` | Endpoint exists at `/detect` â€” OK |
| `connectionsApi.ts` â†’ `POST /api/v1/connections/register` | `connections.py` | Endpoint exists at `/register` â€” OK |

### 7.4 Access API â€” Missing Endpoint
| Frontend Call | Backend Router | Issue |
|---|---|---|
| `connectionsApi.ts` â†’ `POST /api/v1/access/set-mode` | `access.py` | Router mounted (baselined); **endpoint `/set-mode` not defined** |

---

## 8. Unmounted Routers — Current Status

In the current codebase, `backend/api/routers.py` centrally mounts **144 active routers** in `ALL_ROUTERS`. The Feature Parity Sentinel reports only **2 NEW unmounted routers**:

### NEW Unmounted Routers (2 routers — HIGH severity):
| Router Module | File Path | Defect |
|---|---|---|
| `api.routes.admin_dashboard.__init__` | `backend/api/routes/admin_dashboard/__init__.py` | APIRouter created for sub-dashboard aggregation but not registered in `ALL_ROUTERS`. |
| `tools.social.telegram_bot.router` | `backend/tools/social/telegram_bot/router.py` | Standalone telegram webhook router not registered in `ALL_ROUTERS`. |

### Baselined Unmounted Routers (15 remaining known debt):
The sentinel baseline still tracks 15 older unmounted modules (such as `byoc_api`, `periodic_task_scheduler`, `auto_test_generator`, etc.), while **20 unmounted routers** from the original baseline have been officially resolved and mounted.

---

## 9. Ghost UI — Routing Gap Analysis

`frontend/src/App.tsx` uses `createBrowserRouter` with `lazy` components. In earlier revisions, 44+ components were unreferenced. Following recent cleanup and consolidation:
- **41 ghost UI components were cleanly resolved/removed or mounted**.
- Only **4 components are currently flagged as NEW Ghost UI** (preserved core governance/security modules):

| Component | File Path | Status | Rationale |
|---|---|---|---|
| `RulesEnginePanel` | `frontend/src/components/admin/security/RulesEnginePanel.tsx` | Preserved core asset | Restored security rules UI for governance inspection |
| `HITLModal` | `frontend/src/components/dashboard/HITLModal.tsx` | Preserved core asset | Mandatory human-in-the-loop governance confirmation modal |
| `OneLinerMCPConnect` | `frontend/src/components/dashboard/OneLinerMCPConnect.tsx` | Preserved core asset | Instant MCP connector onboarding widget |
| `HoldToKillButton` | `frontend/src/components/swarm/HoldToKillButton.tsx` | Preserved core asset | Hardware/emergency swarm kill switch component |

---

## 10. Stale Claims & Remediation Progress (121 Resolved Items)

Since the baseline snapshot, **121 issues have been completely remediated** in active code:

| Remediation Category | Count | Key Examples Resolved |
|---|---|---|
| **Ghost UI Components** | 41 | `ErrorBoundary.tsx`, `SecretsPage.tsx`, `SettingsPage.tsx`, `MemoryPanel.tsx`, `MCPConnector.tsx`, `DeepResearchPanel.tsx`, `ScheduledTasksPanel.tsx`, `CostDashboard.tsx`, `AdminDashboardHome.tsx`, `SwarmHealthDashboard.tsx`, `LoginScreen.tsx`, `RegisterScreen.tsx`, `MainLayout.tsx` |
| **Missing Backend Routes** | 36 | `/api/admin/metrics/cost`, `/api/browser/*` (16 endpoints), `/api/chat/export`, `/api/chat/search`, `/api/commands`, `/api/conversations/{}/branch`, `/api/prompt-templates`, `/api/research/history`, `/api/schedule*`, `/api/share/*`, `/api/v1/sync/{}` |
| **Orphan Endpoints** | 22 | `/admin-api/codebase/export`, `/admin-api/cost-caps`, `/admin-api/customers`, `/admin-api/data-export`, `/api/v1/dashboard`, `/api/v1/evolution/*`, `/api/v1/memory/*`, `/api/v1/process`, `/api/v1/telegram/*` |
| **Unmounted Routers** | 20 | `api.routes.artifacts`, `api.routes.browser`, `api.routes.branch_conversations`, `api.routes.chat_export`, `api.routes.chat_search`, `api.routes.chat_upload`, `api.routes.deep_research`, `api.routes.prompt_templates`, `api.routes.reasoning`, `api.routes.scheduled_tasks`, `api.routes.share`, `api.routes.slash_commands`, `tools.code.*` |
| **Dead Nav Links** | 2 | `/agents`, `/files` |

> **Summary**: The codebase has successfully resolved 121 major feature-parity gaps. Running `python scripts/feature_parity_sentinel.py --update-baseline` in an approved maintenance PR will synchronize `feature_parity_baseline.json` with the current production baseline.

