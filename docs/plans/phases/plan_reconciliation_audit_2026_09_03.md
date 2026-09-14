# SupremeAI Plan Reconciliation — 2026-09-03

## Why this exists

The repository contains several generations of implementation plans. They contain valuable architecture, but some older assumptions conflict with the current direction and must not be implemented literally.

This document is the reconciliation layer for those plans.

## Reviewed plan families

### 1. Bootstrap Brain / Decision Logic

- `docs/ADMIN_TASKS/SUPREMEAI_BOOTSTRAP_BRAIN_AND_DECISION_LOGIC_PLAN.md`
- `docs/ADMIN_TASKS/implementation_plan.md`

**Status:** Current direction is discovery-first.

Required behavior:

```text
intent
→ capability discovery
→ reusable implementation discovery
→ resource/authorization discovery
→ cost/risk/quality evaluation
→ methodology decision
```

`discover_reusable_implementation` is logically available for every `dev` task. Expensive external discovery is tier-gated rather than unconditional.

`generate_new_code` is a fallback.

### 2. Free-tier federation

- `docs/plans/FREE_TIER_FEDERATION_MASTER_PLAN_V4.md`
- `docs/plans/FREE_TIER_FEDERATION_PLAN_V3.md`
- `docs/plans/FREE_TIER_UPGRADE_PLAN.md`

**Status:** Federation remains valid, but it means **capability federation**, not quota circumvention.

The following are not approved production architecture:

- account multiplication solely to multiply provider quotas
- stealth keep-alives
- fake human interaction
- CAPTCHA/anti-abuse circumvention
- hidden permanent notebook workers

Use services according to their legitimate workload model and provider policy.

### 3. Missing services

- `docs/plans/MISSING_SERVICES_INTEGRATION_PLAN_V4.1.md`

**Status:** Historical service inventory; implement only after current-code verification.

A service marked “missing” in an old plan must first be checked against the current repository. Existing equivalent implementations should be reused rather than duplicated.

The plan's old multi-account/Kaggle federation assumptions are not a production guarantee.

### 4. Production upgrade

- `docs/plans/PRODUCTION_UPGRADE_PLAN.md`
- `docs/PRODUCTION_READINESS_PLAN_V3.md`

**Status:** Keep reliability/security work; defer heavyweight infrastructure until measured bottlenecks justify it.

Enterprise targets such as 99.99% uptime are targets, not present guarantees.

### 5. Storage / memory

- `docs/FREE_TIER_STORAGE_PLAN.md`

**Status:** Align with the current Eternal Brain direction.

Prefer durable high-value knowledge, compact metadata, retention, archival, deduplication, and reuse. Do not turn the database into an unbounded raw-artifact store.

## Current implementation hierarchy

When plans disagree, use this order:

```text
1. Current production code + tests
2. Current security/policy constraints
3. docs/plans/implementation_plan.md
4. current Admin Brain implementation plan
5. newer specialized plans
6. older historical plans
```

If a plan conflicts with current code, do not blindly implement the plan. Re-audit the code and update the master plan.

## Current SupremeAI decision principle

```text
Do not build what already exists.
Do not discover externally when trusted internal knowledge is sufficient.
Do not execute expensive work when it can be reused or cached.
Do not delegate without authorization.
Do not trust generated code without verification.
Do not make an optional provider a correctness dependency.
```

## Required next reconciliation work

1. Audit the actual `multi_account_rotator` / provider-pool implementations against the new federation policy.
2. Verify current Kaggle/Colab execution paths before enabling them in production.
3. Verify current Render architecture before applying old “single service” assumptions.
4. Verify current Supabase/pgvector implementation before adding migrations described as “missing.”
5. Add automated plan/code drift checks so stale plans are flagged before implementation.

## Canonical planning entry point

`docs/plans/implementation_plan.md`

This file should remain concise and point to specialized plans rather than allowing multiple plans to silently become competing sources of truth.
