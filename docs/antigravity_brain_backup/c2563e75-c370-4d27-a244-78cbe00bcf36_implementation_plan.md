# Goal Description

The test suite currently has **153 failing tests** across various domains in the backend. The failures range from `TypeError` with AsyncMocks, `ConnectionError` with Redis, `AttributeError` for missing attributes on mocks, and `NameError` for missing imports.

Since the user requested to set a loop and continue until all tests pass, the goal is to iteratively fix these errors. Because fixing 153 disjointed failures at once is impossible without context limits, we will execute this in batches.

## User Review Required

> [!WARNING]
> Fixing 153 tests is a substantial effort. The plan below outlines a systematic approach. If you approve this plan, I will autonomously loop through the code, fix errors batch-by-batch (prioritizing the most common ones first), and re-run the tests after each batch until the suite is 100% green. 
> Please click **Proceed** if you want me to execute this massive stabilization effort.

## Proposed Changes

We will fix the tests by tackling the highest-frequency errors first:

### Batch 1: Async Mock and Await Issues (TypeErrors)
- **Error:** `TypeError: object dict can't be used in 'await' expression` (5 occurrences)
- **Fix:** Update incorrect mocks (e.g., in `test_enqueue_adds_document`, `test_peek_does_not_remove`) that are injecting standard `dict` return values into async functions instead of using proper `AsyncMock` or async helper functions.

### Batch 2: Redis Connection and Mocks
- **Error:** `redis.exceptions.ConnectionError` and `AttributeError` on Redis Queues (6 occurrences)
- **Fix:** Provide properly configured mocked Redis instances or bypass real connection attempts in `test_halt_requires_admin`, `test_record_usage_without_redis`, etc. Add missing `timeout` attributes to mocks for `UpstashRedisQueue`.

### Batch 3: Missing Imports and Basic Syntax
- **Error:** `NameError: name 'Path' is not defined` (2 occurrences)
- **Fix:** Add `from pathlib import Path` to `test_project_context_service.py`.

### Batch 4: Assorted Domain Logic Errors
- **Fix:** Address remaining issues such as `fastapi.exceptions.HTTPException` leaks, Celery app configurations, and SQLAlchemy mock issues.

## Verification Plan

### Automated Tests
- For each batch, we will run `poetry run pytest` to verify the count of failures has decreased.
- We will continue this iterative loop until `poetry run pytest` reports **0 failures**.
