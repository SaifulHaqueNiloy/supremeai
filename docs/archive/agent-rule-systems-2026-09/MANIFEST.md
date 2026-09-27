# Archive Manifest — Legacy Agent Rule Systems (batch: 2026-09)

> Issue #2251 — feat(governance): [Phase-5] generate rules.yml & enforce automated
> system gates (AGENTS.md v2). Full-Freedom Constitution ("Kite & Spool") flip:
> prose → machine-enforced gates.

## What was archived and why

| Original path | Archived as | Why retired |
| :--- | :--- | :--- |
| `.clinerules/` (master_prompt.md + workflows/speckit-*.md) | `.clinerules/` | Legacy IDE prompt system. The speckit workflow files duplicate the ones under `.specify/`; `master_prompt.md` prose rules are superseded by the machine-readable registry. |
| `.lingma/rules/agents.md` | `.lingma/` | Single-file duplicate of `AGENTS.md` for the Lingma IDE — two copies of the constitution always drift. |
| `.agents/rules/*.md` (4 files) | `agents-rules/` | Legacy agent rule prose (guardian/auditing/discipline). Superseded by automated gates + AGENTS.md v2. |

## Where the rules live now (single source of truth)

1. **`.github/constitution/rules.yml`** — machine-readable rule registry:
   23 constitutional audit rules (unchanged, canonical) + gate registry
   (lease / verification / scope / collision / self-merge / test-guard /
   post-merge) + scope/verification/lease policies + the 3 hard rules.
2. **`AGENTS.md`** — now **GENERATED** from rules.yml by
   `scripts/ci/generate_agents_md.py` (CI drift check: `system-gates.yml → agents-md-sync`).
3. **Automated enforcement**: `.github/workflows/system-gates.yml` runs the
   Verification / Lease / Scope gates via `.github/scripts/constitution/gates.py`.
   Cross-PR collision stays in `pr-gate.yml` (check-collisions, strict mode).

## Retrieval

Everything here is frozen history — do not edit. If a rule from these files is
still needed, re-registered it in `.github/constitution/rules.yml` through the
normal 1-issue-1-branch-1-PR flow.
