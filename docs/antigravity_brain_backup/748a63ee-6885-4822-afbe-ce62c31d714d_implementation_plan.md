# Smart Cache Lifecycle Strategy & Pipeline Improvements

Thank you for the excellent suggestion! The current implementation of cache pruning in the pipelines is actually **destructive** rather than smart. 

Currently, `supreme-core-ci.yml` and `nightly-maintenance.yml` both contain a step named `Force Purge Unnecessary Old Caches (Smartest Clean)` which blindly deletes **all** caches via `gh cache delete` (without filtering for age or patterns). This forces a 100% cache miss on every subsequent run, completely defeating our Granular Caching Strategy.

## User Review Required

> [!WARNING]
> Please review these proposed changes to fully implement the **Smart Cache Lifecycle Strategy**. Once approved, I will implement them directly into the repository.

## Proposed Changes

### 1. Remove Destructive Purge from Core CI
- **File:** `.github/workflows/supreme-core-ci.yml`
- **Action:** Completely remove the `Force Purge Unnecessary Old Caches` step from the `generate-codebase-docs` job. Cache pruning should not happen on every push.

### 2. Implement Smart Pruning Script
- **File:** `scripts/prune_cache.sh` (New File)
- **Action:** Create the script using the GitHub Actions CLI to delete caches that match specific outdated patterns or are older than a certain threshold (e.g., older than 7 days). 

### 3. Update Nightly Maintenance Workflow
- **File:** `.github/workflows/nightly-maintenance.yml`
- **Action:** Update the `cache-prune` job to execute `bash scripts/prune_cache.sh` instead of the hardcoded `awk` loop.
- **Action:** Update all Python environment setups in this file to use `snok/install-poetry@v1` and the Granular Cache Strategy (with `restore-keys`), matching what we did in `supreme-core-ci.yml`.

### 4. Optimize Node.js Dependencies Layering (pnpm)
- The current pipelines use `actions/setup-node@v4` with `cache: 'pnpm'`. This correctly layers the global pnpm store (Layer 2) and separates it from the local `node_modules` (Layer 1). This is optimal and ensures the 10GB limit isn't bloated with redundant `node_modules`.

## Verification Plan
- Ensure that `.github/workflows/nightly-maintenance.yml` triggers correctly on its schedule (`cron: '0 0 * * *'`).
- Ensure `scripts/prune_cache.sh` is executable (`chmod +x`).
