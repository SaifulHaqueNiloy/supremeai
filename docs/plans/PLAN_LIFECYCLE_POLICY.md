# SupremeAI Plan Lifecycle Policy

> Status: active
> Owner: Architecture Governance
> Last verified: 2026-09-15

## Purpose

This policy keeps `docs/plans` as a protected living architecture record while establishing one evidence-based source of truth for implementation decisions.

## Required metadata

Every active or newly edited plan must declare:

```yaml
status: proposed | active | blocked | complete | historical | superseded
owner_circle: <responsible domain>
scope: <capability or system boundary>
source_of_truth: true | false
last_verified: YYYY-MM-DD
supersedes: []
superseded_by: []
code_evidence: []
test_evidence: []
```

## Status rules

- `proposed`: approved idea without implementation evidence.
- `active`: current plan with an owner and next executable work.
- `blocked`: active work prevented by a named dependency or decision.
- `complete`: implementation, tests, runtime evidence, and rollback/recovery evidence exist.
- `historical`: preserved record that is not an active execution source.
- `superseded`: retained plan replaced by a named canonical plan.

## Source-of-truth hierarchy

1. Tested current code and deployed contracts.
2. API, database, security, and deployment contracts.
3. `docs/plans/implementation_plan.md`.
4. A canonical domain plan listed in `phases/plan_reconciliation_register.md`.
5. Specialized active plans.
6. Historical and superseded plans.

When two plans conflict, the higher item wins and the conflict must be recorded in the reconciliation register.

## Completion evidence

A plan may not be marked complete from documentation alone. It must link to the implementation path, callers, tests, deployment/runtime evidence, observability, and rollback or recovery behavior where applicable.

## First-pass organization rules

- Do not delete protected architecture history.
- Do not mass-rename or mass-move files before links and content are reconciled.
- Use `superseded_by` and the reconciliation register before any later archive move.
- Keep experimental, provider-specific, and historical plans explicitly labeled.
- Review active plans at every release boundary.

## Review cadence

Architecture Governance should review this catalog whenever a major module, provider, data contract, or release gate changes.

## Related documents

- [Implementation plan](./implementation_plan.md)
- [Plan-to-code traceability matrix](./PLAN_TO_CODE_TRACEABILITY_MATRIX.md)
- [Plan reconciliation register](./phases/plan_reconciliation_register.md)
- [Catalog](./README.md)
