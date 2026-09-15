# SupremeAI Codebase Audit Report
> **Updated:** 2026-09-13 18:15 UTC — git HEAD: `7f938ba0fb` (3 commits ahead of original audit `71791cd7df`)
> **Frontend Tests:** ✅ 449 passed / 0 failed (90 test files) — verified this session

---

## 🔴 CRITICAL / Must-Fix

### C1 — ✅ VERIFIED CLEAN — No OpenRouter in `SupremeAIService.ts`
**File:** [`packages/shared-services/src/services/SupremeAIService.ts`](file:///f:/supremeai/packages/shared-services/src/services/SupremeAIService.ts) (340 lines)
**Status:** No `openrouter`, `anthropic.com`, `openai.com`, or raw `fetch()` calls detected. File uses only `axios` to the SupremeAI backend.

> **Action:** Update `CHECKPOINT.md` to clear the stale note. No code change needed.

---

### C2 — 🔴 STILL OPEN — `ai_memory` Supabase Table (Phase C) Not Created
**Source:** `CHECKPOINT.md` (still present in latest HEAD)
> *"Supabase `ai_memory` table setup pending (Phase C)."*

The `2026_09_13_090000` migration created `crawl_*` tables; the pgvector `ai_memory` Phase C SQL has **not yet been applied**. Blocks **Memory Must Compound** pillar (B4).

**Action required:** Run the `ai_memory` Phase C SQL against the Supabase instance.

---

### C3 — ✅ FIXED — Gmail OAuth Now Fail-Closed
**Commits:** `82de246a73` + `7f938ba0fb` (re-applied after revert)
**Verified locally this session:** `connect_gmail_oauth()` returns `False` + `WARNING` log. Not `NotImplementedError` crash.

```python
# Current state — fail-closed, honest:
def connect_gmail_oauth(self, provider: str, scopes: list) -> bool:
    logger.warning("Gmail OAuth connect requested — OAuth flow not implemented yet.")
    return False
```

---

### C4 — ✅ FIXED — 5 Stub Plugins Demoted to `experimental/` with `IDEA` Lifecycle
**Commit:** `82de246a73`
- `backend/core/plugins/official/{gmail,google_drive,notion,slack,telegram}_plugin.py` — now shims re-exporting from `experimental/`
- `backend/core/plugins/experimental/` — created with `lifecycle = "IDEA"` and honest `NotImplementedError` messages
- Capability graph is now accurate — no plugin registered as "official" that crashes on use

---

### C5 — ✅ FIXED — `useDashboardActions.ts` Now Wired to Real Backend
**File:** [`frontend/src/hooks/useDashboardActions.ts`](file:///f:/supremeai/frontend/src/hooks/useDashboardActions.ts)
Zero `setTimeout`, zero fake `resolve({ ok: true })` — now calls `workspaceCapabilitiesApi.health(id)` with real error handling.

---

## 🟠 HIGH PRIORITY — Phase 1 Open Items

### H1 — 🟠 STILL OPEN — 3 Phase 1 Items
From [`MASTER_PLAN.md`](file:///f:/supremeai/MASTER_PLAN.md):

1. **Capability health-probe promotion** — capabilities stuck in `IDEA` state never become `connected`.
2. **Execution-mode UI in Settings** — users cannot choose execution mode from the frontend.
3. **`SCRAPER_BACKEND_URL` resolver** — frontend may use wrong URL for scraper-backed operations.

---

### H2 — ✅ FIXED — `performance_metrics` Dead DB Table Dropped
**Commit:** `82de246a73`
**Migration:** [`k5l6m7n8o9p0_drop_dead_performance_metrics.py`](file:///f:/supremeai/backend/alembic_migrations/versions/k5l6m7n8o9p0_drop_dead_performance_metrics.py)
- Idempotent (`inspector.get_table_names()` check before dropping)
- `IGNORE_SAFETY_WARNING` annotation added to bypass migration safety diff script (dead table confirmed)
- Full downgrade path preserved

---

### H3 — 🟠 STILL OPEN — 103 Skipped Tests (Budget: <30 by Phase 2)
103 active skip markers across 53 test files (down from 125 baseline, −22 resolved).

**Triage plan:**
1. Deduplicate legacy `test_api_endpoints.py` — est. −20 skips
2. Quarantine `EXT` behind `@pytest.mark.ext_service` — est. −15 from gate count
3. Rewrite each `DEBT` skip or link to a tracked plan item

---

### H4 — 🟠 STILL OPEN — `chatSlice` Missing (Unified Store Migration Mid-Flight)
`unifiedStore.ts` was updated but `chatSlice` not yet created. If `UNIFIED_STORE` flag toggles on, chat state silently disappears.

**Action:** Create `chatSlice` before enabling the Phase 2 feature flag in staging.

---

### H5 — 🟠 STILL OPEN — Hybrid Fingerprint Login Not Wired to Middleware
[`frontend/src/api/apiClient.ts`](file:///f:/supremeai/frontend/src/api/apiClient.ts) line 122 — device fingerprint collected but not sent to `AntiHackingContextMiddleware`.

---

## 🟡 MEDIUM PRIORITY — Phase 2 Quality Items

### M1 — `cloud_sandbox_orchestrator.py` — Provider Endpoints Not Implemented
`backend/core/sandbox/cloud_sandbox_orchestrator.py` Lines 260, 265 — raises `NotImplementedError` for non-default providers.

### M2 — `swarm_agent_roles.py` — Unforced Abstract Method
`backend/core/swarm/swarm_agent_roles.py` Line 17 — `run()` raises `NotImplementedError` at runtime rather than being `@abstractmethod`. Subclasses that forget to override fail late, not at import time.

### M3 — `resource_registry.py` — Restart / Deploy / Rollback Stubs
`backend/core/registry/resource_registry.py` Lines 123-129: restart, deploy, rollback all `raise NotImplementedError`.

### M4 — AI Learning Engine Fallback Missing
`backend/core/ai/orchestrator.py` Line 54: should degrade to static chain instead of crashing.

### M5 — Skill Provisioning Stub
`backend/core/skills/__init__.py` Line 31: should return graceful "unavailable" response.

### M6 — Coverage Gap (Backend 30%/Gate 50%, Frontend 16%/Gate 30%)
Neither Phase 2 gate is met.

### M7 — Root-Level Lint Gap Not CI-Gated
`tools/`, `scripts/`, `packages/`, `.github/scripts/` not covered by ruff CI. ~1,500 estimated issues with no regression protection.

### M8 — Frontend ESLint 126 Warnings
57 `no-explicit-any` violations + 48 `no-unused-vars`.

### M9 — Knip Dead-Code: 72 Unused Exports, 24 Unused Dependencies
Bloats bundle and expands attack surface.

---

## 🔵 GOVERNANCE / Architecture

### G1 — Pre-Market Human-Approval Gates Pending (Deliberately Deferred)
1. **CI Hard-Blocking Enforcement** — CI passes but doesn't hard-block on failures.
2. **Branch Protection & CODEOWNERS** — not enforced via GitHub Organization settings.
3. **Live Database Backup/Restore Drill** — no production-parity restore test with evidence.
4. **Data Retention & Privacy Sign-Off** — audit log retention not approved for real customers.

### G2 — `behavioral_intelligence` Package — Dead Code (Phase 3 target)
4 missing modules — do not activate until behavioral evaluation benchmark and consent/privacy design are complete.

### G3 — 100+ Stale `target/` Remote Branches
Auto-generated bot branches (`auto-fix/*`, `devin/*`, `copilot/*`, `promotion/staging-*`) need periodic pruning.

### G4 — Dual Cline Stash (WIP Loss Risk)
2 Cline-session stashes from `1a41184224` archive. Run `git stash show stash@{0}` and `stash@{1}`.

---

## ✅ Green / Confirmed Working

| Area | Status | Evidence |
|---|---|---|
| Git working tree | Clean — zero uncommitted changes | `git status` |
| Frontend tests | ✅ 449 passed / 0 failed (90 files) | `pnpm test` — verified this session |
| `SupremeAIService.ts` | No OpenRouter/direct provider calls | ✅ Verified this session |
| EmailAgent `connect_gmail_oauth()` | Returns `False` (fail-closed) | ✅ Verified this session |
| 5 stub plugins → `experimental/IDEA` | Demoted + shims | ✅ Commit `82de246a73` |
| `useDashboardActions` | Real backend wired | ✅ This session |
| Gmail OAuth fail-closed | `return False` not crash | ✅ Commit `7f938ba0fb` |
| `performance_metrics` dead table | Dropped via migration | ✅ Commit `82de246a73` |
| MCP CI path filter (`build-mcp`) | Properly gates on `mcp/**` | ✅ Commit `99d9c752af` |
| MCP `package-lock.json` | Self-contained, committed | ✅ Commit `af3823924a` |
| Scout crawler → research pipeline | Done | Phase 1 patch ✅ |
| Reasoning stream SSE live | Done | Phase 1 patch ✅ |
| Admin `/stats`, `/users`, `/audit-logs` | Real endpoints | Phase 1 patch ✅ |
| One connection registry | Done | Phase 1 patch ✅ |
| `ConfigValidationReport` + CORS hardening | Done | Phase 1 patch ✅ |
| 20-mission suite pass^3 = 1.0 | Done | Commit `610a7939c8` |
| HITL engine + append-only audit ledger | Done | Milestone 12 |
| Supply chain SHA pinning (153 action refs) | 100% | Milestone 17 |
| 4 Render nodes (core/worker/scraper/mcp) | Live 200 OK | Cluster env spec |

---

## 📋 Updated Priority Action Queue

| # | Priority | Item | Status |
|---|---|---|---|
| 1 | 🔴 | **C2:** Run `ai_memory` Phase C SQL in Supabase | **OPEN** |
| 2 | 🟠 | **H1:** Close 3 Phase 1 open items (health-probe, execution-mode UI, SCRAPER_URL) | **OPEN** |
| 3 | 🟠 | **H3:** Triage 103→<30 skipped tests | **OPEN** |
| 4 | 🟠 | **H4:** Create `chatSlice` before UNIFIED_STORE flag in staging | **OPEN** |
| 5 | 🟠 | **H5:** Wire fingerprint login to `AntiHackingContextMiddleware` | **OPEN** |
| 6 | 🟡 | **M2:** Add `@abstractmethod` to `BaseSwarmAgent.run()` | **OPEN** |
| 7 | 🟡 | **M1:** Graceful fallback in `cloud_sandbox_orchestrator.py` | **OPEN** |
| 8 | 🟡 | **M7:** Add root-level ruff CI job for `tools/`, `scripts/`, `packages/` | **OPEN** |
| 9 | 🟡 | **M6:** Climb coverage 30→50 backend / 16→30 frontend | **OPEN** |
| 10 | 🟡 | **M8:** Fix 126 frontend ESLint warnings | **OPEN** |
| 11 | 🔵 | **G3:** Prune stale `target/` remote branches | **OPEN** |
| 12 | 🔵 | **G4:** Inspect and resolve 2 Cline stashes | **OPEN** |
| 13 | 🔵 | **G1:** Pre-market gates (CI blocking, branch protection, DB restore, privacy) | **OPEN (deliberate)** |
| — | ~~🔴~~ | ~~**C1:** Remove OpenRouter from `SupremeAIService.ts`~~ | ✅ Was already clean |
| — | ~~🔴~~ | ~~**C3:** Fix Gmail OAuth crash~~ | ✅ Fail-closed (`7f938ba0fb`) |
| — | ~~🔴~~ | ~~**C4:** 5 stub plugins crashing as "official"~~ | ✅ Demoted to `experimental/IDEA` |
| — | ~~🔴~~ | ~~**C5:** `useDashboardActions` mock execution engine~~ | ✅ Wired to real backend |
| — | ~~🟠~~ | ~~**H2:** Drop `performance_metrics` dead table~~ | ✅ Migration `k5l6m7n8o9p0` |
