# Extract Scheduled Jobs to Dedicated Workflow

The goal is to move the heavy `prompt-eval` job and all maintenance tasks out of the main CI pipeline (`supreme-ci.yml`) into a dedicated scheduled workflow (`scheduled-maintenance.yml`). This speeds up regular code pushes and saves API costs, while ensuring maintenance runs automatically every 12 hours.

## User Review Required
> [!IMPORTANT]
> The new schedule will run **all** maintenance jobs (AI Code Review, AI Validation, Prompt Eval, Cloud Cleanup, Cache Prune) twice a day (every 12 hours). Is this acceptable, or do you want specific jobs (like Cloud Cleanup) to run less frequently (e.g., only on weekends as it was before)? I've set them all to every 12 hours as requested.

## Proposed Changes

### GitHub Workflows

#### [NEW] [scheduled-maintenance.yml](file:///c:/Users/n/supremeai/supremeai_2.0/.github/workflows/scheduled-maintenance.yml)
- Create this new workflow file.
- Configure `on.schedule` to `0 0,12 * * *` (run daily at 00:00 and 12:00 UTC).
- Configure `workflow_dispatch` to allow manual triggers.
- Move the following jobs from `supreme-ci.yml` into this file:
  - `prompt-eval` (LLM Prompt Evaluation)
  - `ai-code-review` (AI Code Review)
  - `ai-validation` (AI Validation)
  - `cleanup-runs` (Cloud Cleanup)
  - `cache-maintenance` (Cache Prune)

#### [MODIFY] [supreme-ci.yml](file:///c:/Users/n/supremeai/supremeai_2.0/.github/workflows/supreme-ci.yml)
- **Remove** the `schedule` block from the `on` triggers.
- **Remove** the `maintenance_job` input from `workflow_dispatch`.
- **Remove** `prompt` references from `detect-changes` and `combine-decisions` logic.
- **Delete** the extracted jobs (`prompt-eval`, `ai-code-review`, `ai-validation`, `cleanup-runs`, `cache-maintenance`).

## Verification Plan

### Automated Tests
- N/A

### Manual Verification
- After pushing the changes, check the GitHub Actions tab.
- Verify that `supreme-ci.yml` is clean and does not trigger maintenance jobs.
- Verify that `scheduled-maintenance.yml` is visible and can be triggered manually via `workflow_dispatch` to test that the extracted jobs run successfully without syntax errors.
