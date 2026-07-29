# Failing Tests Report

Generated: 2026-07-29

## Summary

| Suite | Failed | Passed | Skipped |
|-------|--------|--------|---------|
| Backend (Pytest) | 79 | 2980 | 125 |
| Frontend (Vitest) | 3 | 64 | 0 |
| E2E (Playwright) | 35* | 0 | 0 |

*E2E failures are repeated across 5 browser projects (chromium, firefox, webkit, Mobile Chrome, Mobile Safari). There are 7 unique E2E test cases failing.

---

## Backend (Pytest) — 79 failing tests

### tests/byoc
- `tests/byoc/test_cloud_connector.py::TestCloudConnector::test_credential_validation_returns_false_for_malformed`

### tests/core
- `tests/core/test_pubsub.py::test_pubsub_lazy_initialization`
- `tests/core/test_secret_vault_coverage.py::TestSecretVault::test_init`
- `tests/core/test_secret_vault_coverage.py::TestSecretVault::test_get_secret_env_fallback`
- `tests/core/test_secret_vault_coverage.py::TestSecretVault::test_get_secret_not_found`
- `tests/core/test_secret_vault_coverage.py::TestSecretVault::test_set_secret`
- `tests/core/test_secret_vault_coverage.py::TestSecretVault::test_delete_secret`
- `tests/core/test_secret_vault_coverage.py::TestSecretVault::test_list_secrets`
- `tests/core/test_secret_vault_coverage.py::TestSecretVault::test_invalidate_cache`
- `tests/core/test_secret_vault_coverage.py::TestSecretVault::test_fetch_async`
- `tests/core/test_secret_vault_coverage.py::TestSecureCredentialStore::test_init`
- `tests/core/test_secret_vault_coverage.py::TestSecureCredentialStore::test_encrypt_decrypt_roundtrip`
- `tests/core/test_secret_vault_coverage.py::TestSecureCredentialStore::test_mask`
- `tests/core/test_swarm_pubsub.py::TestSwarmPubSubInit::test_creates_redis_connection`

### tests/engine
- `tests/engine/test_cost_optimizer.py::TestCostOptimizer::test_get_optimal_route_simple_paid`
- `tests/engine/test_cost_optimizer.py::TestCostOptimizer::test_get_optimal_route_complex_free`

