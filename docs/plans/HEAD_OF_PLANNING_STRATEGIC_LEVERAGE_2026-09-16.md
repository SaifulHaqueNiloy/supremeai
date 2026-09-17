---
id: head-of-planning-strategic-leverage-2026-09-16
title: "Head of Planning — Strategic Leverage Memo v1 (Constitution-Anchored Path to 'One of the Best AI Models')"
status: active
document_role: roadmap
owner_circle: C1 (Code & Quality) and cross-circle (C2/C3/C5/C6) per lever
scope: planning-department strategic memo; identifies highest-leverage next moves toward battlefield wins B1–B6 without violating the Constitution; no code changes in this document
depends_on:
  - README.md (SupremeAI Constitution §1–14)
  - docs/architecture/SUPREMEAI_CORE_CONSTITUTION.md (10 universal principles)
  - docs/plans/UNIFIED_NEXT_ROADMAP_2026-09-15.md (M0–M9 active roadmap)
  - docs/plans/vision_strategic_positioning.md (Phase 0–6 master plan + battlefields B1–B6)
  - docs/audits/SYSTEM_DEFECT_REGISTER_2026-09-15.md (6 defect classes A–G)
  - AGENTS.md (Mandatory Rules #1–#9, esp. living-asset protection #6)
  - .github/constitution/rules.yml (machine-enforced constitutional rules)
implements:
  - Reinforces, never supersedes: UNIFIED_NEXT_ROADMAP_2026-09-15.md (M2–M9)
  - Reinforces: vision_strategic_positioning.md (Phase 2 Reliability Moat, Phase 3 Own Model v1)
  - Operationalizes: README Constitution principles #1, #3, #5, #9, #10, #11, #13, #14
supersedes: []
superseded_by: []
last_verified: 2026-09-16
code_evidence: docs/audits/SYSTEM_DEFECT_REGISTER_2026-09-15.md (1,189-module walk; 707 backend routes; 236 frontend endpoints; 37 test suites)
test_evidence: STATUS.md (2026-09-16, frontend 486/486 PASS; mission suite 5 missions / 12 tests green; pass^3 harness live in CI)
plan_lifecycle: living — v1 issued 2026-09-16; future Head of Planning memos appended as dated siblings under docs/plans/HEAD_OF_PLANNING_*.md
target_scope: supremeai_internal
---

# Head of Planning — Strategic Leverage Memo v1

> **বাংলা সারসংক্ষেপ:** এই মেমো SupremeAI-কে "বিশ্বের অন্যতম সেরা AI মডেল"-এ পরিণত করার পথে সর্বোচ্চ-লিভারেজ পদক্ষেপগুলো চিহ্নিত করে — কিন্তু প্রতিটি পদক্ষেপ আমাদের ১৪-দফা Constitution-এর সাথে সঙ্গতিপূর্ণ। নতুন subsystem বানানো নয়; বরং M1 (Canonical Run) পুরো হওয়ার পর M2–M9 মাইলস্টোনগুলোকে সঠিক অগ্রাধিকারে এগিয়ে নেওয়া, Class C/G defect গুলো বন্ধ করা, এবং Memory Flywheel-কে Phase 3 (Own Model v1)-এর জন্য প্রস্তুত করাই এই মেমোর মূল লক্ষ্য।

---

## 0. Memo Purpose and Constitution Anchor

This memo is the first in a recurring **Head of Planning** series. It exists because the project has reached a specific inflection point: the audit-debt baseline (M0) is closed and the canonical Run fabric (M1) is code-complete, which means the next dollar of engineering effort must now be directed at *battlefield leverage* rather than *baseline repair*. The Head of Planning's mandate is to keep analyzing how SupremeAI becomes one of the best AI models in the world — without ever weakening the Constitution that makes SupremeAI worth building in the first place.

The Constitution is not a constraint we work around; it is the moat itself. The vision document (`docs/plans/vision_strategic_positioning.md` §0) already proves this: a frontier model shipped as a bare API loses to a governed system on every field where the *system* is the product. Our path to "one of the best" therefore runs through the six battlefields (B1 Reliability, B2 Task Completion, B3 Cost, B4 Memory, B5 Bengali Depth, B6 Integration Surface) — not through parameter count. Every lever in §4 below is justified by which battlefield it advances and which Constitution principle it serves. No lever is included that would require violating principle #3 (Reuse Before Creation), #4 (Dynamic Discovery), #5 (Verification Before Trust), #13 (No Silent Failure), or #14 (Sustainable Cost).

This document is governed by AGENTS.md Mandatory Second Rule #6 (Architectural Plans as Protected Living Assets). It is a *living memo*: future Head of Planning iterations will be appended as dated siblings under `docs/plans/HEAD_OF_PLANNING_*.md`, never overwriting this v1, so that the planning department's reasoning lineage remains auditable.

---

## 1. Current State Snapshot (verified 2026-09-16)

SupremeAI's current position is summarized below using runtime evidence only — no documentation-only claims, per AGENTS.md Mandatory Rule #2 (Operational Reality Over Superficial Artifacts). Every cell in this table traces to a file or command in the repository; future Head of Planning memos must follow the same evidence discipline.

| Domain | State | Evidence | Constitution principle served |
|---|---|---|---|
| M0 — Audit debt burn-down | ✅ COMPLETE (2026-09-14) | `docs/plans/UNIFIED_NEXT_ROADMAP_2026-09-15.md` §M0 EXECUTION STATUS; PRs #312–#319; import-walk 0 failures across 511 modules; Alembic single head; ai_memory Phase C live on Supabase with 588 rows preserved | #13 No Silent Failure, #5 Verify Before Trust |
| M1 — Canonical Run fabric | ✅ CODE COMPLETE (2026-09-15) | PRs #341/#342/#344; `backend/runs/` package; 116/116 tests green; 9 `/api/v1/runs` endpoints mounted; traceability matrix Execution row → active | #3 Reuse Before Creation (extended, not replaced Mission), #6 Policy Before Power |
| M2 — Context Engine | ⏳ Not started; P0 next milestone | `UNIFIED_NEXT_ROADMAP_2026-09-15.md` §M2; F3 architectural debt | #14 Sustainable Cost (token reduction), #11 Memory Must Compound |
| M3 — Memory consolidation | ⏳ Not started; P1; depends M1 ✅ | 15+ store modules under `backend/memory/` (chromadb, sqlite, supabase, hierarchical_tree, episodic, sliding_window, summary_tree, …) all still active | #3 Reuse Before Creation (kill duplicates), #11 Memory Must Compound |
| M4 — Browser execution layer | ⏳ Not started; P1; depends M1 ✅ | Existing Playwright surface; M4 wraps, never replaces | #8 Graceful Degradation, #2 Capability Sovereignty |
| M5 — Architecture Intelligence | ⏳ Not started; P1; parallel with M1–M4 | No dependency-cruiser / pydeps / architecture-pr workflow exists yet — verified greenfield but small | #10 Make Important Behavior Observable |
| M6 — MCP control-tower refinement | ⏳ Not started; P1 | MCP hub from PR #305 has policy + one-time tokens (extend, never duplicate) | #2 Capability Sovereignty, #12 Least Privilege |
| M7 — Artifact / reference fabric | ⏳ Not started; P1 | `ref://run/{run_id}/artifact/{artifact_id}` not yet implemented | #5 Verify Before Trust |
| M8 — Diagram & architecture UX | ⏳ Not started; P2 | No structured diagram JSON schema; safe-renderer rule (no raw model HTML/SVG to DOM) yet to be enforced | Constitution Core #2 (Build Complete Circles) |
| M9 — Governed skill ecosystem | ⏳ Not started; P3 | Skill registry + permission scopes not yet implemented | #12 Least Privilege, Maximum Capability |
| Phase 0 — Stop the Bleed | ✅ Mostly shipped | Scout hardened, reasoning stream live, RLHF governance fixed, pass^k harness live | #13 No Silent Failure |
| Phase 1 — Capability Completion | 🟡 Mostly shipped; 3 open items | Health-probe promotion out of `IDEA`, execution-mode UI, `SCRAPER_BACKEND_URL` resolver still open | #3 Reuse Before Creation |
| Phase 2 — Reliability Moat | 🚧 Active battlefield | Mission suite at 5 missions / 12 tests; gate target = 20 missions / pass^3 ≥ 0.8; coverage 30/16 → target 50/30; skip count 125 → <30 | #5 Verify Before Trust, #13 No Silent Failure |
| Phase 3 — Own Model v1 | 🟢 Designed, not started | `vision_strategic_positioning.md` §Phase 3; pipelines + Kaggle orchestrator + canary manager all exist; awaiting data flywheel maturity | #1 Eternal Brain, #11 Memory Must Compound |
| Phase 4 — Public Benchmark Attacks | 🟢 Designed, not started | B1/B2/B3/B5 publishable scripts not yet written | #5 Verify Before Trust, #13 Deliver Honestly |
| Phase 5 — Production Hardening | 🟢 Designed, not started | SLA enforcement, pen-test pass, thin-client launch | #6 Policy Before Power |

**Net diagnosis:** SupremeAI is structurally past the "is the foundation honest?" gate (M0 + M1 + Phase 0 + Phase 1 close-out) and is now entering the "does the machinery compound?" phase (M2 + M3 + Phase 2 gate). The highest-leverage planning question for the next 90 days is therefore *not* "what new feature should we ship?" but "what is the smallest set of moves that converts the existing capability surface into measured reliability, measured cost, measured memory, and measured Bengali depth?" That question frames every lever in §4.

---

## 2. Strategic Diagnosis — Where the Leverage Is

The planning department's job is to direct finite engineering hours (single-builder cadence per `vision_strategic_positioning.md` §6: 50% product / 30% moat / 20% ops) at the moves with the highest impact-to-effort ratio. Below is the 2×2 matrix that frames this memo's recommendations. Each lever is placed by (a) battlefield impact if completed and (b) Constitution-alignment cost — where "cost" means how much rule-bending, duplication, or governance shortcut the lever would require.

```text
                   HIGH Constitution-alignment cost
                            (AVOID unless reframed)
                                  │
       L7-colibrì-style           │
       second graph         ──────┼──────    (none — by design)
                                  │
                                  │
───── LOW impact ─────────────────┼──────────── HIGH impact ─────
                                  │       L1 Reliability Moat gate
                                  │       L2 Orphan spine (Class C)
                                  │       L3 False-assurance purge (Class G)
                                  │       L4 Memory flywheel (M3 → Phase 3)
                                  │       L5 Context engine (M2)
                                  │       L7 Radical transparency dashboard
                                  │
                       L6 Bengali adapter (Phase 3 first)
                                  │
              LOW Constitution-alignment cost
                  (DO NOW — these are the levers)
```

**The headline:** every lever we actually need is on the *low-cost, high-impact* quadrant. That is not luck; it is the Constitution doing its job. The vision document already names the battlefields we refuse to fight (raw parameter count, frontier reasoning benchmarks, multimodal scale, pretraining size records), and the `UNIFIED_NEXT_ROADMAP_2026-09-15.md` §5 already lists the ten standing prohibitions (no second memory backend, no Playwright replacement, no quota tricks, no K8s expansion without metrics, no raw HTML/SVG to DOM, no heavy payloads through control plane, no hundreds of raw tools to every model, no new OSS without measured need, no architecture-debt-blocks-progress, no documentation-only completion claims). The planning department's job is therefore *subtractive*: remove the friction that is keeping already-built capability from compounding.

The three friction sources, in priority order, are:

1. **Connection friction** — 57 orphan route families (`SYSTEM_DEFECT_REGISTER_2026-09-15.md` §3) and 1,157 backend stub hits (`§4`). Capability exists; nobody can use it. This violates Constitution Core #2 ("Build complete Circles") and #13 ("No Silent Failure") because the system silently returns 404 or mock data instead of honestly saying "this capability is not wired."
2. **Verification friction** — pass^k harness exists but only 5 missions are in the suite; the gate cannot fire. This violates Constitution #5 ("Verification Before Trust") at the system level: we have the instrument but not the dataset.
3. **Memory friction** — 15+ competing stores dilute the flywheel. Memory cannot compound across sessions if every session writes to a different store. This violates Constitution #11 ("Memory Must Compound") and #1 ("Eternal Brain") at the architectural level.

Each lever in §4 attacks one of these three frictions. No lever introduces a fourth.

---

## 3. What "One of the Best AI Models" Means for SupremeAI

Per `vision_strategic_positioning.md` §0, the planning department explicitly re-states the dream as an engineering claim, not a slogan, so that every lever in this memo can be measured against it:

> **A frontier model, shipped as a bare API, loses to a governed system on any field where the SYSTEM is the product: verified reliability, task completion, memory that compounds, cost per solved problem, and language/regional depth. SupremeAI will beat the best models-as-deployed on those fields — and will own small models of its own where they matter most.**

This means "one of the best AI models" is *not* a single leaderboard rank. It is a scoreboard with six cells, each owned by a battlefield:

| Battlefield | What "best in the world" looks like for SupremeAI | Today's measurement | Phase 2 gate | Phase 4 publication target |
|---|---|---|---|---|
| **B1 Reliability** | pass^3 ≥ 0.8 on a 20-mission suite, published with reproducible scripts; frontier APIs visibly degrade on pass^3/pass^5 | pass^k harness live in CI; only 5 missions in suite | ≥ 0.8 internal on 20 missions | ≥ 0.8 published head-to-head vs raw-API pass^3 baseline |
| **B2 Task Completion** | GAIA-text subset + SWE-bench-lite-style repo-repair harness; SupremeAI's machinery beats the same model without machinery | unmeasured | 20-mission suite green | ≥ frontier-API-as-deployed baseline +10pts |
| **B3 Cost** | $ per verified task published; ≤ 1/10 of paid-stack baseline on comparable quality | unmeasured | instrumented | published |
| **B4 Memory** | Repeat-task cost delta: task #50 is ≥ 30% cheaper than task #5 | unmeasured | measured via learning events | ≥ 30% repeat-task cost reduction |
| **B5 Bengali Depth** | Bangla eval set v1; own adapter beats Gemini/GPT-class on Bangla conversational quality and idiom at 1/50 the cost | unmeasured | eval set v1 | adapter wins head-to-head |
| **B6 Integration Surface** | One-URL connect → first verified task < 3 minutes; MCP marketplace live | minutes | < 5 min | < 3 min |

This scoreboard is the planning department's definition of "done." Every lever in §4 must advance at least one cell. The continuous-planning cadence in §7 exists to keep this scoreboard honest.

---

## 4. The Seven Strategic Levers (Constitution-Anchored)

Each lever below is structured identically: Constitution anchor → battlefield(s) advanced → why now → concrete next actions (2–4) → existing assets it extends (Reuse Before Creation) → anti-patterns avoided → success metric → owner Circle.

### Lever L1 — Close the Reliability Moat Gate (Phase 2 → Mission Suite at 20 + pass^3 ≥ 0.8)

**Constitution anchor:** #5 Verification Before Trust, #13 No Silent Failure, Constitution Core #8 ("Verify before trust").

**Battlefield(s):** B1 (primary), B2 (secondary).

**Why now:** The pass^k harness is already live in CI (`scripts/ci/mission_passk.py`), but only 5 missions / 12 tests exist. The gate target is 20 missions / pass^3 ≥ 0.8. Until that gate fires, *every other Phase 3+ investment is premature* — there is no measured reliability number to beat with an adapter, no honest baseline to publish against frontier APIs in Phase 4. This is the single highest-leverage move in the project right now because it unlocks three downstream battlefields (B1, B2, B4) at once.

**Concrete next actions:**

- **L1.1 — Mission suite expansion (5 → 20).** Author 15 additional missions in `tests/missions/` covering: (a) research-and-summarize (scout corpus already live), (b) repo-repair (SWE-bench-lite-style), (c) file-work (already partially stubbed in ERR-B02), (d) scheduling/orchestration (uses M1 Run fabric), (e) browser-mediated external capability (uses Phase 1 scout). Each mission must be runnable in CI without paid credentials (Constitution #14 Sustainable Cost) — use the same free-tier chain the production system uses.
- **L1.2 — Nightly pass^k on the live zero-cost chain.** The harness exists; schedule it nightly (not just on PR) and publish the artifact to `reports/mission_passk.json` + a dated snapshot under `docs/audits/passk_history/`. The historical curve *is* the B1 narrative.
- **L1.3 — Kill-criteria honesty check.** Per `vision_strategic_positioning.md` §6: "if by end of Phase 2 the mission-suite pass^3 cannot reach 0.7, the verify-loop design is wrong — redesign before Phase 3." This lever's exit gate explicitly includes the kill-criteria check-in. If pass^3 stalls below 0.7, the planning department must redesign the verify loop before authorizing Phase 3 spend.

**Existing assets it extends (Reuse Before Creation):** `scripts/ci/mission_passk.py`, `tests/missions/` (5-mission seed), `backend/runs/` (M1 canonical Run fabric), `core/self_benchmark.py` (pass^k estimator), `scout/persistence.py` (research corpus).

**Anti-patterns avoided:** no new benchmark framework (extends existing); no paid APIs in CI (uses zero-cost chain); no documentation-only "we measured reliability" claim (every number traces to a committed script).

**Success metric:** `reports/mission_passk.json` shows ≥ 0.8 pass^3 across 20 missions for 7 consecutive nights before Phase 3 adapters are authorized.

**Owner Circle:** C1 (Code & Quality) for mission authoring; C5 (Execution) for harness wiring; C3 (Evolution) for learning-event labeling.

---

### Lever L2 — Connect the Orphan Spine (Class C: 57 Route Families)

**Constitution anchor:** #3 Reuse Before Creation, #13 No Silent Failure, Constitution Core #2 ("Build complete Circles") and #10 ("Make important behavior observable").

**Battlefield(s):** B2 (primary), B6 (secondary).

**Why now:** The defect register proves that 57 backend route families — including the entire Missions Engine (11 endpoints), the MCP Hub & Client Management (7 endpoints), the Federated Capability Circles (4 endpoints), and 35 newly-identified route families — have *zero* frontend caller. This is the largest single source of "looks dead but isn't" friction in the project. Constitution #13 (No Silent Failure) is violated at the platform level: the system has the capability but silently returns 404 from the user's view. Connecting these routes is *not new feature work* — it is finishing what was already built. Per AGENTS.md Mandatory Rule #2 (Operational Reality Over Superficial Artifacts), Zero-Gap demands the complete end-to-end capability, not just the backend route existing.

**Concrete next actions:**

- **L2.1 — Missions Engine frontend wiring (11 endpoints).** The missions engine is the *runtime* expression of the M1 Run fabric. Until users can see missions in the UI, the entire Run investment is invisible. Wire: `POST /api/v1/missions` (create), `GET /api/v1/missions` (list), `GET /api/v1/missions/{id}` (state & checkpoints), `POST /api/v1/missions/{id}/start`, `/advance`, `/approve` (HITL gate UI!), `/fail`, `/repair`, `/cancel`, `GET /api/v1/missions/{id}/trace`, `GET /api/v1/missions/{id}/trace/stream` (SSE). The HITL approval UI is Constitution #6 (Policy Before Power) made visible.
- **L2.2 — MCP Hub client management UI (7 endpoints).** Wire slug claiming, client list, provisioning, status/heartbeat, secret rotation, revocation. This is the user-facing expression of Constitution #2 (Capability Sovereignty): the tenant can see and rotate their own capability surface.
- **L2.3 — Federated Capability Circles observer (4 endpoints).** `GET /api/v1/circles`, `/circles/health`, `/circles/events`, `POST /circles/dispatch` — these are the operational dashboard for the 4 bounded Circles. Wiring them is Constitution Core #10 ("Make important behavior observable").
- **L2.4 — The 35 newly-identified route families.** Triage by impact: CommandCenter Admin API (already-tested per STATUS.md item 16), Image & Tool Transformation endpoints, Admin/Governance endpoints, Agent/Memory endpoints. Prioritize those that close Class B static shells (ERR-B01 through ERR-B05) — the same wiring fixes both a Class C orphan and a Class B shell in one stroke.

**Existing assets it extends:** all 707 backend routes already exist and are mounted; `frontend/src/services/controlPlane.ts` (governed API gateway client); `frontend/src/store/adminStore.ts`; the 4 bounded Circles contracts in `backend/core/circles/`.

**Anti-patterns avoided:** no new backend code (Reuse Before Creation — capability exists); no new frontend state-management library (extends `adminStore.ts`); no bypassing the SupremeKernel single-door facade (every call routes through `/api/v1/kernel/dispatch` per the North-Star architecture).

**Success metric:** `scripts/feature_parity_sentinel.py` reports 0 orphan route families within 60 days; the 57 families are reduced to ≤ 5 documented-and-intentional admin-only endpoints.

**Owner Circle:** C2 (Governance) for HITL approval UI; C5 (Execution) for Missions/MCP wiring; C1 (Code & Quality) for parity sentinel enforcement.

---

### Lever L3 — Purge False Assurance (Class G Mocks)

**Constitution anchor:** #5 Verification Before Trust, #13 No Silent Failure, #6 Policy Before Power, Constitution Core #8 ("Verify before trust").

**Battlefield(s):** B1 (primary), B2 (secondary).

**Why now:** Class G defects are the most constitutionally offensive category in the entire defect register because they *fabricate success*. `ERR-G01` (billing_api returns a fabricated Stripe session — users get paid entitlements without payment), `ERR-G02` (production_deploy uses `time.sleep(2)` to simulate deployments), `ERR-G03` (security-scan endpoint returns unconditional `score: 100`), `ERR-G04` (cloud_sandbox_orchestrator returns mock stdout), `ERR-G05` (browser tasks fabricate autonomous step success), `ERR-G06` (Crown Jewel module docstring literally calls itself "mock endpoints" while mounted on live API), `ERR-G07` (`find_stub_data.py` passes despite 1,157 stubs because it scans only 20 literal patterns). These are not bugs; they are *violations of the Constitution's identity*. A system that silently fabricates success cannot be "one of the best" by definition.

**Concrete next actions:**

- **L3.1 — Eliminate mock Stripe checkout (ERR-G01).** Either wire the real Stripe SDK behind the existing route (if a Stripe key exists in Infisical), or fail-closed with HTTP 503 and a clear "billing not configured" message. There is no third option that honors Constitution #13.
- **L3.2 — Replace `production_deploy` simulation with real runner (ERR-G02).** The repo already has `scripts/deploy/blue_green_deploy.py`, `canary_deploy.py`, `disaster_recovery_test.py`, `trigger_render_deploy.py`, `check_render_auto_deploy.py`. Wire `production_deploy.py` to call the real `trigger_render_deploy` path; eliminate the `time.sleep(2)` mock entirely.
- **L3.3 — Replace Crown Jewel mocks (ERR-G02/G03/G05/G06).** `_crown_jewel.py` should call `PlaywrightBrowserAgent.screenshot()` (real screenshot, not 1×1 transparent PNG), pass DOM to `ModelRouter` (real AI summary, not static string), run a real security scan or fail-closed with `{"success": false, "error": "scanner not configured"}`. Either rename the module away from "mock endpoints" in its docstring, or delete it. A live-mounted mock module is a Constitution #13 violation.
- **L3.4 — Strengthen `find_stub_data.py` (ERR-G07).** Expand the pattern set from 20 literals to a comprehensive gate (target: detect ≥ 95% of the 1,157 known stubs). Until the gate can detect them, it cannot prevent regressions. This is Constitution Core #10 ("Make important behavior observable") applied to the test infrastructure itself.

**Existing assets it extends:** `PlaywrightBrowserAgent`, `ModelRouter`, `scripts/deploy/trigger_render_deploy.py`, `infisical_loader.py` for real secret access, `backend/core/middleware/security.py` (which already has the encoded-traversal hardening from the 2026-09-12 security audit).

**Anti-patterns avoided:** no new billing service (wires existing Stripe SDK if present, else fails closed); no new deployment orchestrator (wires existing `trigger_render_deploy`); no new security scanner (wires existing or fails closed honestly); no relaxation of the stub-detection gate to make CI green.

**Success metric:** Class G defect register has 0 open items within 30 days; `find_stub_data.py` reports the full 1,157-stub count (or whatever the real count is after L3.1–L3.4) and CI fails on any new stub introduction.

**Owner Circle:** C2 (Governance) for billing/security fail-closed review; C5 (Execution) for deploy wiring; C1 (Code & Quality) for stub-gate strengthening.

---

### Lever L4 — Activate the Memory Flywheel (M3 Consolidation → Phase 3 Data)

**Constitution anchor:** #1 Eternal Brain, #11 Memory Must Compound, #3 Reuse Before Creation (kill duplicates, not build new), Constitution Core #3.

**Battlefield(s):** B4 (primary), B3 (secondary — fewer stores = lower cost per recall).

**Why now:** The defect register identifies 15+ competing memory store modules under `backend/memory/`. M3's first deliverable per the roadmap is *not code* — it is a decision table that gives every store a keep/merge/archive verdict with caller evidence. Until that decision exists, the flywheel cannot compound: every solved task writes to a different store, so task #50 cannot benefit from task #5's experience. This is the single largest *architectural* obstacle to Phase 3 (Own Model v1), because the data flywheel that would train the Bengali adapter, the behavioral alignment adapter, and the router/verifier micro-model depends on a *single authoritative memory path* with consistent schema, provenance, and confidence.

**Concrete next actions:**

- **L4.1 — M3 decision table (not code yet).** Use `scripts/audit_module_wiring.py` + the 1,189-module import-walk data to produce a verdict for every `backend/memory/*` module: keep (canonical), merge (into canonical with caller rewrites), or archive (zero callers, retired with evidence). This is Constitution #3 (Reuse Before Creation) at the architectural level — we are not building a new memory system, we are *consolidating* the existing 15 into the canonical ai_memory Phase-C path.
- **L4.2 — Memory writes attach to completed Runs (M1 dependency).** M1 is code-complete; wire every memory write to fire on Run `FINALIZED` events. This is the data-flywheel plumbing: every verified task becomes a training-data candidate.
- **L4.3 — Hybrid ranking implementation.** Per `UNIFIED_NEXT_ROADMAP_2026-09-15.md` §M3: semantic + lexical + recency + confidence + scope_match. The ai_memory Phase-C schema (already executed on Supabase per STATUS.md item 0.5) has the columns; the ranking function is the missing piece.
- **L4.4 — Retention job wiring.** `fn_ai_memory_retention_cleanup` exists in the SQL (M0.6); wire it into the Orchestrator's periodic task. Constitution #14 (Sustainable Cost): memory cannot grow unbounded.

**Existing assets it extends:** `backend/core/ai_memory/vector_store.py` (canonical 384-dim path), `backend/memory/hierarchical_tree.py` (keep — strategic), `services/memory_service.py`, the `ai_memory_phase_c.sql` already executed on Supabase, M1 Run fabric for event anchoring.

**Anti-patterns avoided:** **no new memory backend** (standing prohibition §5.1 of `UNIFIED_NEXT_ROADMAP_2026-09-15.md`); no ChromaDB revival (archive, not delete — Constitution #7 Reversible Evolution); no premature adapter training (waits for the flywheel to actually compound, per Phase 3 gate).

**Success metric:** decision table merged; canonical path handles chat recall in a prod-shaped test; duplicate stores archived with zero-caller proof; cross-session recall precision measured and trending up; the data flywheel is *observable* (a dashboard showing daily memory writes, recall-hit rate, and retention-cleanup runs).

**Owner Circle:** C3 (Evolution) owns memory consolidation; C1 (Code & Quality) audits the verdicts; C5 (Execution) wires the Run-anchored writes.

---

### Lever L5 — Wire the Context Engine (M2)

**Constitution anchor:** #14 Sustainable Cost (token reduction), #11 Memory Must Compound (context is the read side of memory), Constitution Core #3 (Reuse Before Creation).

**Battlefield(s):** B3 (primary — tokens-per-task reduction), B4 (secondary — better context = better recall = better compounding).

**Why now:** M1 (Canonical Run) is code-complete, which means `run_id` is available as the scope anchor that M2 needs. Per the roadmap's verdict (§1 of `UNIFIED_NEXT_ROADMAP_2026-09-15.md`), "Run before Context" was chosen specifically because the Context Engine's scope chain is `…PROJECT → CHAT → RUN → STEP`, and `run_id` cannot anchor scope until a canonical Run exists. M2 is therefore unblocked and is the next P0 milestone. Without M2, every prompt sent to the LLM gateway is unbounded — Constitution #14 (Sustainable Cost) is violated on every chat turn, and the cost-per-verified-task metric (B3) cannot be published because there is no token-budget enforcement to measure against.

**Concrete next actions:**

- **L5.1 — Files metadata upgrade (L0/L1/L2).** Per OSS plan §4: add `summary_l0`, `summary_l1`, `content_ref`, `parent_id`, `hash`, `version` to the Files metadata schema via a single Alembic revision (canonical path per the hardening decision). This is the structured-context foundation — without L0/L1/L2, the budgeter has nothing to budget.
- **L5.2 — Context budgeter.** The OSS plan §3.4 specifies the YAML budget shape. Implement the budgeter that selects the smallest sufficient context for a given prompt: prefer L0 (one-line summary) → L1 (paragraph summary) → L2 (full content) only when lower levels are insufficient. This is Constitution #14 made executable.
- **L5.3 — Scope chain enforcement.** `GLOBAL → USER → WORKSPACE → PROJECT → CHAT → RUN → STEP` using M1's `run_id`. Every context item must carry its scope, and tenant filter + provenance are enforced on every retrieval (Constitution Core #5 "Preserve tenant ownership" + #7 "Think before acting").
- **L5.4 — Measurement harness.** Per `UNIFIED_NEXT_ROADMAP_2026-09-15.md` §M2 exit criteria: "tokens-per-task before/after." This is the B3 metric instrumentation. Without it, "we reduced context cost" is a documentation-only claim (prohibited).

**Existing assets it extends:** M1 Run fabric (`run_id` is the scope anchor), existing Files module, `backend/memory/` (the *read* side of M2 is the canonical path from L4 — this is why M2 and M3 are sibling milestones, not sequential), the existing chat/SSE pipeline that already has Auto-RAG injection (extend, not replace).

**Anti-patterns avoided:** **no new context database** (standing prohibition); no separate "context store" — M2 reads from the M3 canonical memory path; no L0/L1/L2 generation that bypasses governance (summaries are generated through the same model gateway, governed by the same policy).

**Success metric:** one context assembly path used by both chat and at least one agent flow; token reduction measured and recorded (target: ≥ 30% reduction on a representative workspace task); tenant-leak tests green.

**Owner Circle:** C3 (Evolution) owns context assembly; C5 (Execution) owns the budgeter enforcement point; C1 (Code & Quality) owns the measurement harness.

---

### Lever L6 — Stand Up the Bengali Adapter Track (Phase 3, First Adapter)

**Constitution anchor:** #1 Eternal Brain (our weights, our registry, swappable), #9 Provider Agnostic User Loyal (the user asks SupremeAI, not Gemini), #11 Memory Must Compound (the flywheel's first downstream product), #14 Sustainable Cost (1/50 the cost of the base model).

**Battlefield(s):** B5 (primary — the one battlefield where SupremeAI is *native* and the giants are *tourists*), B3 (secondary — local adapter = lower cost per task).

**Why now:** Per `vision_strategic_positioning.md` §Phase 3, the Bengali conversation adapter is the *first* adapter to train because it is the one field where the giant labs' "their own strong field" logic flips — ours is native, theirs is tourist. The training infrastructure already exists in the repo (`pipelines/synthetic_data_pipeline.py` → `tools/learning/rlhf_pipeline.py` → `tools/learning/model_trainer.py` → `core/kaggle_orchestrator.py` → `evolution/canary_manager.py`). What is *missing* is the data flywheel's maturity (L4) and the Bengali eval set v1 (the Phase 2 gate's B5 cell). L6 is therefore sequenced *after* L1 (reliability gate fires) and L4 (memory flywheel produces training pairs), but the planning department must begin the *prep work* now so the adapter can ship the moment the gate clears.

**Concrete next actions:**

- **L6.1 — Bengali eval set v1 (Phase 2 gate requirement, B5 cell).** Build from governed sources only (scout corpora + project's own Bangla documentation + curated conversational pairs). Target: 200–500 evaluation items covering conversation, summarization, code-switching (Banglish). This is the *measuring stick* before any training begins — Constitution #5 (Verify Before Trust) applied to the eval, not just the model.
- **L6.2 — BengaliNormalizer audit + corpus preparation.** The normalizer already exists (per `vision_strategic_positioning.md` §2 strengths). Use it to prepare the training corpus from the flywheel's Bangla pairs. Privacy-scrub via the same `learning_events` pipeline already in `core/learning/`.
- **L6.3 — Base model selection (founder decision — see §10).** The vision document specifies "an open 2–7B instruct model." The planning department recommends the founder shortlist 2–3 candidates (e.g., Qwen2.5-3B-Instruct, Llama-3.2-3B-Instruct, Mistral-7B-Instruct-v0.3) — the choice is irreversible-ish because the LoRA adapter is base-specific. This is a Phase 3 gate decision; L6.3 is the *preparation*, not the selection.
- **L6.4 — Kaggle GPU scheduling dry-run.** `core/kaggle_orchestrator.py` exists; verify it can actually claim and use the ~30h/week of free GPU before the adapter training is gated on it. Constitution #14 (Sustainable Cost): if Kaggle is unreliable, the plan must use RunPod burst (~$20–50/mo) only when a promotion gate justifies it.

**Existing assets it extends:** `pipelines/synthetic_data_pipeline.py`, `tools/learning/rlhf_pipeline.py` (now honest per STATUS.md Phase 0), `tools/learning/model_trainer.py`, `core/kaggle_orchestrator.py`, `evolution/canary_manager.py`, `scripts/i18n/bangla_translator.py` + `banglish_converter.py`, the entire Bangla documentation corpus under `docs/plans/ROADMAP_ECOSYSTEM_ARCHITECTURE_BN.md` and elsewhere.

**Anti-patterns avoided:** **no frontier model training** (explicitly refused battlefield per `vision_strategic_positioning.md` §1); no Bengali adapter promotion without pass^k gate (Constitution #7 Reversible Evolution — adapter must beat its base model by ≥ 10% on its own eval AND pass^3 must not regress); no Bengali adapter as the *only* path (Graceful Degradation: if adapter is cold, chain falls back to Groq/Gemini transparently).

**Success metric:** Bengali eval set v1 merged; adapter training dry-run completes on Kaggle within the 30h/week budget; canary promotion path proven (even on a dummy adapter); when the Phase 3 gate fires, the adapter ships behind pass^k ≥ 0.8 on its own eval + no pass^3 regression on the mission suite.

**Owner Circle:** C3 (Evolution) owns training; C2 (Governance) owns canary/HITL; C5 (Execution) owns serving registration in the provider-agnostic gateway.

---

### Lever L7 — Radical Transparency Dashboard (The Founder's Demo)

**Constitution anchor:** Constitution Core #10 ("Make important behavior observable"), #13 No Silent Failure, #5 Verify Before Trust (the dashboard *is* the verification made public).

**Battlefield(s):** B1 (pass^3 published), B3 (cost-per-task published), B6 (one-URL connect → first verified task timer published).

**Why now:** Per `vision_strategic_positioning.md` §Phase 5: "The Founder's Demo: a public page showing live system truth — uptime, pass^3, tasks solved, cost per task, adapter evals. Radical transparency as brand." But the planning department's position is that this cannot wait until Phase 5. The *moment* the B1/B3 metrics exist (L1 + L5 produce them), they must be published — internally first, then publicly. Constitution Core #10 does not say "make important behavior observable when convenient." A system that hides its own reliability numbers is, constitutionally, a system with something to hide. This is also the *marketing department* for a one-person army: public numbers are the only marketing that scales without hiring.

**Concrete next actions:**

- **L7.1 — Internal scoreboard page (frontend route `/scoreboard`).** Show: tonight's pass^3 (from `reports/mission_passk.json`), today's cost-per-verified-task (from L5's measurement harness), today's memory-write count + recall-hit rate (from L4), today's Bengali eval score (from L6.1 once it exists), and a 30-day trend line for each. All numbers trace to committed scripts; the page itself is a thin React component reading from existing endpoints.
- **L7.2 — Public scoreboard subset (Phase 4 prep).** Once the internal scoreboard is stable for 30 days, publish a *subset* publicly: pass^3 on the mission suite, $ per verified task, and (when L6 ships) the Bengali adapter's head-to-head score vs the zero-cost chain. This is the Phase 4 "Public Benchmark Attacks" gate made operational.
- **L7.3 — Honest-failure publication.** When pass^3 drops below 0.7, the dashboard must show that — not hide it. Constitution #13: the system reports honestly. This is also the kill-criteria visibility mechanism from §6 of the vision document.

**Existing assets it extends:** `reports/mission_passk.json` (already produced by CI), `scripts/ci/build_test_failure_trend.py`, `scripts/monitoring/cost_analyzer.py`, the existing admin dashboard infrastructure (`SupremeAIAdminDashboardProvider.tsx`), the existing `/api/v1/admin/stats` real endpoint (shipped per STATUS.md Phase 1 item 0.5).

**Anti-patterns avoided:** no new metrics pipeline (every number traces to an existing committed script); no vanity metrics (no "users signed up" or "messages sent" — only battlefield metrics); no public dashboard before internal stability (avoids publishing noise); no hiding regressions (Constitution #13 enforced at the UI level).

**Success metric:** internal scoreboard live within 30 days; public subset live within 60 days of internal stability; 0 instances of a metric being silently removed after a regression.

**Owner Circle:** C1 (Code & Quality) owns metric integrity; C6 (Infra) owns the dashboard hosting; C2 (Governance) owns the honest-failure publication policy.

---

## 5. The "Do Not Do" List (Constitution-Prohibited, Restated for Planning Discipline)

This section restates the standing prohibitions so that every future Head of Planning memo begins from the same baseline. These are not suggestions; they are encoded in `.github/constitution/rules.yml` (machine-enforced where possible) and in `UNIFIED_NEXT_ROADMAP_2026-09-15.md` §5 (architecturally enforced). Any lever that would require violating one of these is *out of scope for this planning department*, no matter how attractive the impact.

1. **No building a frontier model.** Refused battlefield per `vision_strategic_positioning.md` §1. The planning department will never propose pretraining a 70B+ model. Own adapters only, on narrow fields where small models beat big ones *because* the task is narrow and the data is ours.
2. **No duplicate subsystem.** No second memory backend, no second dependency graph, no second QA gate, no second browser stack, no second run system. M2–M7 *consolidate and extend*, never duplicate.
3. **No Playwright replacement.** M4 wraps Playwright; it does not replace it with Browser Use or any alternative. Chromium does not load into the API process path.
4. **No free-tier quota tricks or account multiplication.** Standing constraint. Multi-account/resource pools are configurable adapters, not assumptions that vendors provide unlimited quota.
5. **No metrics-less K8s/infra expansion.** No scaling decision is authorized without a measured number justifying it. Constitution #14 (Sustainable Cost) is operational, not aspirational.
6. **No raw model HTML/SVG to DOM.** M8 ships a structured diagram JSON schema with a server-safe renderer. Frontend owns HTML/SVG; model output never enters DOM raw.
7. **No heavy payloads through the control plane.** M7's `ref://` semantics exist precisely to keep large artifacts out of the MCP control plane. Control plane carries references, never payloads.
8. **No hundreds of raw tools exposed to every model.** M6's lazy discovery keeps the model-facing surface small while capability count grows. Constitution #12 (Least Privilege, Maximum Capability).
9. **No new OSS dependency without measured need.** Colibrì explicitly rejected (P4 in both source plans). Every new dependency must justify itself with a measurement, not a preference.
10. **No architecture debt blocking progress.** Baseline-N policy (`vision_strategic_positioning.md` §6, encoded in M5): legacy debt does not block progress; new debt blocks progress. The planning department enforces this by *not* proposing refactors as preconditions for new work unless the refactor is the work.
11. **No documentation-only completion claim.** Every "done" in this memo traces to a committed script, a passing test, or a runtime evidence file. AGENTS.md Mandatory Rule #2 (Operational Reality Over Superficial Artifacts).
12. **No silent failure.** Constitution #13. Every failure path must detect, explain, repair/retry, verify, report honestly. Class G defects (Lever L3) are the most egregious current violation of this principle.

---

## 6. Constitution Compliance Matrix

This matrix exists so that any reader — founder, future Head of Planning, or external auditor — can verify that every lever in §4 *serves* (does not violate) a Constitution principle. "Serves" means the lever advances the principle's intent. "Neutral" means the lever does not affect the principle. **No cell in this matrix reads "violates."** If a future iteration of this memo introduces a lever that would require a "violates" cell, that lever is rejected at the planning stage, not at the implementation stage.

| Lever | #1 Eternal Brain | #3 Reuse Before Creation | #5 Verify Before Trust | #6 Policy Before Power | #7 Reversible Evolution | #8 Graceful Degradation | #9 Provider Agnostic | #10 One System Many Surfaces | #11 Memory Must Compound | #12 Least Privilege | #13 No Silent Failure | #14 Sustainable Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **L1 Reliability Moat** | serves | serves (extends harness) | **primary** | serves (HITL) | serves (rollback warm) | serves (retry classification) | neutral | serves (missions use Run) | serves (labeled traces) | neutral | **primary** | serves (zero-cost chain) |
| **L2 Orphan Spine** | serves (memory wires) | **primary** (no new code) | serves (real endpoints) | serves (HITL UI) | neutral | serves (orphan→fail-closed) | serves (capability surface) | **primary** | serves (trace events) | serves (admin-only routes) | **primary** (no silent 404) | neutral |
| **L3 False-Assurance Purge** | neutral | serves (uses existing) | **primary** | serves (fail-closed) | neutral | serves (honest errors) | neutral | neutral | neutral | neutral | **primary** | neutral |
| **L4 Memory Flywheel** | **primary** | **primary** (consolidates 15) | serves (decision table) | neutral | serves (archive, not delete) | neutral | neutral | neutral | **primary** | neutral | serves (observable writes) | serves (retention job) |
| **L5 Context Engine** | serves (read side) | serves (no new DB) | serves (budgeter) | serves (tenant filter) | neutral | serves (degraded context) | neutral | serves (chat + agent) | serves (recall + write) | serves (scope enforcement) | neutral | **primary** (token reduction) |
| **L6 Bengali Adapter** | **primary** (our weights) | serves (existing pipelines) | **primary** (pass^k gate) | serves (canary/HITL) | **primary** (rollback warm) | **primary** (falls back to chain) | **primary** (native depth) | serves (one of N providers) | **primary** (flywheel product) | neutral | neutral | **primary** (1/50 cost) |
| **L7 Radical Transparency** | serves (visible memory) | serves (existing endpoints) | **primary** (publish verification) | serves (audit visible) | serves (regression visible) | neutral | neutral | serves (one dashboard) | serves (memory metrics) | neutral | **primary** (honest failure) | serves (cost published) |

The matrix is intentionally a single grid rather than per-lever lists because the planning department's reading of the Constitution is *holistic*: a lever that serves only one principle is rarely worth doing. Every lever in §4 serves at least four principles, and the primary ones (bolded) trace directly to the battlefields in §3.

---

## 7. Continuous Planning Cadence

The user has asked the Head of Planning to "keep doing this as continuous process." The planning department therefore formalizes the cadence below so that future memos are predictable, comparable, and auditable. This is *not* a meeting schedule — it is a publication schedule. Every cadence slot produces a committed artifact under `docs/plans/HEAD_OF_PLANNING_*.md` or an update to this memo's lineage.

| Cadence | Artifact | Owner | Constitution principle served |
|---|---|---|---|
| **Weekly** | `HEAD_OF_PLANNING_WEEKLY_<YYYY-MM-DD>.md` — defect-burn review (Class A/G), orphan-spine delta (Class C), false-assurance watch (Class G), pass^k nightly trend | Head of Planning (this role) | #13 No Silent Failure, #5 Verify Before Trust |
| **Bi-weekly** | Update to `HEAD_OF_PLANNING_STRATEGIC_LEVERAGE_<date>.md` milestone health (M2, M3, M4 progress vs. exit criteria) | Head of Planning + Circle owners | Constitution Core #10 (observable) |
| **Monthly** | Scoreboard publication — B1/B3/B4/B5/B6 metrics, even if "unmeasured" is the honest entry | Head of Planning | #13, #5, Constitution Core #8 |
| **Quarterly** | Phase gate review — Phase 2 → 3 → 4 transition criteria, kill-criteria honesty check, budget math reconciliation (still under ~$75/mo?) | Head of Planning + Founder | #14 Sustainable Cost, vision §6 kill criteria |
| **Ad-hoc (event-driven)** | `HEAD_OF_PLANNING_INCIDENT_<YYYY-MM-DD>_<slug>.md` — for any production incident, security finding, or Constitution violation detected | Head of Planning (within 48h of event) | #13, #6 Policy Before Power |

**The memo's own evolution rule:** This v1 memo is *never edited in place* after issuance. Corrections, additions, or reversals are issued as v2, v3, … siblings, with explicit "supersedes" / "superseded_by" frontmatter. This honors AGENTS.md Mandatory Rule #6 (Architectural Plans as Protected Living Assets — plans are evolved with shift matrices, never discarded). The lineage of planning reasoning is itself auditable evidence of the planning department's discipline.

**Continuous-process automation hook:** The planning department recommends (as a future small PR, not in this memo's scope) a GitHub Action that opens an issue every Monday 09:00 UTC titled "Head of Planning — Weekly memo due <date>" with a template pre-filled from the previous week's defect register diff and the pass^k nightly trend. This is Constitution #13 (No Silent Failure) applied to the planning function itself: if the planning department stops publishing, the system must notice.

---

## 8. Next 14 Days — Concrete Sprint Plan

The 14-day window below is the planning department's commitment for the next sprint. Every item is small, evidence-driven, and tied to a lever from §4. No item requires a Constitution exemption. Items are sequenced so that the lowest-risk, highest-leverage work lands first.

| # | Action | Lever | Owner Circle | Exit evidence | Risk |
|---|---|---|---|---|---|
| 1 | Triage Class G defects L3.1–L3.4; produce a fix-or-fail-closed PR for ERR-G01 (mock Stripe) and ERR-G02 (mock deploy) | L3 | C2 + C5 | PR merged with before/after evidence; no `mock_session_123` or `time.sleep(2)` simulation remains in the codebase | Low — wires existing infra |
| 2 | Expand mission suite from 5 → 8 missions (3 new: one research-summarize, one repo-repair, one file-work) | L1.1 | C1 + C5 | 3 new mission files in `tests/missions/`; pass^k runs green on the expanded suite | Low — extends existing pattern |
| 3 | Begin M3 decision table (L4.1) — produce verdicts for the 15+ `backend/memory/*` modules using `scripts/audit_module_wiring.py` | L4 | C3 + C1 | `docs/audits/M3_MEMORY_DECISION_TABLE.md` draft with keep/merge/archive verdicts + caller evidence | Medium — requires careful import-walk |
| 4 | Wire the 11 Missions Engine endpoints to the frontend (L2.1) — focus first on `GET /missions` (list) + `GET /missions/{id}` (detail) + `GET /missions/{id}/trace/stream` (SSE) | L2 | C2 + C5 | `feature_parity_sentinel.py` orphan count drops by ≥ 11; missions visible in UI | Medium — frontend + SSE wiring |
| 5 | Schedule nightly pass^k (L1.2) — currently runs on PR; add a GitHub Action schedule `0 2 * * *` that publishes to `reports/mission_passk.json` + dated snapshot | L1 | C1 + C6 | Action runs green for 3 consecutive nights; `docs/audits/passk_history/` has dated snapshots | Low — extends existing CI |
| 6 | Begin Bengali eval set v1 (L6.1) — draft the 200–500 item spec; collect governed-source candidates from scout corpora | L6 | C3 + C1 | `docs/eval/bengali_eval_v1_spec.md` with item categories, source provenance, and scoring rubric | Low — prep work only |

**Out of scope for this sprint (explicitly):** M2 Context Engine implementation (waits for M3 decision table to settle on the canonical memory read path); M5 Architecture Intelligence (parallel-eligible after M0, but the next sprint is a better slot — this sprint is for closing the most constitutionally offensive defects first); any new OSS dependency; any new subsystem.

---

## 9. Next 90 Days — Quarterly Arc

The 90-day arc below is the planning department's quarterly commitment. It traces directly to the Phase 2 gate (`vision_strategic_positioning.md` §Phase 2): "pass^3 ≥ 0.8 on the mission suite is the promotion bar for every future change."

| Window | Milestone target | Lever(s) closed | Phase gate advanced |
|---|---|---|---|
| **Days 1–30** | Mission suite 5 → 12; nightly pass^k live; Class G defects 7 → 0; M3 decision table merged; first 3 missions engine endpoints wired | L1.1, L1.2, L3, L4.1, L2.1 (partial) | Phase 2 gate pre-conditions; Constitution #13 honest-baseline |
| **Days 31–60** | Mission suite 12 → 20; pass^3 measured and trending; M3 consolidation code-complete (canonical path, archive duplicates with zero-caller proof); M2 Context Engine spec + L0/L1/L2 Alembic revision merged; Bengali eval set v1 frozen | L1.1, L1.2, L4.2, L4.3, L5.1, L5.2, L6.1 | Phase 2 gate within reach; M3 exit criteria; B5 measurement baseline |
| **Days 61–90** | Phase 2 gate fires (pass^3 ≥ 0.8 on 20 missions, 7 consecutive nights); M2 Context Engine measurement harness green (≥ 30% token reduction); orphan spine reduced 57 → ≤ 15; L7 internal scoreboard live; Phase 3 prep complete (adapter base model selected, Kaggle dry-run green) | L1.3, L4.4, L5.3, L5.4, L6.3, L6.4, L7.1, L2.2–L2.4 | **Phase 2 → Phase 3 transition authorized** |

**Kill-criteria check (Day 90):** If pass^3 cannot reach 0.7 on the 20-mission suite by Day 90, the planning department *must* redesign the verify loop before authorizing Phase 3 spend. This is `vision_strategic_positioning.md` §6 made operational. The planning department does not get to overrule the kill criteria — only the founder does, and only with a written rationale appended to this memo's lineage.

**Budget check (Day 90):** The vision document's budget math (Render free/low + Supabase free + Upstash free + Cloudflare free + zero-cost LLM chain + Kaggle ~30h/week + RunPod burst only when gate justifies) targets under ~$75/month. The Day 90 review reconciles actual spend against this target. If actual spend exceeds ~$120/month without a gate-justified reason, the planning department must propose consolidation (not expansion) — Constitution #14 (Sustainable Cost) is operational, not aspirational.

---

## 10. Open Questions for the Founder

The planning department cannot resolve these unilaterally. Each is a Phase 3 gate decision or a Constitution-edge-case judgment that belongs to the founder.

1. **Adapter base model selection (L6.3).** The vision document specifies "an open 2–7B instruct model." The LoRA adapter is base-specific, so the choice is costly to reverse. The planning department recommends the founder shortlist 2–3 candidates by Day 60 so the Day 90 prep is complete. Suggested candidates: Qwen2.5-3B-Instruct (strong multilingual, permissive license), Llama-3.2-3B-Instruct (broad ecosystem), Mistral-7B-Instruct-v0.3 (strong reasoning). The founder's call.
2. **Kill-criteria trigger authority.** If pass^3 stalls below 0.7 on Day 90, who has the authority to (a) authorize a Phase 3 spend despite the kill criteria, or (b) park own-models and double down on B1/B2/B3? The planning department recommends the founder pre-commit to a written decision rule (e.g., "if pass^3 is 0.65–0.70 with a clear upward trend, authorize Phase 3 with a 30-day re-check; if below 0.65, park"). This avoids a biased in-the-moment decision.
3. **Public scoreboard publication threshold.** L7.2 publishes a subset of metrics publicly. The planning department recommends publishing when the internal scoreboard has been stable for 30 days *and* pass^3 ≥ 0.7. The founder may prefer a higher bar (e.g., pass^3 ≥ 0.8) or a lower bar (publish immediately, including regressions, as radical-transparency brand). The founder's call.
4. **M5 Architecture Intelligence timing.** M5 is parallel-eligible with M1–M4 after M0. The planning department deliberately deferred it to Day 60+ because L1–L4 are higher immediate leverage. The founder may disagree if architectural-drift risk is judged more urgent than this memo estimates. Re-open if a cycle is detected in the next 30 days.
5. **HITL scope for autonomous skill creation.** M9 (Governed skill ecosystem) is P3 and not in this memo's 90-day arc. But the HITL engine (already shipped per STATUS.md item 12) currently intercepts `AutoSkillCreator` deployments. The founder should decide whether the planning department should propose M9 prep work in the next memo, or whether M9 waits until Phase 3 adapters have shipped.

---

## 11. Constitution Citation Index

Every Constitution principle cited in this memo, with its authoritative source. Future Head of Planning memos must cite from the same sources so the lineage is consistent.

| Principle | Source | Where cited in this memo |
|---|---|---|
| **#1 Eternal Brain** | `README.md` §SupremeAI Constitution | §4 L4, L6; §6 matrix |
| **#3 Reuse Before Creation** | `README.md` §SupremeAI Constitution; `.github/constitution/rules.yml` architecture.rule_002 | §0, §2, §4 (every lever's "existing assets"), §5.2, §6 matrix |
| **#5 Verification Before Trust** | `README.md` §SupremeAI Constitution; Constitution Core #8 | §0, §1, §4 L1, L3, L7; §6 matrix |
| **#6 Policy Before Power** | `README.md` §SupremeAI Constitution; Constitution Core #6 | §4 L1, L2, L6; §6 matrix |
| **#7 Reversible Evolution** | `README.md` §SupremeAI Constitution | §4 L4 (archive not delete), L6 (rollback warm); §6 matrix |
| **#8 Graceful Degradation** | `README.md` §SupremeAI Constitution | §4 L1, L5, L6; §6 matrix |
| **#9 Provider Agnostic, User Loyal** | `README.md` §SupremeAI Constitution | §4 L6; §6 matrix |
| **#10 One System, Many Execution Surfaces** | `README.md` §SupremeAI Constitution | §4 L1, L2, L5; §6 matrix |
| **#11 Memory Must Compound** | `README.md` §SupremeAI Constitution | §0, §1, §4 L4, L5, L6; §6 matrix |
| **#12 Least Privilege, Maximum Capability** | `README.md` §SupremeAI Constitution | §4 L5, L2; §6 matrix; §5.8 |
| **#13 No Silent Failure** | `README.md` §SupremeAI Constitution; `.github/constitution/rules.yml` reliability.rule_001 (severity BLOCK) | §0, §1, §2, §4 L1, L2, L3, L7; §5.12; §6 matrix |
| **#14 Sustainable Cost** | `README.md` §SupremeAI Constitution; `.github/constitution/rules.yml` cost.rule_001 (severity BLOCK) | §0, §4 L4, L5, L6; §5.5; §6 matrix; §9 budget check |
| **Constitution Core #2 — Build Complete Circles** | `docs/architecture/SUPREMEAI_CORE_CONSTITUTION.md` | §2, §4 L2 |
| **Constitution Core #3 — Reuse Before Creation** | `docs/architecture/SUPREMEAI_CORE_CONSTITUTION.md` | §4 L4 |
| **Constitution Core #5 — Preserve Tenant Ownership** | `docs/architecture/SUPREMEAI_CORE_CONSTITUTION.md` | §4 L5 |
| **Constitution Core #8 — Verify Before Trust** | `docs/architecture/SUPREMEAI_CORE_CONSTITUTION.md` | §4 L1, L3, L7 |
| **Constitution Core #10 — Make Important Behavior Observable** | `docs/architecture/SUPREMEAI_CORE_CONSTITUTION.md` | §4 L2, L7 |
| **AGENTS.md Mandatory Rule #2 — Operational Reality Over Superficial Artifacts** | `AGENTS.md` §MANDATORY SECOND RULE | §0, §1, §4 L2, §5.11 |
| **AGENTS.md Mandatory Rule #6 — Architectural Plans as Protected Living Assets** | `AGENTS.md` §MANDATORY SECOND RULE | §0, §7, §11 |
| **Standing Prohibitions** | `UNIFIED_NEXT_ROADMAP_2026-09-15.md` §5 (10 items) | §5 (restated) |

---

## 12. Closing — The Planning Department's Position

SupremeAI is not behind. M0 and M1 are closed. The capability surface is the largest it has ever been. The Constitution is intact and machine-enforced. The defect register is honest about what remains. The 6 battlefields are clearly chosen. The Phase 0–6 ladder is well-defined. The budget math holds.

What SupremeAI needs now is *not* more plans. It needs *execution discipline on the plans that exist*. This memo therefore does three things and only three things:

1. It names the seven highest-leverage moves (L1–L7) that convert existing capability into measured battlefield wins.
2. It binds every move to the Constitution so that no future iteration can drift into "good idea but unconstitutional" territory.
3. It establishes a continuous planning cadence so that the founder and future Head of Planning iterations have a predictable, auditable lineage of strategic reasoning.

The next memo in this lineage will be `HEAD_OF_PLANNING_WEEKLY_2026-09-23.md` (or sooner if an incident triggers the ad-hoc cadence). It will report progress against §8's 14-day sprint, update the §6 compliance matrix with any new levers proposed, and append — never overwrite — this v1.

> **বাংলা উপসংহার:** SupremeAI-এর পরবর্তী ৯০ দিন স্পষ্ট — প্রথম ৩০ দিনে Class G false-assurance গুলো বন্ধ করা, মিশন সুইট ৫ থেকে ১২ করা, M3 decision table তৈরি করা; পরের ৩০ দিনে মিশন ১২ থেকে ২০, M3 কোড-কমপ্লিট, M2 কন্টেক্স্ট ইঞ্জিন শুরু, বাংলা eval set v1 ফ্রিজ; শেষ ৩০ দিনে Phase 2 gate ফায়ার করা (pass^3 ≥ 0.8), radical transparency dashboard লাইভ করা, Phase 3 prep সম্পূর্ণ করা। প্রতিটি ধাপ আমাদের ১৪-দফা Constitution-এর সাথে সঙ্গতিপূর্ণ — কোনো lever এমন নয় যেটার জন্য নীতি ভাঙতে হবে। এটাই "one of the best AI models" হওয়ার পথ — সিস্টেম হল মডেল, প্যারামিটার নয়।

---

*Memo lineage: v1 (this document, 2026-09-16) — initial strategic posture. Future iterations appended as `HEAD_OF_PLANNING_*.md` siblings, never overwriting this file. Per AGENTS.md Mandatory Rule #6, this memo is a protected living asset.*