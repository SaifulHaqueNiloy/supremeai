# 🔬 Maintenance Pipeline Analysis & Enhancement Plan

## Current State: What We Have

| Job | Trigger | Status |
|-----|---------|--------|
| `setup` | Always | ✅ Runs first, generates cache key |
| `health-check` | `run_health_check` | ✅ Calls `health_checker.py` |
| `auto-lint-fix` | `run_auto_lint_fix` | ✅ Ruff + Black + isort → creates PR |
| `dependency-vulnerability-scan` | `run_dependency_scan` | ✅ pip-audit JSON report |
| `generate-codebase-docs` | `run_generate_docs` | ✅ ADR, DFD, OpenAPI → GitHub Pages |
| `worker-test` | `run_worker_test` | ✅ Cloudflare Vitest (migrated) |
| `performance-e2e-test` | `run_performance_e2e` | ✅ Playwright E2E (migrated) |

---

## 🔴 Problems Found (Fix Now)

1. **`NODE_VERSION` env var missing** — `worker-test` and `performance-e2e-test` use `${{ env.NODE_VERSION }}` but this is only defined in supreme-core-ci, not maintenance_pipeline. Will cause runtime error.
2. **No scheduled run** — The maintenance pipeline never runs automatically. Overnight failures go undetected until morning.
3. **`setup` job overhead wasted** — `worker-test`/`performance-e2e-test` don't use the cache from `setup`, so setup runs unnecessarily for them.

---

## 🟡 What's Missing (New Jobs to Add)

| Job | Purpose | Auto-fix Possible? |
|-----|---------|---------------------|
| `ci-failure-smart-summary` | Detect failed Core CI jobs & show admin fix guide | ✅ **YES — main feature** |
| `outdated-dependency-report` | `pip list --outdated` + pnpm outdated → artifact | ❌ Report only |
| `changelog-generator` | Auto-generate CHANGELOG.md from git commits → PR | ✅ Auto PR |
| `cache-purge` | Purge Redis stale keys via Upstash API | ✅ Auto |
| `secret-rotation-checker` | Warn if secrets (API keys) are expiring soon | ❌ Alert only |

---

## ⭐ Smart CI Failure Summary (Main Feature)

**Problem:** When Core CI fails, the admin must manually dig through GitHub logs. Slow and painful.

**Solution:** A `ci-failure-smart-summary` job that:
1. Calls GitHub API → finds the **latest failed run** of `🧠 SupremeAI Core CI`
2. Identifies **which jobs failed** and inspects their annotations/logs
3. Produces a **rich admin panel** in `$GITHUB_STEP_SUMMARY` with:
   - ❌ Failed job name + reason
   - 🔧 Recommended Maintenance Pipeline action to fix it
   - 🔗 Direct one-click link to trigger that maintenance job

### Auto-Fix Mapping: Core CI Failure → Maintenance Fix

| Core CI Failed Job | Likely Cause | Maintenance Fix Action |
|---|---|---|
| `pre-merge-gate` (Ruff/lint) | `print()` / lint violation | ✅ Run `auto-lint-fix` |
| `backend-core` (pytest fail) | Code logic / import error | ✅ Run `auto-lint-fix` → check logs |
| `frontend-core` (ESLint/build) | TS error / ESLint violation | ✅ Run `auto-lint-fix` |
| `security-audit` (Trivy/CodeQL) | Dependency CVE found | ✅ Run `dependency-vulnerability-scan` |
| `production-readiness` (stub data) | Stub/placeholder in code | ❌ Manual code review required |
| Any job (dep conflict) | Poetry/pnpm version mismatch | ✅ Run `dependency-vulnerability-scan` |
| `deploy-to-render` | Render hook failure / secret missing | ❌ Manual secret check |

---

## Implementation Plan

### Phase 1 — Fix Existing Bugs (Quick)
- Add `env: NODE_VERSION: '24'` block to maintenance_pipeline
- Add `schedule: cron: '0 2 * * *'` (nightly 2am UTC auto-run)
- Add `run_ci_failure_summary` input toggle

### Phase 2 — Smart CI Failure Summary Job
- New job: `ci-failure-smart-summary`
- Uses `GITHUB_TOKEN` to call GitHub REST API
- Python script: `detect-previous-failures.py` (already exists!) extended to output failure details
- Renders a beautiful markdown admin panel in Step Summary
- Optionally sends Discord notification (if `DISCORD_WEBHOOK_URL` secret exists)

### Phase 3 — New Utility Jobs
- `outdated-dependency-report`: pip + pnpm outdated → uploaded artifact
- `changelog-generator`: `git log` → CHANGELOG.md → auto PR
- `cache-purge`: Upstash Redis flush via REST API

---

> [!IMPORTANT]
> **Q1:** `ci-failure-smart-summary` কি শুধু GitHub Step Summary-তে দেখাবে, নাকি Discord webhook-এও পাঠাবে? Discord-এর জন্য `DISCORD_WEBHOOK_URL` secret লাগবে।

> [!NOTE]
> **Q2:** `changelog-generator` কি PR তৈরি করবে নাকি সরাসরি `develop`-এ push করবে?
