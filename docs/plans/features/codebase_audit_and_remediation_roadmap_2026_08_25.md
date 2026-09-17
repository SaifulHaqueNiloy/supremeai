---
target_scope: supremeai_internal
# [V5 audit 2026-09-17] Legacy doc migrated to canonical governance schema; defaults are conservative (historical/derived role) — refine on next lifecycle review.
id: auto:codebase_audit_and_remediation_roadmap_2026_08_25
subject: SupremeAI — Codebase Audit & Roadmap (2026-08-25)
document_role: audit
planning_authority: Architecture Governance / Planning Circle
status: historical

---

# SupremeAI — Codebase Audit & Roadmap (2026-08-25)

Source: fresh zip snapshot (`supremeai-main`), 1534 Python files + 461 TS/TSX files, no `.git` history included.

## 1. Progress since last audit (2026-08-21/22) — verified, not assumed
- Coverage gate raised **38% → 45%** (`MIN_BACKEND_COVERAGE` in `ci.yml`) — moving in the right direction.
- Hardcoded Render service IDs (`srv-...`) — **0 occurrences left** in workflows. Fully fixed.
- No live hardcoded secrets found in this scan (only a self-referential constant name `HARDCODED_SECRET = "hardcoded_secret"` inside `vulnerability_prophet.py`, which is a detector rule string, not an actual leaked credential — worth a quick manual glance but not urgent).
- Two new tools appeared that materially help the "self-healing" mission: `backend/pyerrorfix/` (a CLI: detectors/fixers/rules for auto-fixing Python errors) and `tools/gap_finder/` (scanner for capability gaps). These look like real steps toward autonomy — worth auditing whether they're actually wired into CI/self-healing loops or still standalone CLIs nobody calls.

## 2. New duplication found — `backend/brain/` router count grew again
Now **9** separate router files (was 8 last audit): `api_router.py`, `cognitive_router.py` (new), `expert_router.py`, `gcp_router.py`, `model_router.py`, `nine_router.py`, `parallel_cloud_router.py`, `performance_aware_router.py`, `smart_router.py`.

