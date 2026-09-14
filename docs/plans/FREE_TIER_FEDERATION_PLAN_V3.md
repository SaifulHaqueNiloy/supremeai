# Free-Tier Federation Plan v3 — Reconciled

> This file is retained for historical compatibility. The current consolidated implementation is in `docs/plans/implementation_plan.md` and `docs/plans/FREE_TIER_FEDERATION_MASTER_PLAN_V4.md`.

## Core rule

Federate **capabilities**, not provider quotas.

Use multiple services when they provide legitimate, complementary execution surfaces. Do not rotate accounts or automate around limits merely to simulate a larger quota.

## Flow

```text
Task
 → discover internal capability
 → discover authorized resources
 → discover reusable implementation
 → choose cheapest safe execution surface
 → execute asynchronously when heavy
 → verify
 → remember
```

## Non-negotiable

SupremeAI must continue working when an optional free-tier provider becomes unavailable or changes its limits.