### tests/
- `tests/test_agent_tools.py::TestCheckSystemHealth::test_returns_status_string`
- `tests/test_browser_routes_coverage.py::TestCredentials::test_delete_credential`
- `tests/test_browser_routes_coverage.py::TestUrlPermissions::test_delete_url`
- `tests/test_cache_cleanup.py::test_scan_keys_success`
- `tests/test_cache_cleanup.py::test_scan_keys_fallback_to_keys`
- `tests/test_cache_cleanup.py::test_scan_keys_both_fail`
- `tests/test_cache_cleanup.py::test_clear_stale_cache_no_redis_url`
- `tests/test_cache_cleanup.py::test_clear_stale_cache_no_keys_found`
- `tests/test_cache_cleanup.py::test_clear_stale_cache_deletes_keys`
- `tests/test_cache_cleanup.py::test_clear_stale_cache_scan_fallback`
- `tests/test_causal_engine.py::test_causal_discovery`
- `tests/test_core_remaining_zero.py::TestToolsImports::test_self_planner_import`
- `tests/test_daily_learner_coverage.py::TestGoalDecomposer::test_heuristic_fallback_code`
- `tests/test_db_repository.py::test_fetch_from_primary_async_doc_returns_document`
- `tests/test_db_repository.py::test_get_document_with_fallback_uses_supabase_on_primary_failure`
- `tests/test_db_repository.py::test_get_document_with_fallback_returns_none_when_both_down`
- `tests/test_evolution_pipeline.py::test_pipeline_success`
- `tests/test_evolution_pipeline.py::test_pipeline_validation_mismatch`
- `tests/test_hallucination_guard.py::test_factual_verifier`
- `tests/test_local_search_rag_coverage.py::TestLocalSearchRAGInit::test_init_with_chromadb`
- `tests/test_local_search_rag_coverage.py::TestLocalSearchRAGInit::test_init_without_chromadb`
- `tests/test_local_search_rag_coverage.py::TestLocalSearchRAGSearch::test_search_with_browser`
- `tests/test_local_search_rag_coverage.py::TestLocalSearchRAGSearch::test_search_with_local_index`
- `tests/test_local_search_rag_coverage.py::TestLocalSearchRAGStore::test_store_and_retrieve`
- `tests/test_local_search_rag_coverage.py::TestLocalSearchRAGSummarize::test_summarize`
- `tests/test_mcp_server.py::test_mcp_list_tools`
- `tests/test_mcp_server.py::test_mcp_call_tool_dependencies`
- `tests/test_mcp_server.py::test_mcp_call_tool_path`
- `tests/test_memory_service_coverage.py::TestMemoryService::test_init`
- `tests/test_memory_service_coverage.py::TestMemoryService::test_store_memory`
- `tests/test_memory_service_coverage.py::TestMemoryService::test_get_memories`
- `tests/test_memory_service_coverage.py::TestMemoryService::test_search_memories`
- `tests/test_memory_service_coverage.py::TestMemoryService::test_delete_memory`
- `tests/test_memory_service_coverage.py::TestMemoryService::test_clear_user_memories`
- `tests/test_memory_service_coverage.py::TestContextWindow::test_get_context_window`
- `tests/test_memory_service_coverage.py::TestContextWindow::test_update_context_window`
- `tests/test_memory_service_coverage.py::TestSemanticSearch::test_semantic_search`
- `tests/test_memory_service_coverage.py::TestSemanticSearch::test_get_recent_interactions`
- `tests/test_meta_ai_coverage.py::TestRequireAdmin::test_require_admin_non_admin_role`
- `tests/test_meta_ai_coverage.py::TestRequestModels::test_metric_record_request`
- `tests/test_prod_docs_security.py::test_docs_visible_in_local`
- `tests/test_prod_docs_security.py::test_docs_disabled_in_production`
- `tests/test_self_planner_coverage.py::TestSelfPlannerInit::test_init_without_llm_client`
- `tests/test_self_planner_coverage.py::TestSelfPlannerInit::test_init_with_llm_client`
- `tests/test_self_planner_coverage.py::TestSelfPlannerGeneratePlan::test_generate_plan_success`
- `tests/test_self_planner_coverage.py::TestSelfPlannerGeneratePlan::test_generate_plan_llm_error`
- `tests/test_self_planner_coverage.py::TestSelfPlannerGeneratePlan::test_generate_plan_invalid_json`
- `tests/test_self_planner_coverage.py::TestSelfPlannerGeneratePlan::test_generate_plan_non_list_response`
- `tests/test_self_planner_coverage.py::TestSelfPlannerGeneratePlan::test_generate_plan_empty_list`
- `tests/test_self_planner_coverage.py::TestSelfPlannerValidatePlan::test_validate_plan_valid`
- `tests/test_self_planner_coverage.py::TestSelfPlannerExecutePlan::test_execute_plan_empty_graph`
- `tests/test_self_planner_coverage.py::TestSelfPlannerExecutePlan::test_execute_plan_with_tasks`
- `tests/test_sso_integrator_coverage.py::TestGetMetadata::test_get_metadata_onelogin_fallback`
- `tests/test_sso_integrator_coverage.py::TestGetMetadata::test_get_metadata_onelogin_error`
- `tests/test_sso_integrator_coverage.py::TestValidateToken::test_validate_token_jose_available`
- `tests/test_sso_integrator_coverage.py::TestValidateToken::test_validate_token_jose_not_available`
- `tests/test_sso_integrator_coverage.py::TestParseSamlResponse::test_parse_saml_response_valid`
- `tests/test_tenant_admin_coverage.py::TestGetDB::test_get_db_success`
- `tests/test_tenant_admin_coverage.py::TestGetDB::test_get_db_no_client`
- `tests/test_tenant_admin_coverage.py::TestGetDB::test_get_db_exception`
- `tests/test_tenant_admin_coverage.py::TestGetTenantUsage::test_get_tenant_usage_redis`
- `tests/test_tenant_admin_coverage.py::TestGetTenantUsage::test_get_tenant_usage_empty`
- `tests/test_web_fallback.py::test_web_fallback`