Per your own stated consolidation principle (never delete blind — extract each file's unique algorithm, merge into one canonical module, keep old files as backward-compatible facades), the plan stays:
- Merge `expert_router.py` (Bengali/Banglish domain-keyword MoE routing), `smart_router.py` (TaskComplexityAnalyzer + escalation flow), `performance_aware_router.py` (weighted scoring), `nine_router.py` (cost estimator), and now `cognitive_router.py` (needs inspection — likely a reasoning-depth/complexity classifier, overlaps with `smart_router`) into one `backend/core/llm/advanced_model_router.py`.
- `model_router.py` (existing external callers) becomes a thin facade delegating to the unified router.
- `parallel_cloud_router.py` is infra load-balancing, not LLM routing — relocate to `core/infrastructure/`.
- `api_router.py` / `gcp_router.py` become thin facades.
- **Action needed before merging further**: read `cognitive_router.py` fresh, since it's new since last audit — confirm it isn't just `smart_router.py` copy-pasted under a new name (that pattern has happened before in this repo).

## 3. Module-name collisions (same risk class that already caused real production bugs — `secret_vault`, `honeypot_middleware`)
- `config.py` × 4: `backend/core/config.py` (canonical), `backend/api/routes/config.py`, `backend/pyerrorfix/config.py`, `tools/gap_finder/config.py`. The last two are self-contained CLI tool configs (lower risk — different import root), but `api/routes/config.py` vs `core/config.py` is the dangerous pair — same class of bug that caused the CORS/secret_vault double-cache issue previously. Rename `api/routes/config.py` → `api/routes/app_config_routes.py` (or similar) — near-zero-risk, mechanical rename.
- `llm_gateway.py` × 2: `backend/api/routes/llm_gateway.py` vs `backend/core/llm/llm_gateway.py` — same fix, rename the routes one.
- `evolution` named in 5 places now (grew from 4): `backend/evolution/`, `backend/agents/evolution/`, `backend/core/evolution/`, `scripts/evolution/`, plus `backend/tests/evolution/` (test dir, expected to mirror the source tree, not itself a collision).

## 4. Dead / low-usage code candidates (needs re-verification with real grep on canonical import paths, since simple substring grep over-counts)
Historically verified dead (evolution/p2p/scout/skills at 0 outside imports) in the 2026-08-19 audit; this snapshot's grep shows nonzero hits, but those numbers are unreliable with a plain substring search (matches doc mentions, string literals, comments). Recommend re-running the same verified method as before: `grep -rn "^from backend\.<dir>\|^from <dir>\." --include="*.py"` restricted to actual import statements, excluding the directory's own files and `_archive/`, `docs/`, `.md`. Do this once before deleting/relocating anything — don't act on the loose numbers in this pass.

## 5. Agent-system fragmentation — now effectively 7+ locations
- `backend/agents/` — 50 files (legacy, mostly uninstantiated per last verified audit)
- `backend/tools/ai_agents/` — 5 files (the documented "real" live system per `api/routes/agents.py`'s own comment)
- `backend/brain/` — 6 agent-related files (`crewai_agents.py`, `autonomous_agent.py`, `langgraph_agent.py`, `agent_departments.py`, etc.)
- Plus `models/dynamic_agent.py` used by `core/agent_factory.py`

This is the single biggest structural risk to your "self-evolving intelligence, no can't" goal: new agent capability keeps landing in a *new* location instead of extending the one real system, so nothing compounds. This should be the top priority of the next active work session, ahead of any new features.

## 6. Documentation sprawl
11 top-level tracking `.md` files (down from 17 at peak, so consolidation is happening) — `STATUS.md`, `TODO.md`, `CHECKPOINT.md`, `LESSONS_LEARNED.md`, `FEATURE_TRACKING_LOG.md`, `REAL_TESTING_LOG.md`, `implementation_plan.md`, `render_deployment_failure_logs.md`, `SECRETS.md`, `CONTRIBUTING.md`, `README.md`. Still worth merging `STATUS.md` + `CHECKPOINT.md` + `TODO.md` into one living doc; `SECRETS.md` should be checked that it documents *names* of secrets only, never values.

## 7. Roadmap (sequenced, same phase logic as before — structural work before security work, so security audit doesn't get redone after files move)

**Phase 0 — Verify (1-2 days, near-zero risk)**
1. Re-run the strict import-based dead-code check on `evolution/p2p/scout/skills/byoc/engine/adaptive_engine` (loose grep in this session isn't trustworthy — confirm before touching anything).
2. Read `cognitive_router.py` fresh — confirm what's actually new vs duplicate of `smart_router.py`.
3. Confirm whether `pyerrorfix` and `gap_finder` are wired into any CI job / autonomous loop, or are unused standalone CLIs.

**Phase 1 — Agent-system consolidation (highest leverage, ~1-2 weeks)**
Merge `backend/agents/`, `backend/tools/ai_agents/`, and `backend/brain/`'s agent files into one canonical agent framework, following your extract-then-facade principle — same treatment as the router merge. This directly unblocks the "no can't, grows smarter every task" goal, since capability currently scatters instead of compounding.

**Phase 2 — Brain router consolidation (~3-5 days)**
Merge the now-9 router files into `advanced_model_router.py` per section 2 above, with `model_router.py` kept as a facade for the 60+ existing callers.

**Phase 3 — Structural rename pass (~1 day, mechanical, very low risk)**
Rename the 3 remaining module-name-collision pairs (`api/routes/config.py`, `api/routes/llm_gateway.py`, and pick one canonical `evolution` while archiving/merging the rest).

**Phase 4 — Coverage ratchet + auth audit (ongoing)**
Coverage is climbing (38→45%) — keep raising in small increments (next target ~55%) after Phase 1-2 land, since consolidated code is easier to cover than scattered duplicates. Re-run the auth-dependency audit (last known: only ~22 of 85 route files had a recognizable `Depends`-based guard) once files stop moving.

**Phase 5 — Docs consolidation (parallel, low priority)**
Merge `STATUS.md` + `CHECKPOINT.md` + `TODO.md`; archive anything superseded into `docs/archived_reports/` as already done for `FAILING_TESTS.md`.

## Notes
- No `.git` folder in this zip, so I couldn't diff against the last known commit or check exact recent commit history — this audit is a structural snapshot, not a commit-by-commit diff. If you want a precise diff against `d38865c5`/`96505f3a`/`8035653` (last known commits from prior sessions), share a fresh `git clone` or the current `HEAD` SHA.
- I did not push anything — this session has no GitHub write credentials. Deliverable is this file only.