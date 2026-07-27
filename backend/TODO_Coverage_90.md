# Coverage 90% Implementation Tracker

## Phase 1: Fix Cache Cleanup Test (Dynamic Import → Normal Import)
- [ ] Rewrite `test_cache_cleanup.py` to use `sys.path` import instead of `importlib`
- [ ] Verify coverage tool can track `tools/cache_cleanup.py`

## Phase 2: Extend Admin Dashboard Tests
- [ ] `test_admin_dashboard_full.py`: Add `impersonate_user` tests
- [ ] `test_admin_dashboard_full.py`: Add `emergency_deploy` tests
- [ ] `test_admin_dashboard_full.py`: Add `trigger_backup` / `get_backups` tests
- [ ] `test_admin_dashboard_full.py`: Add `get_feature_flags` / `update_feature_flag` tests
- [ ] `test_admin_dashboard_full.py`: Add `get_full_data_export` tests
- [ ] `test_admin_dashboard_full.py`: Add `run_security_scan` tests
- [ ] `test_admin_dashboard_full.py`: Add `admin_websocket` tests (WS connect/disconnect)
- [ ] `test_admin_dashboard_full.py`: Add `execute_manual_gate_override` tests
- [ ] `test_admin_dashboard_full.py`: Add `get_ci_logs` / `receive_ci_report` tests
- [ ] `test_admin_dashboard_full.py`: Add `get_events` / `list_reports` tests
- [ ] `test_admin_dashboard_full.py`: Add `get_roles` / `get_permissions` tests
- [ ] `test_admin_dashboard_full.py`: Add Workspace CRUD tests
- [ ] `test_admin_dashboard_full.py`: Add Settings CRUD tests
- [ ] `test_admin_dashboard_full.py`: Add Sessions / Customers tests
- [ ] `test_admin_dashboard_full.py`: Add `require_admin_token` / `admin_rate_limit` tests

## Phase 3: Extend API Keys Tests
- [ ] `test_api_keys_coverage.py`: Add `list_all_keys` tests
- [ ] `test_api_keys_coverage.py`: Add `get_key` tests
- [ ] `test_api_keys_coverage.py`: Add `delete_key` tests
- [ ] `test_api_keys_coverage.py`: Add `key_usage` / `key_stats` tests
- [ ] `test_api_keys_coverage.py`: Add `record_usage_hook` tests
- [ ] `test_api_keys_coverage.py`: Add `quota_alert` tests
- [ ] `test_api_keys_coverage.py`: Add `bulk_delete` tests
- [ ] `test_api_keys_coverage.py`: Add wrapper function tests

## Phase 4: New SSO Integrator Tests
- [ ] Create `tests/test_sso_integrator_coverage.py` with comprehensive tests

## Phase 5: Extend LLM Router Tests
- [ ] `test_llm_router.py`: Add failover routing edge cases
- [ ] `test_llm_router.py`: Add provider weights configuration tests
- [ ] `test_llm_router.py`: Add cost-sensitive ordering edge cases

## Phase 6: New API Routes __init__ Tests
- [ ] Create `tests/test_api_routes_init.py` for router import safety

## Final Verification
- [ ] Run full test suite and coverage report
- [ ] Verify no regressions
</｜｜DSML｜｜parameter>
</create_file>
