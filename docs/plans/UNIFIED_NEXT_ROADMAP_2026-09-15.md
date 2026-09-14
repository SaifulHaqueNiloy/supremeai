# SupremeAI — Reconciled Next Roadmap (Ecosystem + OSS Integration + Audit Evidence)

```yaml
id: unified-next-roadmap-2026-09-15
title: Reconciled next roadmap — Unified Ecosystem Architecture + Platform OSS Integration, grounded in the 2026-09-14 full system audit
status: active
owner_circle: C1 (Code & Quality) for M0; circle assignment per milestone below
scope: execution order for the next planning horizon (M0–M9); no code changes in this PR
depends_on:
  - docs/plans/UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN.md (canonical, on main)
  - docs/plans/PLATFORM_OSS_INTEGRATION_PLAN.md (registered in this PR)
  - docs/audits/FULL_SYSTEM_AUDIT_2026-09-14.md (merged via PR #308)
  - docs/plans/implementation_plan.md (master reconciled plan)
implements:
  - UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN Phases 0–9
  - PLATFORM_OSS_INTEGRATION_PLAN Phases 0–8
supersedes: []
superseded_by: []
source_of_truth: false   # implementation_plan.md remains the master; this doc is the execution-order bridge
last_verified: 2026-09-15
code_evidence: docs/audits/FULL_SYSTEM_AUDIT_2026-09-14.md (1,189-module import walk, 37 test suites, combined boot)
test_evidence: audit reproduction commands in the audit doc §8
```

