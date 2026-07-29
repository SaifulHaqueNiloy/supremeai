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
