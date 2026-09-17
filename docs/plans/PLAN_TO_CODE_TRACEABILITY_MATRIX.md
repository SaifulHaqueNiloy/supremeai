---
id: plan-to-code-traceability-matrix
subject: "SupremeAI Plan-to-Code Traceability Matrix"
document_role: audit
planning_authority: Architecture Governance / Planning Circle
canonical: true
status: active
evidence_state: partial
disposition: retain
last_verified: 2026-09-17
supersedes: []
superseded_by: []
target_scope: supremeai_internal
---

# SupremeAI Plan-to-Code Traceability Matrix

**Status:** active  
**Source of truth:** `docs/plans/implementation_plan.md`  
**Last verified:** 2026-09-17 (PLAN-001 prompt caching + PLAN-002 WS compaction implemented; M2 Context Engine row refreshed)

This matrix is intentionally evidence-driven. Rows must not be marked complete from documentation alone.

| Canonical area | Primary plan | Code/module evidence | API/data surface | Test/release evidence | Status | Known gap |
|---|---|---|---|---|---|---|
| Architecture governance | `architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md` | architecture docs, dependency graph, `system_dependencies` | architecture reports | architecture CI to be expanded | active | unified static/runtime graph |
| QA governance | `implementation_plan.md` | QA contract and CI workflows | `qa/checklist/core.yaml` | `qa-contract.yml`, build/security/preflight checks; M0-G: auth setups collected + 7/13 fixme converted (`docs/audits/M0_G_QA_SPEC_COMPLETION.md`) | active | 6 fixme stay honestly blocked (need product features/fixtures); broader E2E and coverage breadth |
| Memory and context | `implementation_plan.md` | memory service, vector/RAG, Files/Workspace integration; M2 Context Engine LANDED (`e48daaf0` — `backend/context_engine/` budgeted smallest-sufficient-context assembly, wired into HTTP chat route); PLAN-002 Claude-style WS compaction LANDED (`_compact_history` + hooks in `websocket_agent.py`, pure helpers in `prompt_handler.py`) | memory tables/RPCs and context APIs (`ai_memory` Phase C EXECUTED on Supabase, `docs/database/AI_MEMORY_PHASE_C_EXECUTION_EVIDENCE.md`) | retrieval and tenant-isolation tests; 20/20 contract+injector tests; live store→recall round-trip; `tests/api/test_websocket_compaction.py` 11/11 (success/fallback/bounded) + `test_websocket_agent.py` 42/42 regression | active | Context Engine measurement harness; WS compaction live 60+ turn Gate-5 evidence; L4.1 memory-store consolidation decision |
| Execution | `architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md` | `backend/runs/` — canonical Run fabric (state_machine, retry, budgets, models, service, bridges, hitl, api); `runs` + `run_events` tables (Alembic `2026_09_15_120000`, single head) | `/api/v1/runs` — 8 endpoints (create→`run_id` ack async boundary, get/list ownership-scoped, events, transition, usage admission control, classify, retry, cancel); `runs.api` mounted (148/148 registry entries); evidence bridges for mission/tool/MCP/automation paths | `tests/runs/` 116/116 — lifecycle edge-matrix + guards, retry classification (8-class) + budget exhaustion, budget admission control (overspend refused, not detected post-hoc), cancellation matrix + terminal-race honesty, per-run sequenced audit stream, unified-view query (`mission`+`tool`+`mcp`+`automation` in one table), HITL suspend/resolve loop, API contract via real app | active | dispatch-path instrumentation of live mission/tool/MCP callers (bridges ready; wiring per subsystem) + staging runtime evidence |
| Browser | `architecture/browser_automation.md` ⭐ (consolidated from EAOL + dual_channel) | lightweight scraper and Playwright browser tools | browser endpoints and artifacts | browser smoke tests where environment permits | active | unified browser contract and worker isolation |
| Control Tower/MCP | `implementation_plan.md` | MCP gateway, capability registry and orchestration | MCP/API contracts | MCP build and integration checks | active | explicit control-plane boundary |
| Production readiness | specialized production plans | Render/GitHub/Cloudflare/Infisical/Supabase configuration | env, health, migration and release contracts | release evidence and preflight; M0-A..M0-E: deps locked (openpyxl/sqlglot), alembic single-head guard in CI, dormant-module triage recorded (`docs/audits/M0_D_DORMANT_MODULE_DECISIONS.md`), script hygiene | active | staging promotion and rollback evidence |
| Cost/federation | `implementation_plan.md` | cache, queue, provider adapters and optional workers; PLAN-001 Anthropic prompt caching LANDED (`cloud_adapter.py` `_mark_anthropic_cache_blocks` on generate/stream; usage surfaces `cache_read_input_tokens`/`cache_creation_input_tokens` → Langfuse via existing trace pass-through) | quota/cost metadata incl. Anthropic cache telemetry | quota/failure/load tests; `tests/core/test_cloud_provider_cache.py` 10/10 (marker present for anthropic-family, absent for gemini/groq on generate+stream, cache metrics surfaced/zeroed) | active | measured admission and cost policy |
| Self-evolution | `implementation_plan.md` | discovery, verification and learning candidates | lesson/capability lifecycle | sandbox/promotion/rollback tests | proposed | governed promotion path |

## Required evidence for a completed row

- implementation path and caller;
- API/schema or contract reference;
- automated test evidence;
- deployment or runtime evidence where applicable;
- observability and failure behavior;
- rollback, deprecation or recovery path;
- last verified date.

## Update rule

Any code change affecting a canonical area must update this matrix or explicitly record why the matrix is unchanged.