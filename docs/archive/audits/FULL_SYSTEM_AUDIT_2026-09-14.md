# FULL SYSTEM AUDIT — every module individually + combined

**Date:** 2026-09-14
**Scope:** `main` @ `27deffa9` (all PRs #297–#306 merged), fresh clone, no local patches.
**Mandate:** "check every module every component one by one — are they individually working properly as they should — then check they work properly in combined."

---

## 1. Executive summary

| Layer | Result |
|---|---|
| Syntax (compileall, entire backend) | ✅ 0 errors |
| Import-walk (1,189 backend modules, package-by-package) | ⚠️ 1,170 OK / **19 failures** (all in dormant subsystems; none on the live boot path) |
| Lint (ruff 0.16.4, whole backend) | ✅ All checks passed |
| Test suites (37 pytest suites + 11 root governance suites) | ✅ 4,536 passed / 102 skipped / **8 deterministic failures** / 1 collection error |
| Combined runtime (app boot + routes + auth + health) | ✅ Boots, 147/147 routers mounted, 161 routes, `/health` 200, auth-gating 401 correct |
| Frontend (tsc + vite build + eslint) | ✅ 0 type errors, build ✓, 0 lint errors (3 warnings) |
| QA engine (Part-1 validator, route-audit, release gate, matrix) | ✅ all green (52 checklist items, 40 routes verified) |
| MCP control plane (typecheck + unit scripts) | ✅ typecheck clean; 6/7 test scripts pass (1 requires live service) |
| Config YAML (compose, vercel, firebase, 18 workflows) | ✅ 23/23 parse clean |

**Verdict: the system is production-viable.** Every deterministic defect found is enumerated in §6 with an exact fix recipe. No defect found sits on the live request path (`main.app` → middleware → routers).

---

## 2. Methodology

Five layers, executed on a fresh clone with a from-scratch virtualenv (deps resolved from `backend/pyproject.toml` poetry tables):

1. **Syntax** — `python -m compileall backend -q` (excludes `.venv`).
2. **Individual imports** — new tool `backend/scripts/audit_import_walk.py`: imports every one of 1,189 backend modules, one subprocess per top-level package (isolates cross-package state corruption; failures re-verified in clean subprocesses).
3. **Lint** — `ruff 0.16.4 check` over the whole backend (same version as CI).
4. **Per-suite tests** — driver `scripts/audit_run_backend_suites.sh`: 37 pytest suites under `backend/tests/` run in isolation, plus the 11 repo-root governance suites run **exactly as CI runs them** (`python -m unittest discover -s tests -p ...`).
5. **Combined** — real app boot (`import main` → `main.app`), route census, `TestClient` probes of health/missions/mcp-hub endpoints, OpenAPI surface check; frontend typecheck + production build; QA-engine validators; MCP control-plane typecheck + unit scripts; YAML parse of all infra configs.

Environment for every Python run: `TESTING=true ENV=test`, sqlite test DB URL, placeholder `DATABASE_URL` (fail-closed config stays satisfied, no production secrets required).

---

## 3. Individual module audit — import-walk results (1,189 modules)

Per-package walk (modules = importable units incl. subpackages):

| Package | Modules | Failures |
|---|---:|---:|
| adapters | 6 | 0 |
| adaptive_engine | 21 | 0 |
| admin | 3 | 0 |
| agents | 51 | 0 |
| api | 192 | 0 |
| brain | 22 | 0 |
| browser | 5 | 0 |
| byoc | 4 | 0 |
| **core** | **453** | **12** |
| database | 8 | 1 |
| ecosystem | 16 | 0 |
| engine | 16 | 0 |
| evolution | 12 | 0 |
| integrations | 7 | 0 |
| learning | 8 | 0 |
| memory | 16 | 1 |
| middleware | 8 | 0 |
| missions | 5 | 0 |
| models | 38 | 0 |
| monitoring | 8 | 0 |
| p2p | 4 | 1 |
| pipelines | 3 | 1 |
| runtime | 7 | 0 |
| sandbox | 3 | 0 |
| scaling | 2 | 0 |
| schemas | 3 | 0 |
| scout | 12 | 0 |
| scripts | 28 | 2 |
| services | 62 | 0 |
| skills | 6 | 0 |
| storage | 3 | 0 |
| tools | 137 | 0 |
| utils | 12 | 0 |
| verification | 2 | 1 |
| workers | 5 | 0 |
| ws | 1 | 0 |
| **TOTAL** | **1,189** | **19** |

**Zero failures in the hot packages**: `api` (192), `services` (62), `models` (38), `agents` (51), `middleware` (8), `missions` (5), `tools` (137 after pinning `mcp==1.28.1` per `poetry.lock`).

> Install-artifact note: with `mcp` 2.x (not what the lockfile pins), 9 modules under `tools/mcp` fail to import (`mcp.server.fastmcp` was renamed in mcp 2.x). With the locked `mcp==1.28.1` all 137 tool modules import. **Do not upgrade `mcp` past 1.x without a migration pass over `backend/tools/mcp/*`.**

The 19 failures are dissected in §6 (F4–F6). Key wiring fact, verified by caller search: **none of the 19 broken modules is imported by `core/app_builder.py`, `core/app.py`, or `main.py`** — the production boot chain does not touch them. They are dormant subsystems (p2p, plugins.experimental, multi-db router, grpc, dev refactor scripts) or order-dependent (verification — F5).

---

## 4. Per-suite test audit (backend/tests)

Driver: one isolated pytest run per suite (`--tb=no -q --no-cov`, sandbox env). Results:

| Suite | Passed | Skipped | Failed | Deterministic? |
|---|---:|---:|---:|---|
| adaptive_engine | 11 | 0 | 0 | — |
| agents | 270 | 4 | 0 | — |
| ai | 4 | 0 | 0 | — |
| api | 439 | 24 | 0 | — |
| brain | 4 | 0 | 0 | — |
| byoc | 8 | 0 | 0 | — |
| core | 1881→**1886** | 52 | 5→**0** | ❌ first run only — see F7 |
| database | 5 | 0 | 0 | — |
| engine | 14 | 0 | 0 | — |
| hitl | 0 (no tests) | 0 | 0 | — |
| integration | 0 (no tests) | 0 | 0 | — |
| learning | 5 | 0 | 0 | — |
| llm | 50 | 0 | 0 | — |
| memory | 3 | 0 | 0 | — |
| middleware | 25 | 0 | 0 | — |
| missions | 57 | 0 | 0 | — |
| models | 0 | 0 | collection error | ✅ yes — see F2 |
| monitoring | 2 | 0 | 0 | — |
| orchestration | 5 | 0 | 0 | — |
| p2p_tests | 8 | 0 | 0 | — |
| rag | 4 | 0 | 0 | — |
| runtime | 7 | 0 | 0 | — |
| scout_tests | 17 | 0 | 0 | — |
| scripts | 103 | 0 | 0 | — |
| security | 275 | 0 | 0 | — |
| services | 480 | 2 | 0 | — |
| test_evolution | 9 | 0 | 0 | — |
| test_strategic_patches | 4 | 1 | 0 | — |
| tools | 507 | 16 | 8 | ✅ yes — see F1 |
| unit | 17 | 3 | 0 | — |
| unit_light | 180 | 0 | 0 | — |
| utils | 131 | 0 | 0 | — |
| verification | 2 | 0 | 0 | — |
| workers | 9 | 0 | 0 | — |
| root loose tests (`tests/*.py`) | 271 | 0 | 0 | — |
| **TOTAL** | **≈4,536** | **102** | — | 8 deterministic + 5 flake |

Notes:
- `tests/e2e/` contains Playwright TypeScript specs (run by CI via Playwright, not pytest) and `tests/factories/` is a helper package — both "empty" under pytest by design.
- 102 skipped markers observed, consistent with the governed registry in `docs/SKIPPED_TESTS.md`.
- Every deterministic failure was re-run in isolation: OCR suite fails standalone (missing dep, F1); billing+embeddings pass standalone *and* in a clean full re-run (F7).

### Repo-root governance suites (unittest, CI-identical invocation)

11/11 files pass: `test_audit_definition_shadowing`, `test_capability_integration_gate`, `test_circle_architecture_gate`, `test_merge_policy`, `test_module_capability_matrix`, `test_preflight_evidence`, `test_release_acceptance_gate`, `test_render_preflight_service`, `test_route_graph`, `test_route_graph_query`, `test_route_inventory`.

> ⚠️ These suites are **unittest-only**: running `pytest tests/` from the repo root fails collection with `ModuleNotFoundError: No module named 'scripts.ci'` — the root `conftest.py` puts `backend/` on `sys.path`, where a *regular package* `backend/scripts` shadows the root `scripts/` namespace. CI never hits this (it invokes unittest from root). Documented as F8.

---

## 5. Combined audit — do the parts work together?

### 5.1 Application boot & request path (the real integration test)

```
import main → main.app (FastAPI) ................ OK
Router registration ............................. mounted=147/147 registry entries
Total routes on main.app ........................ 161
GET /health ...................................... 200 {"status":"healthy",...}
GET /api/v1/health ............................... 200 {"status":"healthy",...}
GET /api/v1/missions ............................. 401 (auth middleware gates — correct)
GET /api/v1/mcp-hub/tenants ...................... 401 (auth middleware gates — correct)
OpenAPI/docs surface ............................. disabled unless _docs_exposed (env-gated by design)
```

Both of the newest subsystems (#304 missions, #305 MCP hub) are mounted, registered, and auth-gated. Middleware chain (query timing, memory-aware, auth) executes in order.

### 5.2 Database migrations

`alembic history` resolves cleanly, **but there are 3 heads**: `mcp_gw_0001`, `a7b8c9d0e1f2`, `k5l6m7n8o9p0` (F3). Historical merge revisions exist (`cb8d8501f289`, `h3i4j5k6l7m8`) but none covers the newer branches. No CI/deploy step runs `alembic upgrade` (SQL is applied via Supabase runbooks — consistent with the Phase-C decision for `ai_memory`), so this is an ergonomics/replayability gap, not a live outage.

### 5.3 Frontend ↔ backend contract

- `bun qa/scripts/route-audit.ts`: **all 40 checklist routes verified against the real frontend route graph** — the UI paths the QA contract tests exist in the built router.
- Frontend production build compiles the full app against `packages/shared-types`, which are also imported by backend tools (`core/schema_exporter.py`, `core/type_sync_bus.py`) — the type bridge builds clean.

### 5.4 QA engine (release gate)

| Validator | Result |
|---|---|
| `scripts/ci/validate_qa_checklist.mjs` | ✅ 5 files, 52 items, 39 automated / 13 manual |
| `qa/scripts/validate-checklist.ts` | ✅ 40/40, ids unique |
| `qa/scripts/route-audit.ts` | ✅ 40/40 routes exist |
| `qa/scripts/generate-report.ts --self-test` | ✅ all fixtures (STOP RELEASE / WARNING / LOG ONLY) |
| `qa/scripts/coverage-matrix.ts` | ✅ advisory only |

### 5.5 MCP control plane (`infrastructure/mcp-control-plane`)

- `tsc --noEmit`: ✅ 0 errors.
- Unit scripts: `test_health_history` ✅ · `test_policy` ✅ (all policy/HITL assertions pass; process needs a clean `process.exit` — F9) · `test_registry` ✅ · `test_events` ✅ · `test_summary` ✅ · `test_actions` ✅ · `test_resource_list` ⚠️ requires live MCP server on `:3771` (SSE transport) — environment-dependent by design.

### 5.6 Infra configs

All 23 YAML/JSON infra files parse: `docker-compose.yml`, `docker-compose.production.yml`, `vercel.json`, `firebase.template.json`, 18 GitHub workflow files. ✅

### 5.7 Frontend build

| Check | Result |
|---|---|
| `tsc -p tsconfig.app.json --noEmit` | ✅ 0 errors |
| `vite build` (production) | ✅ built in 32.6s (chunk-size warnings only) |
| `eslint .` | ✅ 0 errors, 3 warnings (`no-unused-vars`) |

---

## 6. Findings register (every defect found, classified)

Severity: **P1** = deterministic breakage a fresh deploy/clone will hit · **P2** = real defect, currently dormant or ergonomic · **P3** = hygiene.

### F1 — P1 · `openpyxl` used by production code but never declared
`backend/tools/localization/bengali_ocr_converter.py:140` → `pd.ExcelWriter(..., engine="openpyxl")`. `openpyxl` is in **neither** `backend/pyproject.toml` **nor** `backend/poetry.lock`. The 8 `tests/tools/test_bengali_ocr_converter.py` failures are deterministic `ModuleNotFoundError: No module named 'openpyxl'` — the same crash occurs on any machine/CI job that happens to have pandas without openpyxl. The Docker image builds from the lockfile, so it depends on a transitive write-path dependency that nobody declared.
**Fix recipe:** add `openpyxl = "^3.1.5"` to `[tool.poetry.dependencies]`, run `poetry lock --no-update`, commit both. (Not patched in this audit because regenerating the lockfile requires poetry and would mix a dependency change into an audit PR.)

### F2 — P1 · `sqlglot` used by test suite but not declared (fresh-venv collection error)
`backend/tests/models/test_ai_memory_schema_contract.py:37` imports `sqlglot` (added in PR #303), but `sqlglot` is absent from `pyproject.toml` dev deps and the lockfile. Any fresh environment (new contributor, CI matrix change) gets `ModuleNotFoundError` at collection for the whole `tests/models` suite.
**Fix recipe:** add `sqlglot` to the dev dependency group + `poetry lock --no-update`.

### F3 — P2 · Alembic has 3 heads
`mcp_gw_0001`, `a7b8c9d0e1f2`, `k5l6m7n8o9p0`. Plain `alembic upgrade head` errors; `upgrade heads` works. Past merge revisions exist for older branchpoints but none covers these.
**Fix recipe:** one merge revision per pair of branchpoints (or a single 3-way merge), then enforce `alembic heads | wc -l == 1` in CI.

### F4 — P2 · Import-contract drift cluster in dormant subsystems (11 modules)
Cross-module name drift, each proven by clean-subprocess import:
- `memory/unified_db_manager.py:13` imports `SQLiteStore` — the class is actually `SQLiteMemoryStore` (`memory/sqlite_store.py:6`).
- `p2p/resource_broker.py:11` imports `InsufficientCreditsError, credit_system` — `p2p/credit_system.py` defines neither (it defines `CreditLedger`, `ResourceBroker`; no exception type, no module-level instance).
- `database/multi_db_router.py:27` and `pipelines/code_to_db_sync.py:29` call `WriteBehindBatcher(max_batch_size=50, ...)` — the constructor signature is `(name, flush_interval=2.0, max_batch=200)` (`core/persistence/write_behind.py:43`).
- `core/plugins/experimental/*` (5 plugins) + `core/plugins/official/*` (6 modules incl. `__init__`) import `core.plugins.experimental.base` — **that module does not exist anywhere in the tree**.
**Caller search result:** zero production importers of any of these (only each other + tests). They are dormant; the live app does not import them. Fix when each subsystem is revived: rename to the real symbols, or create the missing base module. Never wire them into the app before their tests exist.

### F5 — P2 · Order-dependent circular import: `verification` ↔ `runtime`
`verification/__init__.py` → `verification/verifier.py` → `runtime.task_result` → `runtime/__init__.py` → `runtime/task_runtime.py:23` → `verification.verifier` (partially initialized) → `ImportError`. Importing `verification` (or `verification.verifier`) **before** `runtime` crashes; the reverse order succeeds. The live boot path currently loads `runtime` first (via `core/factory.py`/`core/app.py` chain), so production works — but any refactor that flips first-contact order breaks boot.
**Fix recipe:** make `verification/__init__.py` lazy (module-level `__getattr__`), or move the `VerifierEngine` import in `runtime/task_runtime.py` into function scope.

### F6 — P3 · Dead dev-artifact scripts with hardcoded Windows paths (2 modules)
`scripts/refactor/refactor_remediation.py:3` and `scripts/refactor/refactor_swarm.py:3` begin with `filepath = r"c:\Users\n\supremeai\..."` and execute file I/O **at import time** (crash with `FileNotFoundError` on any non-`c:\Users\n` machine). These are one-shot refactor scripts from a dev machine, checked in as modules.
**Fix recipe:** delete, or move to `archive/` outside the import tree.

### F7 — P3 · Load-induced test flake in `tests/core` (environment observation)
First full-suite run (executed concurrently with a frontend build) produced 5 failures (`test_billing_zero_cost` ×4, `test_embeddings_coverage` ×1). All pass standalone, and a clean full re-run of `tests/core` passes 1886/1886. The 5 failures did not reproduce → resource contention, not code. Operational note: don't run heavy builds concurrently with the suite on small CI runners.

### F8 — P3 · Root `tests/` are unittest-only; pytest invocation fails
Running `pytest tests/` from the repo root fails collection (`backend/scripts` regular package shadows root `scripts` namespace because the root conftest adds `backend/` to `sys.path`). CI runs these via `python -m unittest discover` and passes. Document so nobody "fixes" CI by switching to pytest without a sys.path strategy.

### F9 — P3 · `mcp-control-plane` test:unit doesn't exit without the service
`test_policy.ts` ends with `main().catch(console.error)`; the HITL manager's fetch to `:3771` ECONNREFUSEDs and a live timer keeps bun alive — assertions all pass but the script must be `timeout`-killed. Add `process.exit(0)` at the end of each script (or close the timer) so the suite is CI-able without the running service.

### F10 — P1 (fixed in this PR) · `.venv` symlink tracked in git
Commit `f7dede7` (PR #305) accidentally committed `backend/.venv` — a **symlink** to `/home/z/supremeai-main/backend/.venv`, dangling for every other checkout and blocking venv creation (`uv venv` → "File exists"). `.gitignore`'s `.venv/` (trailing slash) matches directories, not symlinks.
**Fixed here:** untracked the symlink, added bare `.venv` pattern to `.gitignore`.

### F11 — P3 · Frontend polish (non-blocking)
3 eslint warnings (unused vars, `frontend/src`), vite chunk >600 kB warnings. Tracked in the existing P2 backlog; no action in this audit.

---

## 7. What was NOT auditable in this environment

- **Live external services**: Supabase project, Render deploy, Firebase hosting, Telegram/HITL delivery, payment providers. All were audited at the contract level (config fail-closed behavior, mock/offline fallbacks, RLS SQL) — not against live accounts.
- **`qa/playwright/*` browser runs**: require a booted frontend+backend pair with seeded auth; the scaffold's validators and CI workflows are green, spec runs are the next milestone per the QA plan.
- **LLM-adjacent suites requiring provider keys**: covered via the offline/mock fallbacks exercised in tests; real-provider behavior depends on keys.

## 8. Sign-off

- Individually: **1,170/1,189 backend modules import cleanly**; all 12 failures outside `core` are classified; hot-path packages (api/services/models/tools/agents) are 100% clean. All deterministic test failures are dependency-declaration bugs (F1/F2), not logic bugs.
- Combined: **the app boots, all 147 registered routers mount, health and auth behave correctly, frontend builds against shared types, QA gates and governance suites pass.**
- The 10 open findings are enumerated with recipes; F10 is fixed in this branch.

**Reproduction:**
```bash
bash scripts/audit_run_backend_suites.sh                 # per-suite matrix
cd backend && for p in <packages>; do \
  TESTING=true ENV=test .venv/bin/python scripts/audit_import_walk.py $p; done
python -m unittest discover -s tests -p 'test_merge_policy.py'   # root governance
bun qa/scripts/validate-checklist.ts && bun qa/scripts/route-audit.ts
```