---

## Frontend (Vitest) — 3 failing tests

- `src/App.test.tsx > App component > renders header, title, and health status`
- `src/App.test.tsx > App component > renders chat console when chat tab is active`
- `src/App.test.tsx > App component > allows user to send messages in the chat console`

---

## E2E (Playwright) — 7 unique failing test cases (35 total failures across browsers)

- `tests/e2e/accessibility.spec.ts:5:9 › Accessibility Tests (WCAG) › Homepage should not have any automatically detectable accessibility issues`
- `tests/e2e/accessibility.spec.ts:19:9 › Accessibility Tests (WCAG) › Admin Dashboard should be accessible`
- `tests/e2e/admin-dashboard.spec.ts:5:7 › SupremeAI Nexus E2E Flow › should load the dashboard and verify Java Worker widget`
- `tests/e2e/admin-dashboard.spec.ts:25:7 › SupremeAI Nexus E2E Flow › should be able to submit an orchestration command via chat`
- `tests/e2e/chat.spec.ts:3:5 › Chat sends message`
- `tests/e2e/visual.spec.ts:4:9 › Visual Regression Tests › Homepage layout should be stable`
- `tests/e2e/visual.spec.ts:10:9 › Visual Regression Tests › ConsentMatrixModal should match the approved snapshot`

---

## Notes

- E2E failures are primarily due to missing Playwright browser binaries (`Executable doesn't exist`). Install with `pnpm exec playwright install`.
- Frontend failures are due to duplicate DOM elements (`Found multiple elements by: [data-testid="header-title"]` and `[data-testid="tab-chat"]`).
- Backend failures span multiple modules including secret vault, pubsub, cache cleanup, database repository, memory service, self-planner, SSO integrator, tenant admin, and others.

---

## 🔍 GitHub CI Failed Jobs — Root Cause Analysis (RCA)

> **Source:** GitHub Actions CI Run — `2026-07-29` · Branch: `main`
> **Total Backend Failures:** 79 · **Root Cause Categories:** 9

---

### RCA-001: `ImportError` — Missing Classes in Refactored Modules

**Affected Tests (12 tests):**
- `tests/core/test_secret_vault_coverage.py` — all 9 tests
- `tests/test_memory_service_coverage.py` — all 10 tests

**Error Messages:**
```
ImportError: cannot import name 'SecretVault' from 'core.security.secret_vault'
ImportError: cannot import name 'SecureCredentialStore' from 'core.security.secret_vault'
ImportError: cannot import name 'MemoryService' from 'services.memory_service'
```

**Root Cause:**
The classes `SecretVault`, `SecureCredentialStore` (in `core/security/secret_vault.py`) and `MemoryService` (in `services/memory_service.py`) have been renamed, removed, or moved to a different module during a refactor. The test files still import them by the old names.

**Fix Required:**
- Verify current class names in `core/security/secret_vault.py` and `services/memory_service.py`
- Update import statements in the test files to match the new class names/locations

---

### RCA-002: `AttributeError` — API Contract Broken (SSOIntegrator)

**Affected Tests (5 tests):**
- `tests/test_sso_integrator_coverage.py` — all 5 tests

**Error Messages:**
```
AttributeError: 'SSOIntegrator' object has no attribute 'saml_settings'
AttributeError: 'SSOIntegrator' object has no attribute 'validate_token'
AttributeError: 'SSOIntegrator' object has no attribute 'parse_saml_response'
```

**Root Cause:**
`SSOIntegrator` class has been refactored. The attributes `saml_settings`, and methods `validate_token`, `parse_saml_response` no longer exist on the object. The public API contract has changed without updating the tests.

**Fix Required:**
- Inspect the current `SSOIntegrator` class definition
- Update test mocks and assertions to match the new API

---

### RCA-003: `AttributeError` — tenant_admin Module-Level Attributes Removed

**Affected Tests (5 tests):**
- `tests/test_tenant_admin_coverage.py` — all 5 tests

