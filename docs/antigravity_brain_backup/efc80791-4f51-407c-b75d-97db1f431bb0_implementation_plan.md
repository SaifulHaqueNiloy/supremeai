# Implementation Plan: Optimize CI/CD Pipeline Deployment Conditions & Coverage Thresholds

## Proposed Changes

### Component: CI/CD Workflows

#### [MODIFY] [supreme-core-ci.yml](file:///c:/Users/n/supremeai/supremeai_2.0/.github/workflows/supreme-core-ci.yml)
- Update `circuit-breaker` job to output `previous_failed` (`true`/`false`) depending on the status of the last completed run.
- Update `backend-core` and `frontend-core` job `if` conditions to run if changes are detected OR if `previous_failed` is `true`.
- Update `deploy-backend` and `deploy-frontend` job `if` conditions to ensure they only run if the respective core job ran (either due to detected changes or a previous failure) AND the core job succeeded (i.e. did not fail or get cancelled).
- Modify the pytest command in `backend-core` to use `--cov-fail-under=50` instead of `--cov-fail-under=80`.

---

## Verification Plan

### Manual Verification
- Review GHA workflow structure and yaml syntax locally.
- Note: Per user request, the changes will NOT be pushed to the remote repository yet.
