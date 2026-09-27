# SupremeAI — Agent Violation Matrix (Living Document)

> **Source:** Exhaustive auditor analysis ([#2004](https://github.com/SaifulHaqueNiloy/supremeai/issues/2004))
> **Last updated:** 2026-09-27
> **Maintained by:** Planner lane (auditor duty, Charter Rule #22)

This is a **living document** — new violation vectors are added as discovered.
Closed vectors are marked `✅ closed by rule #N + issue #M`.

---

## How to read this matrix

Each row represents a way an agent can violate a rule. The matrix walks every
lifecycle stage:

```
CLAIM → BRANCH → WORK → VERIFY → PUSH → PR → MERGE → POST-MERGE → NEXT
```

---

## STAGE 1: CLAIM

| # | Violation | How | Enforcement | Status |
|---|---|---|---|---|
| 1.1 | Agent claims without reading rules | Agent skips reading AGENTS.md | None | ❌ Open — Rule #23 tracks rules_version |
| 1.2 | Agent claims wrong-lane issue | Coder claims CI-lane issue | `next_claimable.sh <lane>` filters | ⚠️ Advisory — no PR-level check |
| 1.3 | Agent skips priority | Claims P3 when P0 exists | `next_claimable.sh` shows priority | ❌ Open — no mechanical prevention |
| 1.4 | Double-claim (TOCTOU) | Two agents claim same issue | `atomic_claim.sh` CAS (but --skip-assign not merged) | 🔴 #1989 |
| 1.5 | Stale claim | Agent claims, goes offline | `stale-mutex-cleanup.yml` (24h) | 🟠 #1996 |
| 1.6 | Claim without file declaration | Agent doesn't declare files | ✅ Rule #20 added (#2009) | 🟠 #2001 (enforcement) |
| 1.7 | Agent reads outdated rules | Rules changed since last read | ✅ Rule #23 added (#2009) | 🟠 #2000 (enforcement) |

## STAGE 2: BRANCH

| # | Violation | How | Enforcement | Status |
|---|---|---|---|---|
| 2.1 | Wrong branch name | Uses `feature/foo` | `branch-naming-guard.yml` | ⚠️ Advisory — also accepts `feat/foo` |
| 2.2 | Branch not from latest main | 50 commits behind | `auto-update-pr-drift.yml` (reactive) | ❌ #1999 |
| 2.3 | Branch slot collision | Two agents use same slot | `acquire_role_slot.py` (non-atomic) | 🔴 #1990 |
| 2.4 | Force-push to overwrite | `git push --force` after review | ✅ Rule #15 added (#2009) | 🟠 #2007 (enforcement) |
| 2.5 | Branch from wrong base | Branches from another agent's branch | ✅ Rule #14 added (#2009) | ❌ Open (no CI check yet) |

## STAGE 3: WORK

| # | Violation | How | Enforcement | Status |
|---|---|---|---|---|
| 3.1 | Scope creep | Coder modifies `.github/workflows/` | `pr-pipeline.yml` scope classify (advisory) | ❌ #1995 |
| 3.2 | Drive-by fix | Agent fixes unrelated bug | Charter rule #4/#5 | ❌ No automated detection |
| 3.3 | Bundle multiple issues | `Closes #123 #456` | None | 🟠 #2006 |
| 3.4 | Copy-paste from unmerged branch | Agent copies code from another PR | None | ❌ Open |
| 3.5 | Delete tests to pass CI | Agent removes failing tests | ✅ Rule #21 added (#2009) + `learning_guards.py` (exit 0) | 🔴 #1992 |
| 3.6 | Disable security checks | Agent comments out auth check | ✅ Rule #21 + `learning_guards.py` (exit 0) | 🔴 #1992 |
| 3.7 | Mock/stub to fake green | Agent replaces real impl with mock | ✅ Rule #21 added (#2009) | ❌ No automated detection |
| 3.8 | Multiple issues simultaneously | Agent has 2 claims at once | ✅ Rule #13 added (#2009) | 🟠 #2008 (enforcement) |

## STAGE 4: VERIFY

| # | Violation | How | Enforcement | Status |
|---|---|---|---|---|
| 4.1 | Skip pre-push hook | `git push --no-verify` | Local bash hook only | 🔴 #1993 |
| 4.2 | Skip tests | `pytest --skip` | ✅ Rule #21 + `learning_guards.py` (exit 0) | 🔴 #1992 |
| 4.3 | Lower coverage threshold | Edit `MIN_BACKEND_COVERAGE=30` → `10` | ✅ Rule #21 added (#2009) | ❌ No protection on ci.yml |
| 4.4 | Fake verification output | `echo "PASS"` instead of real check | None | ❌ Open |
| 4.5 | Wrong environment for tests | Missing deps (passes trivially) | None | ❌ Open |

## STAGE 5: PUSH

| # | Violation | How | Enforcement | Status |
|---|---|---|---|---|
| 5.1 | Push to main directly | `git push origin main` | Local hook only | 🔴 #1993 |
| 5.2 | Push to another agent's branch | `git push origin coder-2` | ✅ Rule #18 added (#2009) | ❌ No CI check yet |
| 5.3 | Push without sync | Branch is stale | `auto-update-pr-drift.yml` (reactive) | ❌ #1999 |
| 5.4 | Push secrets | `.env` committed | `gitleaks` in CI | ✅ Enforced |
| 5.5 | Force-push | `git push --force` | ✅ Rule #15 added (#2009) | 🟠 #2007 |
| 5.6 | Push large binary | >10MB file | None | ❌ Open |

## STAGE 6: PR

| # | Violation | How | Enforcement | Status |
|---|---|---|---|---|
| 6.1 | PR without issue reference | `feat: add thing` | `ISSUE_LINKED_B` (not in BLOCK_COUNT) | 🔴 #1991 |
| 6.2 | PR references wrong issue | `(#123)` but PR is about #456 | None | ❌ Open |
| 6.3 | PR title format wrong | `fixed bug` | ✅ Rule #16 added (#2009) | ❌ No CI check yet |
| 6.4 | PR has 0 reviewers | No review requested | None | 🟠 #2005 |
| 6.5 | PR description empty | No description | ✅ Rule #17 added (#2009) | ❌ No CI check yet |
| 6.6 | Multiple issues in one PR | `Closes #123, #456` | None | 🟠 #2006 |

## STAGE 7: MERGE

| # | Violation | How | Enforcement | Status |
|---|---|---|---|---|
| 7.1 | Merge with failing CI | Admin force-merges | Branch protection (not set up) | 🔴 #1993 |
| 7.2 | Merge out of order | Low-priority before P0 | None | ❌ Open |
| 7.3 | Merge batch member individually | Agent merges PR in rollup batch | Charter §3.6 | ❌ No enforcement |
| 7.4 | Self-merge | Agent approves + merges own PR | ✅ Rule #12 added (#2009) | 🟠 #2005 (enforcement) |

## STAGE 8: POST-MERGE

| # | Violation | How | Enforcement | Status |
|---|---|---|---|---|
| 8.1 | Regression on main | Merged PR breaks main | CI on main push (reactive) | ✅ Rule #22 added (#2009) — enforcement pending |
| 8.2 | Rules changed without audit | Admin edits AGENTS.md | None | 🟠 #2000 |
| 8.3 | LESSONS_LEARNED not updated | Agent doesn't log mistake | Charter rule #8 | ❌ No automated check |
| 8.4 | Discovery issue not created | Agent finds bug, doesn't file | Charter rule #11 | ❌ No enforcement |
| 8.5 | Stale lock not released | `status:in-progress` stays | `stale-mutex-cleanup.yml` (24h) | 🟠 #1996 |

## STAGE 9: NEXT (loop continuation)

| # | Violation | How | Enforcement | Status |
|---|---|---|---|---|
| 9.1 | Agent goes idle | PR merges, agent doesn't claim | None | ❌ Open |
| 9.2 | Agent claims same issue again | PR merged but agent re-claims | None | ❌ Open |
| 9.3 | Agent skips MCP Tower heartbeat | Agent doesn't connect | ✅ Rule #19 added (#2009) | ❌ Enforcement pending |

---

## Summary

| Stage | Total | ✅ Rule added | 🔴 Enforcement issue | ❌ Open (no rule/enforcement) |
|---|:---:|:---:|:---:|:---:|
| CLAIM | 7 | 2 | 2 | 3 |
| BRANCH | 5 | 2 | 2 | 1 |
| WORK | 8 | 3 | 3 | 2 |
| VERIFY | 5 | 2 | 1 | 2 |
| PUSH | 6 | 2 | 2 | 2 |
| PR | 6 | 3 | 2 | 1 |
| MERGE | 4 | 1 | 1 | 2 |
| POST-MERGE | 5 | 1 | 2 | 2 |
| NEXT | 3 | 1 | 0 | 2 |
| **Total** | **49** | **17** | **15** | **17** |

**Progress:** 17/49 vectors have a rule added (#2009). 15/49 have enforcement issues open. 17/49 still need rules or enforcement.
