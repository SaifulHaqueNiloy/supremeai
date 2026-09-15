# Root-Level Lint Baseline (Owner Audit P1 #6 — Escalation Ladder)

**Date:** 2026-09-15 · **Tree:** main @ 7979586e (M0-E); batch 2 measured @ 8f162480 · **Ruff:** 0.16.4 · **Scope:** `tools/ scripts/ packages/ .github/scripts/` (410 py files)

## Why this file exists

The Operational Tooling Quality Gate already enforces a **fatal-only** rule set
(`--select E9,F821,F822,F823`) on all four root directories — that gate is
clean (0 violations). Owner audit P1 #6 asks for wider root-level lint
coverage. Auto-promoting the full rule set would immediately red CI on
2,118 pre-existing violations, so this baseline + a **non-blocking CI report
step** establish the measurement ladder instead: batch-fix per rule class →
watch the CI report trend → flip rule classes to blocking when a class hits 0.

## Current state (measured)

| Rule class | Meaning | Count | Auto-fixable |
|---|---|---|---|
| E9,F821,F822,F823 | fatal: syntax/undefined names | **0** | — (already blocking in CI) |
| F401 | unused-import | 85 | ⚠️ technically, but **FORBIDDEN as auto-fix** (see below) |
| F541 | f-string without placeholders | 47 | yes (`[*]`) |
| F841 | unused-variable | 23 | no (`[-]`) |
| F811 | redefined-while-unused | 4 | no |
| F402 | import-shadowed-by-loop-var | 1 | no — **highest real-bug risk of the class** |
| W293 | blank-line-with-whitespace | 1,591 | 1,583 safe-fix; 94 string-interior cases need manual review |
| W291 | trailing-whitespace | 74 | most safe-fix; remainder string-interior |
| W292 | missing-newline-at-EOF | 12 | yes |
| **Total (E9,F,W)** | | **1,837** | |

