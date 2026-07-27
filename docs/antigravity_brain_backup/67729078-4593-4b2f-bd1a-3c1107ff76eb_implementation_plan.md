# Consolidate Docs Deployment into SupremeAI Core CI

This plan integrates the GitHub Pages deployment steps directly into the `generate-codebase-docs` job of `supreme-core-ci.yml` and removes the redundant `deploy-docs.yml` file.

## Proposed Changes

### [CI/CD Workflow Config]

#### [MODIFY] [.github/workflows/supreme-core-ci.yml](file:///c:/Users/n/supremeai/supremeai_2.0/.github/workflows/supreme-core-ci.yml)
- Update `generate-codebase-docs` job to:
  - Add explicit permissions: `contents: write`, `pages: write`, `id-token: write`.
  - Add deployment steps using `actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`, and `actions/deploy-pages@v4`.
  - Restrict the deploy-pages step to runs on the `main` branch.

#### [DELETE] [.github/workflows/deploy-docs.yml](file:///c:/Users/n/supremeai/supremeai_2.0/.github/workflows/deploy-docs.yml)
- Remove this file entirely as its logic is now merged.

## Verification Plan

### Manual Verification
- Commit the changes and check the workflow run to verify that `generate-codebase-docs` successfully generates documentation, pushes it to GitHub, and triggers GitHub Pages deployment directly.
