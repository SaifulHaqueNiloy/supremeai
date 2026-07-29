# Failing Tests Report

Generated: 2026-07-29

## Summary

| Suite | Failed | Passed | Skipped |
|-------|--------|--------|---------|
| Backend (Pytest) | 61 | 2980 | 125 |
| Frontend (Vitest) | 3 | 64 | 0 |
| E2E (Playwright) | 35* | 0 | 0 |

*E2E failures are repeated across 5 browser projects (chromium, firefox, webkit, Mobile Chrome, Mobile Safari). There are 7 unique E2E test cases failing.

## Status Update
- ✅ Fixed `tests/core/test_secret_vault_coverage.py` (11/11 passing)
- ✅ Fixed `tests/test_memory_service_coverage.py` (8/8 passing)
- ⏳ Remaining: 61 backend failures across multiple modules

---
*Remaining failures documented in previous version of this file*
