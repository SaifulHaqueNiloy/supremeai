# Fix 102 Test Failures Implementation Plan

The recent architectural and security overhauls have stabilized the main backend systems and eliminated the fundamental application crashes. However, 102 tests are still failing across the monorepo due to mismatches between the updated code and legacy test expectations. 

As an elite engineering operation, we must align all tests with the new unified architecture. 

## Proposed Changes

To safely tackle 102 failing tests, we will group the fixes into 3 phases:

### Phase 1: Configuration & Environment Validations (18 Tests)
Many config tests in `test_config.py` and `test_config_coverage.py` are failing due to recent validator changes in `core/config.py`.
- Fix `test_defaults` assertions (e.g., `ollama_url` defaulting to `""` instead of `http://localhost:11434`).
- Update `test_env_override` patch dictionaries to provide all newly required production keys (e.g. `SUPREMEAI_JWT_SECRET`, valid CORS formats) to satisfy PyDantic V2 strict validation.
- Fix `CORS_ORIGINS` parsing tests to correctly assert the behavior of stripping `localhost` in production environments.

### Phase 2: API Gateway & Router 404 Mismatches (~45 Tests)
Several endpoint tests (`test_api.py`, `test_task_endpoints.py`, `test_payments.py`) are returning `404 Not Found` instead of `200 OK`. 
- Investigate `backend/main.py` and `app.py` to ensure all legacy routers (like `task_endpoints`, `payments`, `graph_routes`) are properly included in the FastAPI app.
- Fix middleware (`origin_validator.py` or `TrustedOriginMiddleware`) that might be short-circuiting TestClient requests to `404`.
- Patch test clients to include valid mocked dependencies or JWTs if new security layers require them.

### Phase 3: LLM Gateway & Self-Healer Integration (~39 Tests)
Tests in `test_llm_gateway.py`, `test_self_healer.py`, and `test_core_missing_coverage.py` are failing due to mismatched mocks or asynchronous signature updates.
- Update `SelfHealer` mocks in `test_llm_gateway.py` to match the new synchronous/asynchronous DB injection requirements.
- Fix `AttributeError` failures by properly mocking `core.services` where test dependencies bypass the module-level aliases.
- Resolve missing coverage branches in `test_acompletion_cost_guard_check` by supplying expected model keys.

## User Review Required

> [!WARNING]
> Since we are dealing with 102 tests, fixing them all in one shot may cause extensive file changes. Are you comfortable with me proceeding with Phase 1 and Phase 2 immediately, or would you prefer I execute one phase at a time and run `pytest` in between to verify?

## Verification Plan

### Automated Tests
- Run `poetry run pytest tests/test_config.py tests/test_config_coverage.py -v` after Phase 1.
- Run `poetry run pytest tests/test_api.py tests/test_task_endpoints.py -v` after Phase 2.
- Finally, run the full suite `poetry run pytest tests/ -v` to confirm a 100% pass rate.