**Error Messages:**
```
AttributeError: module 'api.routes.tenant_admin' does not have the attribute 'db'
AttributeError: module 'api.routes.tenant_admin' does not have the attribute 'app_mod'
```

**Root Cause:**
Tests patch `api.routes.tenant_admin.db` and `api.routes.tenant_admin.app_mod` as module-level attributes, but these were refactored away. The `db` dependency and `app_mod` are no longer exposed at module level in `tenant_admin.py`.

**Fix Required:**
- Update tests to patch the correct dependency injection path
- Use FastAPI's `Depends()` override pattern or mock at the correct import path

---

### RCA-004: `AttributeError` — SelfPlanner API Changed

**Affected Tests (7 tests):**
- `tests/test_self_planner_coverage.py` — all 7 tests

**Error Messages:**
```
AttributeError: module 'tools.self_planner' does not have the attribute 'ModelRouter'
AttributeError: 'SelfPlanner' object has no attribute 'execute_plan'
```

**Root Cause:**
Two breaking changes in `tools/self_planner.py`:
1. `ModelRouter` class was removed/moved from the module (tests patch `tools.self_planner.ModelRouter`)
2. `SelfPlanner.execute_plan()` method was renamed or removed

**Fix Required:**
- Locate `ModelRouter` in the new module path and update the patch target
- Verify the new method name for `execute_plan` in `SelfPlanner`

---

### RCA-005: `AttributeError` — LocalSearchRAG API Changed

**Affected Tests (6 tests):**
- `tests/test_local_search_rag_coverage.py` — all 6 tests

**Error Messages:**
```
AttributeError: module 'tools.knowledge.local_search_rag' does not have the attribute 'chromadb'
AttributeError: 'LocalSearchRAG' object has no attribute 'store'
AttributeError: 'LocalSearchRAG' object has no attribute 'summarize'
AttributeError: 'coroutine' object has no attribute 'get'  (async method not awaited)
TypeError: object dict can't be used in 'await' expression
```

**Root Cause:**
`LocalSearchRAG` class API has changed:
1. `chromadb` is no longer a module-level attribute (no longer imported at module scope)
2. `store()` and `summarize()` methods were renamed or removed
3. Some tests call async methods without `await`, causing coroutine attribute errors

**Fix Required:**
- Update `chromadb` patch target to the correct import location
- Rename test calls to match current `LocalSearchRAG` public API
- Ensure async methods are awaited in async test contexts

---

### RCA-006: `TypeError: MagicMock can't be used in 'await' expression`

**Affected Tests (6 tests):**
- `tests/test_db_repository.py` — 3 tests
- `tests/test_mcp_server.py` — 3 tests

**Error Message:**
```
TypeError: object MagicMock can't be used in 'await' expression
```

**Root Cause:**
Tests use `unittest.mock.MagicMock` to mock async functions/methods that are now called with `await`. `MagicMock` returns a regular value, not a coroutine. Must use `AsyncMock` for any awaitable.

**Fix Required:**
```python
# ❌ Wrong
mock_fn = MagicMock(return_value={"doc": "value"})

# ✅ Correct
from unittest.mock import AsyncMock
mock_fn = AsyncMock(return_value={"doc": "value"})
```

---

### RCA-007: `ValueError: chromadb.__spec__ is not set` (App Import Crash)

**Affected Tests (2 tests):**
- `tests/test_prod_docs_security.py` — 2 tests

**Error Message:**
```
ValueError: chromadb.__spec__ is not set
File "experience_db.py", line 14:
    HAS_CHROMADB = (not LOW_MEMORY_MODE) and importlib.util.find_spec("chromadb") is not None
```

**Root Cause:**
`conftest.py` mocks `chromadb` as a `MagicMock()` object in `sys.modules`. However, `adaptive_engine/experience_db.py` calls `importlib.util.find_spec("chromadb")`, which internally checks `sys.modules["chromadb"].__spec__`. The mock's `__spec__` is a `MagicMock` (not `None` or a valid `ModuleSpec`), causing `find_spec()` to raise `ValueError`.

