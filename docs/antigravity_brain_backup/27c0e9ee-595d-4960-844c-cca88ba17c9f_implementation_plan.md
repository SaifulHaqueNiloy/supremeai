# Phase 4: Zero-Admin Maintenance Automation

The user has provided a brilliant roadmap for minimizing administrative overhead by turning SupremeAI into a self-healing and self-improving system. We will implement these requested automations into the GitHub Actions pipeline.

## User Review Required

> [!CAUTION]
> `MonkeyType` requires running the code to trace runtime types. Simply running it statically won't generate type hints. I propose we integrate it with `pytest` (e.g., `monkeytype run -m pytest`) so it observes types during tests, then applies them using `monkeytype apply`. Do you agree?

> [!WARNING]
> Automatically updating `requirements.txt` via `pip-audit` or `pip-tools` might introduce breaking changes from major version bumps. We will create PRs instead of merging directly, so you always have the final say.

## Proposed Changes

### [MODIFY] [maintenance_pipeline.yml](file:///c:/Users/n/supremeai/supremeai_2.0/maintenance_pipeline.yml)
We will expand the existing manual pipeline to include the new tasks. 

#### Fix Syntax Errors
- Fix the duplicated keys and commands accidentally added by the user's manual copy-paste (e.g., duplicate `commit-message`, duplicate `run: pip install ...`).

#### New Job 1: `auto-deps-update`
- Triggers when `github.event.inputs.task == 'auto-deps-update'`
- Runs `pip-audit` to find vulnerable packages.
- Uses a quick script or `pip-tools` to bump the specific vulnerable packages in `requirements.txt`.
- Uses `create-pull-request` to create a PR for the updates.

#### New Job 2: `dead-code-removal`
- Triggers when `github.event.inputs.task == 'dead-code-removal'`
- Runs `vulture . --min-confidence 80` and outputs to a report.
- Runs `ruff check --select F401,F841 --fix .` to aggressively remove unused imports and unused variables.
- Uses `create-pull-request` to push the changes.

#### New Job 3: `auto-docs-and-types`
- Triggers when `github.event.inputs.task == 'auto-docs-and-types'`
- Installs `docformatter` and `monkeytype`.
- Runs `docformatter --in-place --recursive .`.
- Uses `create-pull-request` to push formatted docstrings.

#### [NEW] [scripts/maintenance/create_issue.py](file:///c:/Users/n/supremeai/supremeai_2.0/scripts/maintenance/create_issue.py)
- A simple script that parses the `pip-audit --format=json` output and uses the GitHub REST API (via `GITHUB_TOKEN`) to create an Issue if critical vulnerabilities are found that can't be easily auto-remediated.

## Verification Plan

### Automated Tests
- Run `yamllint` or similar check locally to ensure `maintenance_pipeline.yml` is perfectly valid.
- We will test the syntax locally using `ruff check` and `python` to verify python scripts.

### Manual Verification
- You can manually trigger each workflow in the "Actions" tab on GitHub to verify they successfully create PRs and Issues.
