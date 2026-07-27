# Implementation Plan: Fix 5 Pipeline Bugs and Optimize GitHub Actions (Local Only)

This plan resolves 5 critical bugs in `supreme-ci.yml` and implements optimization updates:

1. **Deployment Skip Bug**: Modify the `if` conditions in deployment jobs (`deploy-backend`, `deploy-studio`, `deploy-webchat`) to include `if: always() && ...` alongside check for `success`/`skipped` status of their needs, ensuring pipeline steps don't block deployment when tests are skipped due to change detection.
2. **`continue-on-error` Check**: Verify that no critical test or build jobs (`backend-test`, `frontend-monorepo-ci`) have `continue-on-error: true` enabled.
3. **Infinite Loop Prevention**: Already completed in the previous step by switching `ci-auto-fix-v3.py` to a PR-based model (`gh pr create` on separate branches) rather than direct pushes.
4. **Cache Size Optimization**: Confirm that both backend test pipelines run `poetry install --sync --without ml` to prevent heavy ML packages like PyTorch from bloating the runner environment to 5.6 GB.
5. **Double Caching Elimination**: Clean up all manual caching steps for `pnpm` and `Flutter` in `supreme-ci.yml`, using only the built-in caches of setup actions.

## User Review Required

> [!WARNING]
> - `Cargo.lock` remains completely untouched.
> - No `git push` is performed. All changes will be committed locally.

## Proposed Changes

### 1. Workflow Configuration Updates

#### [MODIFY] [supreme-ci.yml](file:///c:/Users/n/supremeai/supremeai_2.0/.github/workflows/supreme-ci.yml)
- Merge frontend/mobile jobs into `frontend-monorepo-ci`.
- Remove manual `pub ক্যাশ` for Flutter.
- Update downstream dependencies (`ci-report`, `deploy-studio`, `deploy-webchat`, `cache-cleanup`, `build-vsix`, `build-windows-exe`) to depend on `frontend-monorepo-ci` and `backend-test`.
- Fix the **Deployment Skip Bug** by adding `always() &&` to the deployment jobs' `if` conditions.
- Add Bangla comments.

---

### 2. Auto-Fix Configuration

#### [MODIFY] [ci-auto-fix-v3.py](file:///c:/Users/n/supremeai/supremeai_2.0/.github/scripts/ci-auto-fix-v3.py)
- Map `frontend-monorepo-ci` in `JOB_FIXERS` to automatically trigger fixes in `apps/studio-client`, `apps/web-chat`, `tools/vscode-extension`, and `apps/mobile`.
- Add Bangla comments.

---

## Verification Plan

### Automated Tests
- Validate YAML structure of `.github/workflows/supreme-ci.yml` via local syntax check.
- Commit all changes locally.
