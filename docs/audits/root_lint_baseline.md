# Root-Level Lint Baseline (Owner Audit P1 #6 — Escalation Ladder)

**Date:** 2026-09-15 · **Tree:** main @ 7979586e (M0-E) · **Ruff:** 0.16.4 · **Scope:** `tools/ scripts/ packages/ .github/scripts/` (410 py files)

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

## Batch 1 result (2026-09-15, this PR)

`ruff check --select W291,W292,W293 --fix` (safe fixes only) resolved
**1,583** violations across 56 files → remaining **254** = 160 F-class +
94 W-class string-interior cases (whitespace INSIDE docstrings/prompts —
left for manual review; auto-fixing would mutate string content, incl.
possible LLM prompts and printed output). Ladder now: 1,837 → 254 (−86%).

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
