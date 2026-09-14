# SupremeAI Plan-to-Code Traceability Matrix

**Status:** active  
**Source of truth:** `docs/plans/implementation_plan.md`  
**Last verified:** 2026-09-15

This matrix is intentionally evidence-driven. Rows must not be marked complete from documentation alone.

| Canonical area | Primary plan | Code/module evidence | API/data surface | Test/release evidence | Status | Known gap |
|---|---|---|---|---|---|---|
| Architecture governance | `UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN.md` | architecture docs, dependency graph, `system_dependencies` | architecture reports | architecture CI to be expanded | active | unified static/runtime graph |
| QA governance | `implementation_plan.md` | QA contract and CI workflows | `qa/checklist/core.yaml` | `qa-contract.yml`, build/security/preflight checks | active | broader E2E and coverage breadth |
| Memory and context | `implementation_plan.md` | memory service, vector/RAG, Files/Workspace integration | memory tables/RPCs and context APIs | retrieval and tenant-isolation tests | active | canonical Context Engine contract |
| Execution | `UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN.md` | Mission/Agent/Tool/MCP execution paths | Run/task/event contracts | lifecycle, retry and cancellation tests | proposed | canonical Run fabric |
| Browser | `UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN.md` | lightweight scraper and Playwright browser tools | browser endpoints and artifacts | browser smoke tests where environment permits | active | unified browser contract and worker isolation |
| Control Tower/MCP | `implementation_plan.md` | MCP gateway, capability registry and orchestration | MCP/API contracts | MCP build and integration checks | active | explicit control-plane boundary |
| Production readiness | specialized production plans | Render/GitHub/Cloudflare/Infisical/Supabase configuration | env, health, migration and release contracts | release evidence and preflight | active | staging promotion and rollback evidence |
| Cost/federation | `implementation_plan.md` | cache, queue, provider adapters and optional workers | quota/cost metadata | quota/failure/load tests | active | measured admission and cost policy |
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
