# Plan-to-Code Traceability Matrix

> Status: active
> Owner: Architecture Governance
> Last verified: 2026-09-15

This is the initial governance matrix. It maps canonical planning areas to runtime evidence. Detailed module-level rows should be added as each area is reconciled.

| Canonical area | Primary plan | Code/module evidence | API/data surface | Test/release evidence | Status | Known gap |
|---|---|---|---|---|---|---|
| Overall architecture | `UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN.md` | `backend/`, `frontend/`, `tools/` | FastAPI, frontend clients, shared contracts | CI and release checks | active | Full caller evidence still being collected |
| Execution priorities | `implementation_plan.md` | Backend services and operational tooling | Cross-cutting | Release gates and audit reports | active | Needs current dependency matrix |
| Control Tower/MCP | `architecture/unified_fastmcp_control_tower_multitenant_master_plan_bn.md` | `backend/tools/mcp/`, MCP services | MCP routes, capability registry | MCP integration checks | active | Gateway persistence and rollout evidence |
| Dynamic configuration | `architecture/dynamic_configuration_zero_hardcode_roadmap.md` | `backend/config/`, provider registries | Environment/config contracts | Configuration and startup checks | proposed | Runtime reload and rollback evidence |
| Production hardening | `features/production_hardening_and_p1_p2_roadmap_2026_09_11.md` | Security, migration, health, CI modules | Auth, tenant, database, deployment | CI, smoke, security checks | active | Secret rotation and skipped-test closure |
| Data and memory | `features/Plan_09_Smart_Data_Storage.md`, `features/Plan_17_Data_Lifecycle_Management.md` | Memory and storage services | Supabase/Postgres/pgvector | Schema and retention tests | active | Production schema evidence |
| Capability wiring | `features/orphan_components_wiring_master_plan.md` | `backend/`, `tools/` capability modules | Registry and tool contracts | Caller and integration tests | active | 62 partially wired/dormant modules require disposition |
| Frontend experience | `design/complete_frontend_master_plan_bn.md` | `frontend/src/` | Admin/customer UI contracts | Frontend checks and E2E | active | API-to-screen traceability incomplete |
| Intelligence/self-evolution | `features/zero_cost_autonomous_self_evolution_plan.md` | Agent, learning, verification services | Proposal/evaluation/audit events | Benchmark, regression, rollback | proposed | Governance and promotion evidence |
| Cost/federation | `FREE_TIER_FEDERATION_MASTER_PLAN_V4.md` | Provider and worker integrations | Quotas, queues, fallback | Cost and degraded-mode checks | proposed | Must remain policy-compliant and optional |

## Evidence standard

Each row becomes `complete` only when it links to concrete source files, active callers, automated tests, deployed verification, and a recovery path. A plan can remain active while individual features are complete.

## Update process

1. Update the canonical plan and this matrix together.
2. Add or revise code, API, test, and runtime evidence.
3. Record conflicts in `PLAN_RECONCILIATION_REGISTER.md`.
4. Run link and documentation checks before commit.