> **বাংলা সারসংক্ষেপ:** দুটো ডকুমেন্ট একই সিদ্ধান্তে পৌঁছায় — SupremeAI আর বানানো হবে না, বিদ্যমান সিস্টেমকেই ক্যানোনিক্যাল করে সংযুক্ত করা হবে। তবে একটা অগ্রাধিকার দ্বন্দ্ব আছে: এক ডক আগে Run চায়, অন্যটি আগে Context Engine। এই রোডম্যাপ সেটা মীমাংসা করেছে (M1 = Run, কারণ Context-এর scope-anchor হিসেবে `run_id` লাগবে এবং অডিটের F5 বাগ ঠিক Run-এর পথেই আছে)। তার আগে **M0**: আমাদের নিজস্ব ফুল-সিস্টেম অডিট (PR #308) যে বাগগুলো ধরেছে — undeclared deps (F1/F2), Alembic 3 heads (F3), ১১টা ডরম্যান্ট ভাঙা মডিউল (F4), circular import (F5), আর `ai_memory` Phase-C-র বাকি থাকা কাজ — সেগুলো আগে বন্ধ করতে হবে। প্রতিটা মাইলস্টোন ছোট, মাপা যায়, টেস্ট+প্রমাণ বাধ্যতামূলক।

---

## 1. Verdict on the two documents

| Aspect | UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN | PLATFORM_OSS_INTEGRATION_PLAN | Reconciliation |
|---|---|---|---|
| Core doctrine | Consolidate → canonicalize → connect → govern | Extract concepts, never copy repos | **Identical.** Adopted verbatim. |
| Second memory backend / second graph / Playwright replacement | Forbidden (§23) | Forbidden (§21) | **Identical.** Adopted. |
| Colibrì | Reject (P4) | Reject (P4) | **Identical.** Revisit only with measured need. |
| Skill packs | Optional, governed (P3) | Optional, governed (P3) | **Identical.** |
| Phase order | Run **before** Context (Ph1→Ph2) | Context **before** Run (Ph1→Ph3) | **Conflict — resolved: Run first.** Reasons below. |
| Unique content | Architecture Intelligence graph + CI blueprint + health score + failure model | Files L0/L1/L2 metadata schema + browser resource architecture + diagram output schema | Both folded into M2/M4/M5/M8. |

**Why Run before Context (M1 before M2):**
1. `PLAN_TO_CODE_TRACEABILITY_MATRIX.md` already marks *Execution → canonical Run fabric* as **proposed** and *Memory and context* as **active with a canonical-Context-Engine gap** — Run is the larger architectural hole.
2. The Context Engine's scope chain is `…PROJECT → CHAT → RUN → STEP` (both docs agree). `run_id` cannot anchor scope until a canonical Run exists. Building Context first would force a rework pass.
3. The audit (F5) proved `verification ↔ runtime` has an **order-dependent circular import** — exactly the module cluster Run wiring will touch. Fixing it is M0.3, and it de-risks M1 directly.
4. Missions core (merged PR #304) is a working seed: `Mission` model + state machine + service + API already exist; Run fabric extends it instead of starting greenfield.

---

## 2. Ground truth this roadmap is anchored to (evidence, not documentation)

| Claim in the plans | Verified reality on main @ 506d506 |
|---|---|
| "system_dependencies is the active runtime graph" | ✅ Real — `backend/models/sentinel.py` (sentinel/morphic schema, migration `cfe7c95dbee2`). Foundation for M5 confirmed. |
| "Run contract exists" | ❌ **No canonical Run model.** Only `automation_execution`, `execution_log`, `execution_policy`, `pending_tasks` tables. M1 is genuine new work (extension, not replacement — Rule 1). |
| "Memory is substantially implemented" | ⚠️ True but **fragmented**: 15 store modules under `backend/memory/` (chromadb, sqlite, supabase, cloud_postgres, hierarchical_tree, episodic, sliding_window, summary_tree, …) + `backend/core/ai_memory/vector_store.py` + `services/memory_service.py`. M3's consolidation is justified — this is the duplicate-subsystem surface the doctrine targets. |
| "ai_memory canonical = vector(384), Phase C SQL ready" | ✅ Audit doc `docs/database/AI_MEMORY_SCHEMA_AUDIT.md` + idempotent `backend/database/supabase/ai_memory_phase_c.sql` merged (PR #303). **Execution on Supabase + sign-off is still pending** → M0.6. |
| "Architecture tooling exists in CI" | ❌ No dependency-cruiser, no pydeps, no architecture-pr workflow anywhere. M5 is greenfield but small (config + 4 scripts + 2 workflows). |
| "QA contract is machine-readable and green" | ✅ Validators green (52 items, 40 routes, release gate self-test). ⚠️ But 15 `test.fixme` across customer/admin/security specs + auth setup skeletons are TODO → M0.7. |
| Audit findings F1–F11 | F10 fixed (merged in #308). **F1, F2, F3, F4, F5, F6, F8, F9 open** → M0. F7/F11 tracked, non-blocking. |

---

## 3. Milestone plan

Dependency graph:

```text
M0 (audit debt + baseline hygiene)
 └→ M1 Canonical Run ──→ M2 Context Engine ──→ M3 Memory consolidation
                              └→ M7 Artifact fabric
 M1 ─→ M4 Browser layer          M5 Architecture Intelligence (parallel, from M0)
 M1 ─→ M6 MCP lazy discovery     M8 Diagram UX (after M5)
                                 M9 Skill ecosystem (after M6+M7)
```

### M0 — Audit-debt burn-down + baseline hygiene (এখনই, ~১ সপ্তাহ)

**Goal:** current code যাচাই শেষ — এখন যাচাইকৃত বাগগুলো বন্ধ করা, যাতে M1+ একটা পরিষ্কার baseline-এ দাঁড়ায়। প্রতিটা আইটেম ছোট PR, আলাদা ভেরিফায়েবল।

| # | Item | Audit ref | Fix | Exit evidence |
|---|---|---|---|---|
| M0.1 | Declare `openpyxl` (runtime) + `sqlglot` (dev) in `backend/pyproject.toml`, `poetry lock --no-update` | F1 (P1), F2 (P1) | pyproject + lockfile | OCR suite 8/8 green in fresh venv; `tests/models` collection OK |
| M0.2 | Alembic single head: one merge revision for `mcp_gw_0001` / `a7b8c9d0e1f2` / `k5l6m7n8o9p0` + CI guard (`alembic heads` count == 1) | F3 (P2) | 1 revision + workflow step | `alembic upgrade heads` replay on scratch PG |
| M0.3 | Break `verification ↔ runtime` circular import: lazy `__getattr__` in `verification/__init__.py` (or function-scope import in `runtime/task_runtime.py`) | F5 (P2) | ≤10 lines | `import verification` succeeds **before** `import runtime` in clean subprocess; both orders green |
| M0.4 | Dormant-module triage (repair-or-retire table): `memory/unified_db_manager` (SQLiteStore→SQLiteMemoryStore), `p2p/resource_broker` (define `InsufficientCreditsError`/`credit_system` or retire p2p), `database/multi_db_router` + `pipelines/code_to_db_sync` (`max_batch_size`→`max_batch`), `core/plugins/experimental.base` (create base or archive plugins), `core/grpc_client` (generate protos or archive) | F4 (P2) | one PR per cluster, decision recorded | import-walk failures 19 → ≤2 documented; `scripts/audit_import_walk.py` rerun attached |
| M0.5 | Delete/archive `scripts/refactor/refactor_remediation.py` + `refactor_swarm.py` (hardcoded `c:\Users\n` paths); add `process.exit(0)` hygiene to mcp-control-plane test scripts | F6, F9 (P3) | file moves + 2-line patches | import-walk `scripts` package clean; `bun run test:unit` exits ≤90s without service |
| M0.6 | **ai_memory Phase C execution + sign-off (CHECKPOINT pending):** run `ai_memory_phase_c.sql` on Supabase, capture verification SQL output, then code follow-ups: `memory_service.py:702` 1536-dim hash fallback → 384; `vector_store.py` writer gaps (session_id/content discarded) so AutoRAG persists; wire `fn_ai_memory_retention_cleanup` into Orchestrator periodic task | PR #303 §10 | SQL runbook + 3 code patches | Supabase `\d ai_memory` evidence + HNSW index present; AutoRAG store→recall round-trip test green |
| M0.7 | QA spec completion: write `qa/playwright/*/.auth/setup.ts` skeletons, convert 15 `test.fixme` → real specs (5 customer / 5 admin / 5 security) | audit §5.4 | Playwright work | `qa/scripts/generate-report.ts` shows ≥36 automated with E2E evidence in CI artifact |

**Forbidden in M0:** no refactors beyond the listed items, no new subsystems, no dependency upgrades beyond the two declarations.

**Exit criteria for M0:** import-walk = 0 unexplained failures; Alembic 1 head; both dep declarations locked; ai_memory SQL executed with evidence; all 5 QA spec groups runnable; full suite ≥ current 4,536 passing with the 8 deterministic failures gone.

### M0 EXECUTION STATUS — ✅ COMPLETE (2026-09-14)

Executed as seven small sequential evidence-driven PRs per the approved execution order (user verdict on #309: split M0 into M0-A…M0-G; M5 may start in parallel with M1–M4 after M0):

| Item | PR (merged) | Evidence artifact |
|---|---|---|
| M0-A deps+lock (F1/F2) | #312 | OCR 38/38 + tests/models 40/40 in CI-identical env; zero lock drift |
| M0-B Alembic single head (F3) | #313 | merge rev `6250e2a31d38`, offline replay 63 DDL stmts, AST guard + CI step |
| M0-C circular import (F5) | #314 | both import orders green; 7/7 targeted tests |
| M0-D dormant triage (F4) | #315 | `docs/audits/M0_D_DORMANT_MODULE_DECISIONS.md`; walk failures 19→0 |
| M0-E script hygiene (F6/F9) | #316 | dead scripts out; 6 MCP test scripts exit deterministically (5×0, 1 fail-fast) |
| M0-F ai_memory checkpoint | #317 | `docs/database/AI_MEMORY_PHASE_C_EXECUTION_EVIDENCE.md`; live Supabase execution, 588 rows preserved, round-trip proven |
| M0-G QA spec completion | #319 | `docs/audits/M0_G_QA_SPEC_COMPLETION.md`; ground truth 13 fixme → 7 converted/6 honest; setups now collected (38 tests listed) |

**Exit-criteria verification on final main (8e5e0a0):** import-walk 0 failures across all six previously-failing packages (511 modules: memory/p2p/database/pipelines/core/scripts); `alembic heads` = 1 + guard OK; 151/151 tests green across all previously-failing suites; every PR merged with CI fully green (24/25 checks incl. Backend Tests matrix).

**Sequencing note:** with M0 closed, per the approved plan M5 (Architecture Intelligence) may start **in parallel** with M1 Canonical Run → M2 Context Engine → M3 Memory → M4 Browser. M1+M2+M3 must be implemented as one unified execution/context architecture, not three separate features.

---


### M1 — Canonical Run fabric (P0; ecosystem Ph1) — owner C5

**Goal:** এক execution contract — Mission/Agent/Tool/MCP/Browser/Code সব Run হিসেবে observe হবে, feature rewrite ছাড়া।

- Extend (not replace): `Run` model anchored to existing `Mission` (missions/models.py) + `automation_execution`/`execution_log` become Run evidence streams; `pending_tasks` maps to REQUESTED.
- Implement lifecycle `REQUESTED → POLICY_CHECKED → PLANNED → RUNNING (WAITING_APPROVAL/RETRYING/DEGRADED/BLOCKED) → terminal → FINALIZED` reusing the missions state-machine pattern (already tested — 24 tests).
- Retry classification enum (transient / rate_limited / dependency_unavailable / policy_blocked / invalid_input / deterministic / resource_exhausted / approval_required).
- Budgets: wall-clock, token, tool-call, retry (colibrì-free, no new infra — DB columns + enforcement helper).
- HITL hook: reuse existing HITL manager contract.
- Async boundary: long ops return `run_id` ack (contract only; queue choice later).
- ~20 tests: lifecycle transitions, budget enforcement, retry classification, cancellation, audit events.

**Exit criteria:** missions + one tool path + one MCP path observable as Runs in a test DB; lifecycle/retry/budget tests green; traceability matrix Execution row → active.

---

### M2 — Context Engine (P0; ecosystem Ph2 + OSS Ph1/§4) — owner C3

**Goal:** smallest-sufficient-context assembly over **existing** Files/Memory/RAG — L0/L1/L2 + budgeter + scopes + provenance. **No new context database.**

- Files metadata upgrade per OSS plan §4 (`summary_l0`, `summary_l1`, `content_ref`, `parent_id`, `hash`, `version`) — Alembic revision (canonical path per hardening decision).
- Context budgeter (yaml budget shape from OSS plan §3.4); scope chain `GLOBAL→USER→WORKSPACE→PROJECT→CHAT→RUN→STEP` using M1's `run_id`.
- Provenance + tenant filter enforced on every item (§19 invariants).
- Measurement harness: tokens-per-task before/after (success metric §22).

**Exit criteria:** one context assembly path used by chat + one agent flow; token reduction measured and recorded; tenant-leak tests green.

---

### M3 — Memory consolidation (P1; ecosystem Ph3 + OSS Ph2/§5) — owner C3

**Goal:** ১৫+ স্টোর মডিউল থেকে **এক authoritative memory path** — lifecycle + scopes + confidence + provenance + hybrid ranking.

- First deliverable is a **decision table**, not code: every module in `backend/memory/` gets keep/merge/archive verdict with caller evidence (reuse `scripts/audit_module_wiring.py` + the audit's import-walk data).
- Implement lifecycle (Candidate→Validated→Stored→Reinforced→Updated/Superseded→Archived), confidence/source/last_confirmed_at/expires_at on the canonical store (ai_memory superset).
- Hybrid ranking: semantic + lexical + recency + confidence + scope_match.
- Memory writes attach to completed Runs (M1 dependency).

**Exit criteria:** decision table merged; canonical path handles chat recall in prod-shaped test; duplicate stores archived with zero-caller proof.

---

### M4 — Browser execution layer (P1; ecosystem Ph4 + OSS §6/7) — owner C6

- `browser.open/click/type/select/extract/screenshot/download/wait` contract wrapping existing Playwright; lightweight HTTP routing first (existing scraper); sessions belong to Runs; action budgets + timeouts + cleanup mandatory; SSRF/target policy (extend existing `test_integration_discovery_ssrf`).
- **Do not** replace Playwright with Browser Use; **do not** load Chromium into the API process path.

**Exit criteria:** both routing paths observable as Runs; RAM/CPU per browser Run measured (OSS §22 metric); degradation test (browser down ≠ cascade).

---

### M5 — Architecture Intelligence (P1; ecosystem Ph5 + OSS §11–13; parallel with M1–M4 after M0) — owner C1

- Greenfield verified: add dependency-cruiser (frontend), pydeps (backend), repo-structure graph, merge with `system_dependencies` runtime state (sentinel schema).
- `architecture-rules.yml` + cycle/boundary/changed-edge/blast-radius scripts; **baseline-N policy** (`N → pass, N+1 → fail`) so legacy debt never blocks progress.
- Workflows: `architecture-pr.yml` (PR diff comment), `architecture-nightly.yml` (full rebuild + drift + orphan + vuln).
- Architecture health score as indicator (not a release gate).

**Exit criteria:** a sample PR shows an architecture diff comment; baseline violation count recorded in docs; nightly green.

---

### M6 — MCP control-tower refinement (P1; ecosystem Ph6 + deferred MCP Phases B/D/E) — owner C2/C5

- Lazy discovery (small stable gateway surface → discovery → circle → tool → Run), capability metadata standard, policy-before-execution (mcp hub from PR #305 already has policy + one-time tokens — extend, don't duplicate).
- **Never** circumvent quotas or multiply free-tier accounts (standing constraint).

**Exit criteria:** model-facing tool surface stays ≤ small-N while capability count grows; policy tests green.

---

### M7 — Artifact/reference fabric (P1; ecosystem Ph7)

- `ref://run/{run_id}/artifact/{artifact_id}` semantics, checksum/retention/access metadata, browser/code/analysis outputs connected; control-plane payload-size measurement before/after.

### M8 — Diagram & architecture UX (P2; ecosystem Ph8 + OSS §10)

- Structured diagram JSON schema → **server-safe renderer** (frontend owns HTML/SVG; model output never enters DOM raw); dependency explorer + blast-radius view on top of M5 graph.

### M9 — Governed skill ecosystem (P3; ecosystem Ph9 + OSS §15/16)

- Skill registry + manifests + permission scopes + sandbox/resource policy + provenance + versioning; cybersecurity/scientific packs as opt-in installs. Security skills require explicit target allowlist + rate limit + audit trail.

---

## 4. Success metrics (merged from both docs — measured, not aspirational)

- **Execution:** % major tasks as canonical Runs; retry/failure rate by class; budget-violation count = 0 in prod.
- **Context:** avg tokens per workspace task ↓; retrieval relevance ↑; context-failure rate ↓.
- **Memory:** duplicate stores archived = 100%; cross-session recall precision ↑; retention job runs (180d default).
- **Browser:** unnecessary Chromium launches ↓; per-Run RAM/CPU recorded.
- **Architecture:** 0 new cycles/violations per PR (baseline-N); static/runtime mismatch count trending ↓.
- **Quality:** QA contract pass rate; the 8 audit-deterministic failures stay at 0; E2E fixme count 15 → 0.

## 5. What must NOT happen (standing constraints + both docs' prohibitions, merged)

1. রিপো নতুন করে বানানো নয়; duplicate subsystem নয় (দ্বিতীয় memory backend / dependency graph / QA gate / browser stack / run system)।
2. Playwright wholesale replacement নয়; API process-এ Chromium নয়।
3. Free-tier federation quota tricks / account multiplication — **নিষিদ্ধ** (standing)।
4. Metrics ছাড়া K8s/infra expansion — **নিষিদ্ধ** (standing)।
5. Model-generated raw HTML/SVG DOM-এ — নয়; structured schema + safe renderer only.
6. Heavy payload control plane-এর ভেতর দিয়ে — নয়; `ref://` only.
7. শত শত raw tool প্রতিটা মডেলের সামনে খুলে দেওয়া — নয়; lazy discovery.
8. Colibrì / নতুন OSS dependency — measured need ছাড়া নয়।
9. Architecture debt দিয়ে সব progress বন্ধ করা — নয়; baseline-N policy (নতুন debt ব্লক, পুরোনোটা incremental retire)।
10. Documentation-only completion claim — নয়; traceability matrix-এর evidence rule বলবৎ।

## 6. Execution protocol (per milestone)

1. Branch `feat/<milestone>` off fresh main; read `worklog`/traceability matrix first.
2. Implement smallest slice; tests first where contracts are new.
3. Green gates: ruff 0.16.4, affected suites, merge-tree dry-run, QA validators.
4. Evidence in PR body (audit reproduction commands where applicable).
5. Update `PLAN_TO_CODE_TRACEABILITY_MATRIX.md` row + this doc's milestone checkbox on merge.
6. Runtime verification on staging where the milestone touches boot/deploys.

---

*Maintainer note: this document is the execution-order bridge between the two architecture plans and the 2026-09-14 full-system audit. If a milestone's premise changes, update this doc and the traceability matrix in the same PR (plan governance rule).*
