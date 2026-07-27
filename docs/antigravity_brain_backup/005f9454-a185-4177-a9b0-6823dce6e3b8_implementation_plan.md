# Comprehensive Implementation Plan — Backend Test Reliability & Error Remediation

This implementation plan targets the remaining test failures, model/schema mismatches, and route async issues identified in the test logs across `backend/`.

---

## User Review Required

> [!IMPORTANT]
> - All tests will be updated to match the single source of truth (`Settings` in `core.config`, Pydantic V2 schemas, async routing standards).
> - Production functionality will strictly maintain zero-cost resilience and zero hardcoded secrets.

---

## Component Breakdown & Remediation Plan

### 1. `tests/test_admin_dashboard_full.py` & `api/routes/admin_dashboard.py`
- **Issue**: Mismatched `export_codebase_to_markdown` export function, async coroutine returns in stream handlers (`media_type` attribute error), and monkeypatching immutable `settings` properties.
- **Changes**:
  - Update `api/routes/admin_dashboard.py` to ensure `export_codebase_to_markdown` is correctly exported and non-coroutine response wrappers are returned.
  - Update `tests/test_admin_dashboard_full.py` to mock `_get_cached_secret` or dictionary settings instead of attempting `setattr` on read-only properties.

### 2. `tests/test_email_service.py` & `core/email_service.py`
- **Issue**: `EmailService` signatures expect `to` instead of `to_email` or positional args, missing `settings` attribute on module.
- **Changes**:
  - Align `EmailService` methods (`send_welcome_email`, `send_password_reset`, `send_billing_notification`, `_send_email`) with expected keyword signatures.
  - Expose or mock `settings` cleanly in `core/email_service.py`.

### 3. `tests/test_billing_api_coverage.py` & `api/routes/billing_api.py`
- **Issue**: Missing exports (`get_balance`, `TopUpRequest`), coroutine indexing issues in webhook tests.
- **Changes**:
  - Export `get_balance` and `TopUpRequest` schema from `api/routes/billing_api.py`.
  - Fix test invocations to `await` coroutine responses before indexing.

### 4. `tests/test_code_validator.py` & `tools/code/code_validator.py`
- **Issue**: Mismatched positional arguments for `validate_syntax(language=...)` and dictionary return schema keys (`valid` vs `is_valid`).
- **Changes**:
  - Standardize `CodeValidator` methods to accept optional `language="python"` parameter.
  - Ensure `validate_url` returns consistent dictionary format `{"is_valid": bool, "scheme": str, "netloc": str}`.

### 5. `tests/test_factual_verifier.py` & `core/factual_verifier.py`
- **Issue**: Dictionary key mismatches (`is_correct` vs `is_verified`) and missing `_ddgs` duckduckgo search client attribute.
- **Changes**:
  - Update `FactualVerifier` output schema to include `is_correct` alias matching `is_verified`.
  - Safely initialize `_ddgs` property or fallback gracefully during web search verification.

### 6. `tests/test_events_routes_coverage.py` & `tests/test_evolution_routes_coverage.py`
- **Issue**: Coroutine subscripting in sync test blocks and missing `asyncio` imports in test files.
- **Changes**:
  - Mark route tests with `@pytest.mark.asyncio` and `await` async endpoint functions.
  - Add missing `import asyncio` to test files.

### 7. `tests/test_mcp_servers_integration.py` & `tools/mcp/`
- **Issue**: Missing module imports (`mcp_cloud_deploy`, `mcp_github_cicd`) and return dictionary key mismatches (`row_count`, `success`, `count`).
- **Changes**:
  - Provide fallback module aliases or lazy-loader handles for optional MCP server tools.
  - Standardize Supabase MCP tool responses to include `row_count`, `count`, and `success` status fields.

---

## Verification Plan

### Automated Tests
- Run full pytest test suite in `backend/`:
  ```bash
  poetry run pytest -q --tb=short
  ```
- Run targeted test suites for modified components:
  ```bash
  poetry run pytest tests/test_admin_dashboard_full.py tests/test_email_service.py tests/test_billing_api_coverage.py tests/test_code_validator.py
  ```

### Manual Verification
- Verify CI workflow run locally using pre-commit hooks:
  ```bash
  poetry run pre-commit run --all-files
  ```
