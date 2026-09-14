# SupremeAI Plan Lifecycle Policy

**Status:** active  
**Source of truth:** `docs/plans/implementation_plan.md`  
**Last verified:** 2026-09-15

## Purpose

Prevent plan sprawl, conflicting execution instructions, stale infrastructure assumptions and undocumented completion claims.

## Required metadata

Every active or proposed plan must contain:

```yaml
id:
title:
status: proposed | active | blocked | complete | historical | superseded
owner_circle:
scope:
depends_on:
implements:
supersedes:
superseded_by:
source_of_truth: true | false
last_verified:
code_evidence:
test_evidence:
```

## Source-of-truth hierarchy

```text
Current tested code
→ API/schema contracts
→ docs/plans/implementation_plan.md
→ canonical architecture documents
→ specialized active plans
→ historical/reference plans
```

If a plan conflicts with tested code or an authoritative contract, the plan is stale until reconciled.

## Status rules

- **proposed:** idea not approved for implementation.
- **active:** approved and currently executable.
- **blocked:** approved but blocked by a named dependency or decision.
- **complete:** code, caller, tests, deployment evidence, observability and rollback/recovery evidence exist.
- **historical:** records a previous state or execution model; do not implement literally.
- **superseded:** replaced by a newer canonical plan.

## Reconciliation rules

1. Search for an existing equivalent before adding a plan.
2. Every overlapping plan must name its canonical replacement.
3. Never delete protected architecture history during the first reconciliation pass.
4. Prefer redirect/index metadata before physical moves.
5. Do not mark infrastructure as missing without current code evidence.
6. Do not treat examples, targets or aspirations as implemented capabilities.
7. Plans must define acceptance criteria and evidence requirements.
8. New plans must be reconciled into `implementation_plan.md`.

## Completion rule

A document existing in the repository is not completion evidence. Completion requires traceable implementation and verification.
