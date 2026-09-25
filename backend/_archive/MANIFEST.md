# backend/_archive — Archived Dead Modules

Per [MAINTAINABILITY_PLAN.md §2](../../docs/plan-network/MAINTAINABILITY_PLAN.md)
(rule 3: **archive first, delete after 1 sprint**) and issue #1340.

Original subpaths are preserved under each batch directory. Nothing imports
these modules (AST import graph + repo-wide textual reference scan + runtime
invocation scan, tool: `scripts/audit/find_dead_modules.py`, evidence:
`ci-reports/dead_modules.json`). **Do not import from here.**

## batch-1 — archived 2026-09-25 (issue #1340)

Verification date: 2026-09-25 · Scheduled delete-after review: 2026-10-09

| Original path | Lines | Note |
|---|---|---|
| backend/core/brand_compliance.py | 250 | zero refs repo-wide |
| backend/scripts/self_healing_tests.py | 125 | one-off remediation script |
| backend/core/permission_cache.py | 98 | zero refs repo-wide |
| backend/scripts/run_chaos_experiment.py | 130 | one-off script (plan §2 named) |
| backend/scripts/refactor_root_cause.py | 116 | one-off script (plan §2 named) |
| backend/scripts/self_test_and_improve.py | 97 | one-off script |
| backend/scripts/benchmark/load_test_phase3.py | 93 | phase-3 leftover |
| backend/scripts/dev/update_imports.py | 88 | one-off codemod |
| backend/seed_db_configs.py | 66 | one-off seeder |
| backend/scripts/audit_import_walk.py | 73 | one-off audit script |
| backend/scripts/refactor_logging.py | 53 | one-off codemod |
| backend/update_md.py | 51 | debug parser for stale pytest txt |
| backend/core/prompts/ai_handshake_prompt.py | 25 | zero refs repo-wide |
| backend/debug_ci_boot.py | 23 | debug leftover |
| backend/scripts/find_router_error.py | 17 | debug leftover |
| backend/get_tb_collect.py | 14 | debug leftover |
| backend/get_tb.py | 14 | debug leftover (stale `api.main` import) |
| backend/reports/optimization_engine.py | 9 | zero refs repo-wide |

Total: 18 files, ~1,339 lines.

### Plan-candidate verification results (not archived — ALIVE)

The plan's §2 table lists candidates; verification showed several are live:

| Plan candidate | Verification result | Evidence |
|---|---|---|
| backend/worker_service.py | **ALIVE — keep** | referenced by `docker-compose.yml` |
| backend/scripts/check_single_alembic_head.py | **ALIVE — keep** | invoked by `.github/workflows/ci.yml` |
| backend/scripts/auto_find_blindspots.py | alive (importers) | non-test importer in graph |
| backend/scripts/store_ci_roadmap_to_memory.py | alive (importers) | non-test importer in graph |
| backend/adapters/red_team_adapter.py | manual-ops referenced | master docs reference it |

## batch-2 — archived 2026-09-25 (issue #1345)

Verification date: 2026-09-25 · Scheduled delete-after review: 2026-10-09
All five are dead twins of LIVE canonical files (mention-site analysis, dual
import-convention graph). Auditor hardened first: dual-convention resolution +
relative-import package fix (see issue #1345).

| Original path | Lines | Note |
|---|---|---|
| backend/core/utils/firestore_helpers.py | 469 | twin of live `utils/firestore_helpers.py` |
| backend/core/models/shared_workspace.py | 386 | twin of live `models/shared_workspace.py` |
| backend/core/context_manager.py | 274 | SmartContextManager lives in `core/competitive_kit.py` |
| backend/scripts/seed_ecosystem.py | 187 | twin of live `ecosystem/seed_ecosystem.py` |
| backend/core/test_retry_handler.py | 97 | stray test outside CI matrix |

Total: 5 files, ~1,413 lines.
