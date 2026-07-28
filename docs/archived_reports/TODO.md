# Test Fix TODO.md

## Step 1: Fix AuthMiddleware blocking test requests (highest impact)
- [x] Set `ALLOW_TEST_AUTH_BYPASS=true` in conftest.py's `isolate_env` fixture
- [x] Update `override_auth` fixture to also mock at middleware level via monkeypatch
- [x] Ensure `settings.allow_test_auth_bypass` is properly set before app creation

## Step 2: Fix test_config_cache.py failures
- [ ] Fix `test_config_cache_get_fallback` - mock `database.session.AsyncSessionLocal` at module level
- [ ] Fix `test_config_cache_set_and_invalidate` - ensure proper mock cleanup

## Step 3: Fix test_health.py tests
- [ ] Rewrite tests to use monkeypatch without module reload
- [ ] Remove `@pytest.mark.skip` decorators
- [ ] Use direct mock patching of `core.services.redis_queue`

## Step 4: Fix test_celery_app.py AttributeError
- [ ] Fix mock target path in test

## Step 5: Fix test_code_validator.py async function test
- [ ] Fix test code to avoid referencing undefined variables

## Step 6: Fix RBAC and other assertion failures
- [ ] Fix test_rbac.py parametrize test
- [ ] Fix test_provider_failover_chain.py assertions
- [ ] Fix other assertion-based failures

## Step 7: Fix telemetry test failures
- [ ] Update mock structure for opentelemetry

## Step 8: Run tests and verify fixes
- [ ] Run `pytest tests/test_api.py -x --tb=short` to verify auth fix
- [ ] Run targeted test files to verify individual fixes
- [ ] Run full test suite