**Fix Required:**
In `conftest.py`, set a proper `__spec__` on the chromadb mock:
```python
# বাংলা মন্তব্য: chromadb mock এর __spec__ কে None সেট করতে হবে
# যাতে importlib.util.find_spec() ValueError না দেয়
chromadb_mock = create_mock_module("chromadb", is_package=True)
chromadb_mock.__spec__ = None  # ← Critical fix
sys.modules["chromadb"] = chromadb_mock
```

---

### RCA-008: Lazy Redis Init — `from_url` Not Called at Startup

**Affected Tests (2 tests):**
- `tests/core/test_pubsub.py::test_pubsub_lazy_initialization`
- `tests/core/test_swarm_pubsub.py::TestSwarmPubSubInit::test_creates_redis_connection`

**Error Message:**
```
AssertionError: Expected 'from_url' to be called once. Called 0 times.
```

**Root Cause:**
Tests assume Redis connection is established eagerly (at `__init__` time). The implementation was changed to **lazy initialization** — `Redis.from_url()` is now called only on first use, not at object creation.

**Fix Required:**
Update tests to trigger the first Redis operation before asserting `from_url` was called, or update the assertion to reflect lazy initialization behavior.

---

### RCA-009: Logic/Routing Assertion Failures

**Affected Tests (9 tests):**

| Test | Error | Root Cause |
|------|-------|------------|
| `test_cost_optimizer.py::test_get_optimal_route_simple_paid` | `assert 'gemini/gemini-1.5-flash' == 'ollama/llama3.2'` | Cost optimizer routing changed — simple paid tasks now route to Gemini Flash instead of Ollama |
| `test_cost_optimizer.py::test_get_optimal_route_complex_free` | `assert False` (`groq/...` does not startswith `anthropic`) | Free tier routing changed — complex tasks now route to Groq instead of Anthropic |
| `test_cache_cleanup.py` — 4 tests | `assert <MagicMock...> == ['key1', ...]` | `scan_keys()` returns wrong type — function now returns a coroutine/mock object instead of a list |
| `test_browser_routes_coverage.py` — 2 tests | `assert 1 == 0` (list not empty after delete) | In-memory store not properly cleared between tests — missing teardown fixture |
| `test_meta_ai_coverage.py::test_require_admin_non_admin_role` | `assert 401 == 403` | `require_admin` changed to return HTTP 401 (auth failure) instead of 403 (forbidden) for non-admin |
| `test_meta_ai_coverage.py::test_metric_record_request` | `AttributeError: LATENCY` | `MetricRecordRequest` model no longer has `LATENCY` enum attribute |
| `test_causal_engine.py::test_causal_discovery` | `assert 0 == 3` (empty results) | Causal discovery returns no edges — algorithm or data fixture changed |
| `test_byoc/test_cloud_connector.py` | `assert True is False` | Credential validation now accepts malformed credentials (logic changed) |
| `test_daily_learner_coverage.py` | `assert False` | Heuristic fallback code pattern changed — test keyword no longer in output |

---

### 📊 RCA Summary Table

| RCA ID | Category | Tests Affected | Priority |
|--------|----------|---------------|----------|
| RCA-001 | ImportError — class renamed/moved | 19 | 🔴 Critical |
| RCA-002 | AttributeError — SSOIntegrator API | 5 | 🔴 Critical |
| RCA-003 | AttributeError — tenant_admin refactor | 5 | 🔴 Critical |
| RCA-004 | AttributeError — SelfPlanner API | 7 | 🔴 Critical |
| RCA-005 | AttributeError — LocalSearchRAG API | 6 | 🔴 Critical |
| RCA-006 | TypeError — MagicMock not AsyncMock | 6 | 🟠 High |
| RCA-007 | ValueError — chromadb.__spec__ mock | 2 | 🟠 High |
| RCA-008 | Lazy Redis init assumption | 2 | 🟡 Medium |
| RCA-009 | Logic/routing assertion failures | 9 | 🟡 Medium |
| **Total** | | **61** | |

> 📌 **Recommended Fix Order:** RCA-001 → RCA-006 → RCA-007 → RCA-002 → RCA-003 → RCA-004 → RCA-005 → RCA-008 → RCA-009
