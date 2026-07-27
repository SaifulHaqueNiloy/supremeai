# Implementation Plan — Fix Admin Backend Startup and Health Check

The `supremeai-admin` service fails to deploy and times out on Render. The logs show that curl requests to `https://supremeai-admin.onrender.com/api/v1/health` receive no response (status code `000`), indicating that the server crashes or hangs during startup.

## Root Cause Analysis

1. **Circular/Heavy Imports on Startup**:
   - `core/app_admin.py` imports `build_app_shell` and `router_health_check` from `core/app.py`.
   - `core/app.py` has module-level side effects: it instantiates a global `app` and calls `register_all_routers(app)`, which imports all user-facing optional routers.
   - Some optional routers, such as `tools.image_to_code` and `tools.style_learner`, immediately load heavy machine learning dependencies (e.g. `sentence-transformers/all-MiniLM-L6-v2` model weights via Hugging Face Hub) at module import time.
   - Downloading weights or initializing these models consumes excessive memory, exceeding Render's Free tier limits (~512MB RAM) and causing the admin service process to get killed (OOM) or hang indefinitely during startup.

2. **Strict Route Count Validation (`MIN_EXPECTED_ROUTES`)**:
   - `router_health_check(app)` asserts that the app has at least 20 routes (defaulting from `MIN_EXPECTED_ROUTES`).
   - The isolated `supremeai-admin` service only loads `ADMIN_ROUTERS`. If the total registered routes fall below 20 (especially when some fail to import), the server calls `sys.exit(1)` and crashes on startup.

## Proposed Changes

To fix these issues, we will decouple the FastAPI builder helpers from the legacy/test global app instantiations.

### 1. Extract Core Builder to `core/app_builder.py`

#### [NEW] [app_builder.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/app_builder.py)
- Create a new module containing `InterceptHandler`, `build_app_shell`, `router_health_check`, and all core middlewares.
- Update `router_health_check` to accept an optional `expected_count` parameter.
- Add explanation comments in **Bangla** as required by the coding standards.

### 2. Refactor App Entry Points

#### [MODIFY] [app.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/app.py)
- Import `build_app_shell` and `router_health_check` from `core/app_builder.py`.
- Keep the legacy global `app` initialization for tests and backward compatibility.

#### [MODIFY] [app_user.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/app_user.py)
- Import `build_app_shell` and `router_health_check` from `core/app_builder.py` instead of `core/app.py`.

#### [MODIFY] [app_admin.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/app_admin.py)
- Import `build_app_shell` and `router_health_check` from `core/app_builder.py` instead of `core/app.py`.
- Call `router_health_check(app, expected_count=5)` to allow the smaller set of admin routes to pass validation.

### 3. Update Render Infrastructure Configurations

#### [MODIFY] [render.yaml](file:///c:/Users/n/supremeai/supremeai_2.0/render.yaml)
- Add `MIN_EXPECTED_ROUTES: 5` environment variable to the `supremeai-admin` service definition.

---

## Verification Plan

### Automated Tests
- Run tests on the app configuration import to verify that the admin backend imports successfully without side effects.
- Command:
  ```bash
  $env:SERVICE_ROLE="admin"; $env:ENV="local"; $env:PYTHONPATH="backend"; .venv/Scripts/python -c "from core.app_admin import app; print('Success! Routes loaded:', len(app.routes))"
  ```
- Run general backend tests:
  ```bash
  pnpm backend:test
  ```

### Manual Verification
- Confirm that no heavy packages (like Hugging Face `sentence-transformers`) are imported during `core.app_admin` module execution.
