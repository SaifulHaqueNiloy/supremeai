# Implementation Plan — Backend Interconnection Remediation

**Date:** 2026-08-19
**Scope:** `backend/` (1,232 `.py` files, 188,653 lines)
**Trigger:** Static audit found 22 broken internal imports (→ ~14 missing modules) and 43/100 production Agent classes orphaned (~43%). App still runs on Render because these modules are never reached by the live import graph (entrypoint reachability gap).

---

## Context / RCA
- Features were built as standalone modules but **never wired into the app entrypoint graph**.
- Some imports use **wrong prefixes** (`core.database.supabase_client` instead of `database.supabase_client`).
- Some **dependency modules were never created**.
- Result: a working core + a large dead/fragmented periphery. Not "entirely broken", but significantly unconnected.

## Reachability probe (evidence used for fix-vs-quarantine)
| Broken import target | Non-test importers | Verdict |
|---|---|---|
| `database.supabase_client` (via wrong `core.database.*`) | 42 (live: auth, evolution, internal…) | **WRONG PREFIX** → fix path |
| `tools.cloud_sandbox_orchestrator` | 12 (live: sandbox_api→api/routers.py, core/orchestration, core/queue) | **WRONG PREFIX** → fix path (real: `core/orchestration/cloud_sandbox_orchestrator.py`) |
| `tools.pr_reviewer` | 8 (live: pr_review_api→api/routers.py, scripts/seed_tools_registry) | **MISSING, LIVE** → build |
| `skills.installer` | 3 (live: core/evolution/auto_skill_creator, which is imported by api/routes/evolution.py, brain/autonomous_agent.py) | **MISSING, LIVE** → build |
| `skills.schema` | 2 (live: auto_skill_creator) | **MISSING, LIVE** → build |
| `scripts.devops.bug_prophet` | 1 (core/startup/agents ← core/lifespan.py, live) | **MISSING, LIVE** → build |
| `core.llm.language_model` | 2 (only orphan agents bias/explainability) | **DEAD-only** → quarantine agents, do NOT build |
| `core.monitoring.metrics_collector` | 2 (only orphan agents auto_scaling/cost_optimization) | **DEAD-only** → quarantine agents |
| `core.monitoring.health_checker` | 1 (only dead remediation_engine) | **DEAD-only** → quarantine |
| `core.backup.backup_manager` | 1 (only dead remediation_engine) | **DEAD-only** → quarantine |

---

## Phase 0 — Safety & baseline
- Create branch `fix/backend-interconnection`.
- Save current audit output (broken list + orphan list) to `backend/_audit_baseline.txt` for diffing later.
- Leave `docs/plan/` untouched (admin-owned).

## Phase 1 — Quick wins: wrong-prefix fixes (Tier B)
1. `core/evolution/fitness_engine.py`: `from core.database.supabase_client import …` → `from database.supabase_client import …`.
2. `api/routes/sandbox_api.py` + `tools/collaborative_editor.py`: repoint `tools.cloud_sandbox_orchestrator` → `core.orchestration.cloud_sandbox_orchestrator` (verify symbol names match).
3. Import-test each fixed file (PYTHONPATH=backend, supabase absent is OK for path resolution).

## Phase 2 — Build missing modules required by LIVE code (Tier A)
First confirm each is on the live import path (`api/routers.py`, `core/lifespan.py`, `api/routes/evolution.py`).
For each, **read the importer first** to extract the exact expected symbols, then implement a minimal-but-functional module:
1. `tools/pr_reviewer.py` — symbols expected by `api/routes/pr_review_api.py` + `scripts/seed_tools_registry.py`.
2. `skills/installer.py` — symbols expected by `core/evolution/auto_skill_creator.py`.
3. `skills/schema.py` — symbols expected by `auto_skill_creator.py`.
4. `scripts/devops/bug_prophet.py` — symbols expected by `core/startup/agents.py`.
- Verify each importer imports cleanly after build.

## Phase 3 — Quarantine dead agents + their non-existent deps (Tier C)
Move to `backend/_archive/agents/` (preserve code, remove from import graph) and drop any registration:
- `agents/governance/bias_detection_agent.py`, `explainability_agent.py`
- `agents/infrastructure/auto_scaling_agent.py`, `cost_optimization_agent.py`
- `evolution/digital_twin/remediation_engine.py`
- Their missing deps (`core.llm.language_model`, `core.monitoring.metrics_collector`, `core.monitoring.health_checker`, `core.backup.backup_manager`) become moot → **do NOT build**.
- Nothing is hard-deleted; `_archive/` keeps full history.

## Phase 4 — Orphan Agent triage (remaining ~38 production)
For each remaining orphan Agent class:
- If it is an intended feature → wire it in (register in `agents/__init__.py` / orchestrator / lifespan).
- Else → move to `backend/_archive/agents/`.
- Prioritize high-value: `SelfImprovingAgent`, `PerformanceTuningAgent`, `GovernanceAgent`, `SwarmAgent`, `SupremeAgentOrchestrator`.
- Decide per-agent; keep a tally of wired vs archived.

## Phase 5 — Verification
- Re-run audit script → **broken internal imports = 0**, orphan count = expected (archived removed).
- Import-test: all previously-broken files + `agents` package + app entrypoint (supabase installed in CI).
- Optional follow-up: add a **CI static import-graph drift gate** so broken internal imports fail the build (prevents regression).

---

## Effort estimate
- P0: 15 min · P1: 30 min · P2: 2–4 h (depends on module complexity) · P3: 30 min · P4: 1–3 h · P5: 1 h.

## Risks / notes
- Tier A builds must match the **importer's expected API** — read importers before coding.
- If a "live" importer actually lazy-imports inside `try/except`, building is lower urgency but still correct for consistency.
- Quarantine preserves all code; no hard deletion.
- Re-run the audit after each phase to keep the baseline honest.
