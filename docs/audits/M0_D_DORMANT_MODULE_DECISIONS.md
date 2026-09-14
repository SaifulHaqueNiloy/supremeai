# M0-D: Dormant-Module Triage — Repair-or-Retire Decision Table

Roadmap item M0.4 (`docs/plans/UNIFIED_NEXT_ROADMAP_2026-09-15.md`), closing audit finding **F4 (P2)** from `docs/audits/FULL_SYSTEM_AUDIT_2026-09-14.md`.

Rule applied (roadmap doctrine): **no module is deleted just because it looks duplicate** — every decision below is backed by a caller search across the whole repo (production packages, tests, tools, workflows) and by the import-walk tool.

| # | Cluster | Symptom (import-walk) | Production callers | Test callers | Decision | Action taken | Final owner |
|---|---------|----------------------|--------------------|--------------|----------|--------------|-------------|
| 1 | `memory/unified_db_manager` | `cannot import name 'SQLiteStore' from 'memory.sqlite_store'` (real class: `SQLiteMemoryStore`) | **0** | 0 | **REPAIR** (defer final keep/merge/retire to M3 memory inventory, which requires a full store-by-store table) | import fixed + back-compat alias `SQLiteStore = SQLiteMemoryStore` | M3 |
| 2 | `p2p/resource_broker.py` | `cannot import name 'InsufficientCreditsError' from 'p2p.credit_system'` | **0** | **0** (tests/p2p_tests cover `credit_system.py` and `secure_tunnel.py` only) | **RETIRE** | file deleted (`git rm`); restorable from git history if P2P mesh work ever starts | — |
| 3 | `database/multi_db_router.py` | `WriteBehindBatcher.__init__() got an unexpected keyword argument 'max_batch_size'` (signature: `max_batch`) | 0 (dormant; `outbox_batcher` consumed by `pipelines/code_to_db_sync.flush_outbox_queue`) | 0 | **REPAIR** | kwarg `max_batch_size` → `max_batch` (1 line); also un-breaks `pipelines/code_to_db_sync`, which imports the batcher | — |
| 4 | `pipelines/code_to_db_sync.py` | same TypeError (via `database.multi_db_router.outbox_batcher`) | 0 | 0 | **REPAIR** (same root cause as #3) | no direct edit needed — fixed transitively | — |
| 5 | `core/grpc_client.py` | `ModuleNotFoundError: No module named 'protos'` | **0** | 0; **no `*.proto` sources exist anywhere in the repo** → stubs can never be generated | **RETIRE** | file deleted (`git rm`); the Worker gRPC contract (if ever needed) will be defined with real `.proto` sources under M1 Run | M1 |
| 6 | `core/plugins/experimental/*` + `core/plugins/official/*` (11 modules) | `ModuleNotFoundError: No module named 'core.plugins.experimental.base'` — `base.py` was referenced by every plugin but **never committed** (absent from the entire git history) | 0 (plugins are registry-seeded, capability-gated) | 0 | **REPAIR** — create the missing contract rather than archive 11 files | `core/plugins/experimental/base.py` created: `BasePlugin` ABC mirroring `official/base.py` exactly (duplicated on purpose: an `experimental → official` import would close a shim-induced package cycle; rationale documented in the module docstring) | plugin subsystem owner |

## Evidence

- `python scripts/audit_import_walk.py <pkg>` for `memory`, `p2p`, `database`, `pipelines`, `core`: **0 failures in all five packages** (was 16 failures total). Full-suite walk: 19 → 0 unexplained failures (the 3 remaining audit failures were `scripts/refactor/*` → M0-E, and `verification` → M0-C).
- `pytest tests/p2p_tests/` — green after the retire (tests never referenced the deleted file).
- `compileall` on `core/plugins/` + ruff clean on all touched files.
- `docs/generated/module_capability_matrix.json` regenerated (adds `experimental/base.py`, removes the two retired files).

## Guard

The drift gate (`Advanced Pre-Merge Checks`) + `scripts/audit_import_walk.py` keep this honest; M0-B's single-alembic-head guard is independent.
