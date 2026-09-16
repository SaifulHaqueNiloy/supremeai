# PR Guardian — Improvement-Only Merge Automation (Design Draft)

**Purpose**: Define how an MCP-connected guardian can review open GitHub PRs, decide “improvement vs regression,” and act accordingly — merge if improvement with no regression, otherwise close PR or fix regression before merge.

**Status**: Working draft for alignment with the repository governance model and SupremeAI principles.
**Scope**: This is an implementation/planning proposal for the SupremeAI PR automation workflow. It is not yet a committed plan.

---

## 1. Core Decision Principle

CI status should not be the primary gating signal.

Instead, the guardian should answer one question:

> Does this PR move the codebase toward a clearly better state with no meaningful regression?

That means:

- Improvement evidence must be explicit and reviewable.
- A PR must not merge simply because tests pass if it introduces a harmful change elsewhere.
- A PR must not be closed simply because some regression is detected — first decide whether the regression is fixable and worth preserving the improvement.

---

## 2. What “Improvement” Should Mean

Improvement should be defined in concrete, verifiable terms rather than vague feel.

A PR is more likely an improvement if it:

- Fixes a real bug, incorrect behavior, security weakness, or production problem.
- Reduces complexity, duplication, or maintenance risk without breaking existing behavior.
- Improves performance, reliability, observability, or developer workflow in a measurable way.
- Aligns the codebase with documented architecture, conventions, or best practices.
- Adds missing capability that is intentionally on the roadmap.

A PR should not be treated as an improvement if:

- It is purely cosmetic and introduces risk or inconsistency.
- It changes behavior without clear benefit or justification.
- It breaks contract, test, or runtime expectations without a compensating gain.
- It silences warnings/errors by removing important checks rather than fixing root causes.

---

## 3. What “Regression” Should Mean

Regression should be treated broadly, not only as failing CI.

Common regression signals include:

- Broken API contracts, route shapes, or frontend/backend mismatches.
- Broken tests, compilation failures, or runtime errors.
- Loss of existing functionality that was previously working.
- Reduced reliability, security, tenant isolation, or authorization safety.
- Performance degradation or operational fragility.
- Removed safeguards, validation, or error handling that were doing real work.

Important nuance:

- A regression may exist even if one CI job is green.
- A green CI run is not proof of safety; it is only one evidence source.

---

## 4. Decision Flow

Suggested decision flow for each PR:

1. **Discover**
   - List open PRs against `main`.
   - Fetch title, description, commits, changed files, diff, review/comment state, linked issues, and any existing evidence artifacts.

2. **Classify intent**
   - Determine whether the PR is a bug fix, feature, refactor, docs, or mixed.
   - Read the stated goal and compare it to the actual changes.

3. **Score improvement evidence**
   - Does the PR solve a concrete problem?
   - Is the benefit real, not hypothetical?
   - Is the change consistent with the codebase’s architecture?
   - Is the scope justified?

4. **Scan for regression**
   - Compile/test/runtime health.
   - Contract preservation.
   - Existing behavior preservation.
   - Security/authorization/tenant boundaries.
   - Operational risk and observability.

5. **Decide**
   - **Improvement + no regression** → eligible for merge.
   - **Improvement + fixable regression** → fix regression, re-validate, then merge.
   - **Improvement + severe/unfixable regression** → do not merge; recommend close or redesign.
   - **No improvement, or unclear benefit** → do not merge; recommend close or revise.

6. **Act**
   - Only take automated merge/close action when the decision is strong and evidenced.
   - When decision is borderline or consequential, escalate to human review instead of guessing.

---

## 5. Merge vs Close vs Fix Logic

### 5.1 Merge
Merge only when:

- There is clear improvement evidence.
- No significant regression is present.
- Any remaining questions are low-risk and reversible.

### 5.2 Fix Regressions
If regression is present but fixable:

- Prefer fixing the regression on the PR branch.
- Keep the improvement.
- Re-validate the result.
- Then consider merge.

This is usually better than closing a valuable PR solely because of a fixable regression.

### 5.3 Close PR
Close when:

- The PR introduces no clear improvement.
- The change is harmful, too risky, or not aligned with project direction.
- The regression is severe and cannot be cleanly fixed.
- The PR is abandoned, duplicated, or clearly outdated.

If unsure, escalate instead of closing a possibly valuable PR.

---

## 6. Severity and Risk Tiering

Not all PRs deserve the same judgment depth.

Low-risk:
- docs, formatting, small refactors with clear behavior preservation, minor config changes
- may be eligible for automated merge if improvement is obvious and safe.

Medium-risk:
- behavior changes, routing or policy tweaks, refactors touching shared modules
- need stronger evidence and possible staged/partial merge or human visibility.

High-risk:
- auth, security, tenant/RBAC, billing, infra, public API contracts, migrations
- should not be auto-merged without explicit evidence and governance approval.

---

## 7. Evidence Needs Before Automation

Automation should not be based on vibes.

For automated merge eligibility, the guardian should ideally have:

- PR description or linked issue explaining the problem.
- Clear diff showing what changed and why.
- Local or CI evidence relevant to the change type.
- Sign that the change does not break important contracts or existing behavior.
- Confidence that the change is net-positive.

If evidence is weak, automation should pause and request human review.

---

## 8. Interaction with Existing Governance

This PR guardian should respect:

- **Safety first**: Never auto-merge if there is any reasonable chance of security, auth, tenant, or data-integrity harm.
- **Evidence before merge**: Merge because improvement is demonstrated, not because CI is green.
- **Reversibility**: Prefer changes that are easy to revert or rollback; if a PR is high-risk, require stronger evidence.
- **Human escalation**: For consequential conflicts, uncertainty, or rule precedence issues, escalate rather than decide alone.
- **No silent destructive action**: Do not close or merge consequential PRs without a clear, recorded rationale.

---

## 9. Suggested MCP Tool Surface

A PR guardian MCP server could expose tools such as:

- `list_open_prs`
- `get_pr_details`
- `get_pr_diff`
- `get_pr_review_comments`
- `evaluate_pr_improvement`
- `detect_regression_signals`
- `merge_pr`
- `close_pr`
- `request_human_review`

Each tool should return structured output with verdict, confidence, evidence summary, and recommended action.

---

## 10. Suggested Implementation Plan

1. Start with read-only PR analysis.
2. Build a reusable improvement/regression rubric.
3. Add structured verdict output with evidence and confidence.
4. Add human review escalation paths before any write action.
5. Add safe auto-merge for low-risk, high-confidence improvement PRs.
6. Add regression-fix workflow for medium-risk PRs where fix is straightforward.
7. Reserve close/merge of high-risk PRs for explicit human approval.

---

## 11. Uncertainties and Open Questions

- PR volume and review load: how many PRs and how often?
- Which GitHub token/permissions are available for merge/close actions?
- Whether merge should be automatic by the guardian or only after human approval on the GitHub side.
- How regression evidence should be collected reliably across frontend, backend, and infra.
- Whether improvement judgment should be rule-based, LLM-assisted, or hybrid.

---

## 12. Summary

The right model is not “CI green → merge.”

A better model is:

- Read the PR.
- Judge whether it is a genuine improvement.
- Check whether it causes regression.
- If yes to improvement and no to regression → merge.
- If improvement yes and regression fixable → fix then merge.
- If regression severe or benefit absent → close or escalate.

This keeps automation useful without turning it into a blind merger.
