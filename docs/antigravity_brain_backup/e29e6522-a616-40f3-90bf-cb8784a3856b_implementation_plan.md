# Backend Endpoint Fix Implementation Plan

Based on the audit report, we need to address several critical route conflicts, missing registrations, and security issues across the FastAPI backend.

## User Review Required

> [!WARNING]
> Please review the proposed fixes, especially the routing changes, to ensure they don't break existing frontend clients.
> Specifically:
> 1. In `task_workspace.py`, changing the route prefix from `/task` to `/workspace/task` to avoid conflict with `task.py`.
> 2. Removing hardcoded `user_id` in `billing_api.py` requires requests to include a valid Authorization header.

## Open Questions
- Do you want to merge the `payments.py` and `billing_api.py` Stripe webhooks, or should we keep them separate for now? I plan to keep them as-is but fix the bugs in `billing_api.py`.
- Should I completely remove the 501 error block in `auth.py` so direct login works in production?

## Proposed Changes

### 1. Centralized Route Registration (`main.py` & `core/app.py`)
- We will consolidate route registration to reduce duplication.
- Remove duplicate entries for `evolution`, `auth`, and `onboarding` in `core/app.py`.
- Add the missing `swarm.py` router to `core/app.py` so it is reachable.

#### [MODIFY] `core/app.py`
- Remove `api.routes.auth` from `core_routers` if it's already in `main.py` (or vice versa).
- Remove duplicate `api.routes.evolution` from `optional_routers`.
- Add `("api.routes.swarm", "/api/v1/swarm")` to `core_routers`.

### 2. Route Conflicts and Fixes

#### [MODIFY] `api/routes/task_workspace.py`
- Change router prefix from `/task` to `/workspace-task` to prevent overriding `task.py`'s `/task/execute`.

#### [MODIFY] `api/routes/swarm.py`
- The `limiter` is not attached to the FastAPI app, so the `@limiter.limit` decorator will fail. We will import the central limiter if one exists, or remove the local one and rely on the global rate limiting.

### 3. Security and Dependency Fixes

#### [MODIFY] `api/routes/billing_api.py`
- **Security Fix:** Replace `user_id = "default_user_session"` with actual `user_id` extracted from the JWT token via `Depends(get_current_user_token)`.

#### [MODIFY] `api/routes/evolution.py`
- Fix `Depends(FitnessEngine)` which causes runtime errors because it's a class. We'll instantiate it properly.

#### [MODIFY] `api/routes/admin.py`
- Fix the relative path for `AdminGodLayer` to use absolute path resolution via `pathlib`, preventing crashes when the server is started from a different working directory.

#### [MODIFY] `api/routes/auth.py`
- Re-evaluate the `HTTPException(status_code=501)` for direct login in production. (Will remove or modify based on your feedback).

## Verification Plan

### Automated Tests
- Run `pytest` or `pnpm backend:test` if available.
- Check that the server boots without duplicate route warnings.

### Manual Verification
- Inspect the `/docs` (Swagger UI) to confirm that no duplicate routes exist and that the `/api/v1/swarm` routes are now visible.
- Verify `billing_api` endpoints require authentication.