(For reference, the default ruff rule set across the four dirs totals 2,118 —
that broader number is NOT this ladder's baseline; the ladder tracks E9,F,W.)

## Batch 1 result (2026-09-15, PR #334)

`ruff check --select W291,W292,W293 --fix` (safe fixes only) resolved
**1,583** violations across 56 files → remaining **254** = 160 F-class +
94 W-class string-interior cases (whitespace INSIDE docstrings/prompts —
left for manual review; auto-fixing would mutate string content, incl.
possible LLM prompts and printed output). Ladder now: 1,837 → 254 (−86%).

## Batch 2 result (2026-09-15, this PR)

**REL-001 (silent failure) — 9 of the 24 repo-wide sites fixed in scripts/ tooling.**
Each bare `except: pass` now logs a contextual stderr warning (or appends to
discovery notes in `lib/auto_discovery.py`, matching file convention); behavior
is unchanged — handlers still fall through to the same defaults, they are just
no longer silent:

| File | Site | Handler now does |
|---|---|---|
| scripts/generate_module_docs.py | ×2 | stderr `[module-docs]` read-failure w/ path + exc |
| scripts/ci/generate_module_capability_matrix.py | ×1 | stderr audit-summary-unreadable w/ path + exc |
| scripts/ci/check_truthy_env_var.py | ×1 | stderr SyntaxError-skipped w/ file + exc |
| scripts/health/superai_health_check.py | ×1 | stderr discovery-failed → legacy fallback notice |
| scripts/audit_isolated_modules_and_capabilities.py | ×2 | stderr config/file skipped w/ path + exc |
| scripts/lib/auto_discovery.py | ×1 | `disc.notes.append("render.yaml unreadable: …")` |
| scripts/ci/mission_passk.py | ×1 | stderr junit-unparseable (file + exc) |

**Deferred (2 sites, owner call):** `pre_merge_guard.py:707` and
`secret_rotation_reminder.py:282` REL-001 fixes were prepared but withheld —
both files carry pre-existing ARCH-001 blocking findings that the audit ratchet
would pull into PR scope, and review showed them to be **scanner false-positives**
(`"localhost" not in o` is a defensive filter that EXCLUDES localhost origins;
the "Windows-path" hits are `name:\s` regexes whose `e:\s` substring matches the
scanner's `[eE]:\\` drive-pattern — not paths). Owner call: either adjust the
scanner heuristic or accept per-file exemptions (the exemption YAML loader
exists in models.py but is not wired into `run_audit`).

Also completed in this PR: **re-delivery of batch 1's whitespace batch**
(1,421 W-class fixes across 55 files). The original batch-1 whitespace commit
was not included when #334 re-applied the hardening branch to main (only
ci.yml + test_ws_auth.py + this baseline doc landed), so main still carried
1,677 W-class violations; this PR re-runs the identical
`ruff check … --select W291,W292,W293 --fix` on `tools/ scripts/ packages/
.github/scripts/`. 93 string-interior cases remain excluded by the same
design rule as batch 1 (auto-fix would mutate string content).

**Ladder after batch 2 (E9,F,W scope, measured): 1,837 → 372 (−80%).**
Remaining 372 = 160 F-class (F401 85 · F541 47 · F841 23 · F811 4 · F402 1)
+ 212 W-class (string-interior cases + the withheld whitespace of the three
owner-call quarantined files).

Remaining REL-001 sites: **13 in backend/** + the 2 deferred scripts sites
(production/runtime paths — per-module logger-convention review; separate batch).
Still owner-call quarantined (whitespace fixes withheld there until resolved):
`scripts/db/auto_seed.py` (SEC-003:49), `scripts/devops/config/validators.py`
(ARCH-001:413), `tools/knowledge/card_builder.py` (ARCH-001 ×9 docstring
misfires).

## Audit-ratchet quarantine (batch 1 scope adjustment)

CI's Constitution Audit runs `--pr-diff` — touching a file with pre-existing
blocking findings (even whitespace-only) pulls those findings into the PR's
audit scope. 8 files carried 18 pre-existing blocking findings
(REL-001 except:pass × 7, ARCH-001 × 10, SEC-003 × 1) and are therefore
**quarantined out of batch 1**; their whitespace fixes land together with the
actual violation fixes (batch 2). Quarantined: validators.py, card_builder.py,
audit_isolated_modules_and_capabilities.py, check_truthy_env_var.py,
generate_module_capability_matrix.py, generate_module_docs.py,
superai_health_check.py, auto_seed.py.

Per-directory F-rule counts: `tools/` 9 · `scripts/` 145 · `packages/` 0 · `.github/scripts/` 6.

## Suggested fix order (smallest safe batches first)

1. **W292+W291+W293 (1,677)** — pure whitespace, zero semantic risk,
   `ruff format` on the four dirs handles them mechanically. Largest single
   count reduction per unit of review effort.
2. **F541 (47)** — `[*]` auto-fixable, no behavior change.
3. **F402 (1)** — single case; manual review, possible latent bug, worth its own commit.
4. **F811 (4)** — manual review each (redefinition may be intentional override).
5. **F841 (23)** — manual review; unused variable may indicate a dropped call chain.
6. **F401 (85) LAST and NEVER via `--fix`** — see warning below.

## ⚠️ Why F401 must not be auto-fixed here

This codebase has **import side effects**: importing certain modules performs
registration onto singletons (e.g. browser-package registration onto the app
engine, plugin registration, Alembic target-metadata population). An
"unused" import may be the only thing keeping a registration alive. Every
F401 in the root dirs must be reviewed individually, ideally with the
module's import graph, before removal — the same class of issue as the
AUDIT-FF silent-unmount incidents. When this class is eventually fixed,
the diff should state per-file why each removed import is provably
side-effect-free.

## Escalation to blocking (definition of done)

A rule class may move into the blocking `ruff check` invocation of the
Operational Tooling Quality Gate when its count reaches **0 and stays 0 for
two consecutive CI weeks**. Proposed final blocking set:
`E9,F821,F822,F823,F401,F402,F541,F811,F841,W291,W292,W293`.

## CI wiring (this PR)

`ci.yml` → `tooling-quality` job gains two strictly-additive steps:
1. **Root-level lint drift report (non-blocking)** — `continue-on-error: true`,
   runs `--select E9,F,W --statistics`, prints `ROOT_LINT_TOTAL` to the log.
2. **Upload root lint report** — artifact `root-lint-report-<sha>`, retained 30 days.

The blocking gate lines are untouched; the job cannot go red from this report.
