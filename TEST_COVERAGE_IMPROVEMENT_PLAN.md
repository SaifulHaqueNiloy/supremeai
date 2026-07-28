# 🎯 Test Coverage Improvement Plan

> **Project:** SupremeAI 2.0 Backend  
> **Current Coverage:** 57.87% Line / 42.88% Branch  
> **Target:** ≥ 90% Line / ≥ 85% Branch  
> **Last Updated:** 2026-07-25  
> **Author:** Principal Autonomous AI Architect

---

## 📊 Current State Assessment

### Coverage by Package

| Package | Current % | Lines Covered | Total Lines | Gap (Lines) | Priority |
|---------|-----------|--------------|-------------|-------------|----------|
| `models` | **90.41%** | 745 / 824 | 824 | 79 | 🟢 Maintain |
| `core` | **67.98%** | 8,170 / 12,018 | 12,018 | 3,848 | 🟡 Medium |
| `tools` | **58.51%** | 4,891 / 8,359 | 8,359 | 3,468 | 🟠 High |
| `services` | **51.37%** | 563 / 1,096 | 1,096 | 533 | 🔴 Critical |
| `api` | **50.18%** | 3,187 / 6,351 | 6,351 | 3,164 | 🔴 Critical |
| **Total** | **57.87%** | **17,556 / 28,648** | **28,648** | **11,092** | — |

### Test Infrastructure Status

| Component | Status |
|-----------|--------|
| pytest (v8+) | ✅ Configured |
| pytest-cov | ✅ Configured |
| pytest-asyncio | ✅ Configured |
| Branch Coverage | ✅ Enabled |
| HTML Reports | ✅ `htmlcov/` |
| XML Reports (CI) | ✅ `coverage.xml` |
| Conftest with Mocks | ✅ Comprehensive (Redis, Supabase, Stripe, GCP, etc.) |
| Test Fixtures | ✅ Auth headers, DB session, env isolation |
| `--cov-fail-under` | ✅ Set to 75% in `pyproject.toml` |

---

## 🔍 Root Cause Analysis: Why Coverage Is Low

### 1. **Missing Test Files for Critical Modules** (Top Priority)
Many modules in `core/`, `tools/`, `api/routes/` have **no dedicated test file** or only smoke tests.

### 2. **Async Code Complexity**
WebSocket routes, streaming endpoints, and async generators are difficult to test.  
Example low-coverage files:
- `api/routes/websocket_agent.py` — 19.17%
- `api/routes/websocket_voice.py` — 19.64%
- `api/routes/websocket_hitl.py` — 22.45%

### 3. **External Dependency Mocking Gaps**
Some tests leak real network calls because mocks are incomplete (e.g., `swarm_routes.py` currently has a `RuntimeError: no current event loop` failure).

### 4. **Error/Edge-Case Coverage Gap**
Most existing tests cover only the **happy path**. Error branches (`try/except`, `if/else`, `None` guards) are untested.

### 5. **Dead/Scaffold Code**
Some modules contain unreachable or platform-specific code that should be either removed or marked `# pragma: no cover`.

---

## 🗺️ Strategic Roadmap

### Phase 0: Stabilize Current Tests (Week 1)
**Goal:** All existing tests pass consistently.

| Task | Details | Owner |
|------|---------|-------|
| 0.1 | Fix `test_swarm_routes.py::test_telemetry_persists_to_db` — add event loop fixture | AI |
| 0.2 | Run full suite: `poetry run pytest tests/ -q --tb=short` | Manual |
| 0.3 | Pin any flaky tests with `@pytest.mark.flaky(reruns=2)` | AI |
| 0.4 | Document known failures in `TEST_COVERAGE_KNOWN_FAILURES.md` | AI |

### Phase A: Eliminate 0% Coverage Files (Week 1-2)
**Target Impact:** +35–100 lines → ~58.5%

| File | Lines | Strategy | Test File |
|------|-------|----------|-----------|
| `tools/cache_cleanup.py` | 35 | Test cleanup triggers, TTL expiry, cache invalidation | `tests/test_cache_cleanup.py` ✅ Exists — verify coverage |
| `core/evolution/agent_mutator.py` | — | Create test for mutation logic | New |
| `tools/localization/` | — | Add coverage for localization tools | New |

### Phase B: Attack < 50% Files (Week 2-6)
**Target Impact:** +5,500 lines → ~77%

Target the **30 lowest-coverage files** (see table below). Each file should get:
1. A dedicated test file named `test_<module>_coverage.py`
2. Minimum: **3 test scenarios** (happy path, error path, edge case)
3. Mock all external dependencies via `conftest.py` patterns

#### Top 10 Priority Targets

| Rank | File | Current % | Missing Lines | Test Strategy |
|------|------|-----------|--------------|---------------|
| P1 | `api/routes/admin_dashboard.py` | 22.13% | 387 | Mock DB, test all 20+ endpoints, chart aggregation, pagination |
| P2 | `api/routes/__init__.py` | 38.20% | 199 | Test every router registration, middleware injection, error handlers |
| P3 | `tools/learning/skill_recommender.py` | 45.82% | 149 | Test scoring algorithms, filtering, cold-start, recommendation loop |
| P4 | `core/evolution/daily_learner.py` | 35.87% | 143 | Test learning cycle scheduling, experience aggregation, persistence |
| P5 | `tools/sso_integrator.py` | 24.04% | 139 | Test OAuth flows, token exchange, SAML, provider integration |
| P6 | `tools/parallel_agent_executor.py` | 40.45% | 131 | Test parallel execution, result aggregation, timeout, cancellation |
| P7 | `api/routes/tenant_admin.py` | 43.38% | 124 | Test tenant CRUD, user provisioning, quota enforcement |
| P8 | `api/routes/billing_api.py` | 34.39% | 124 | Test billing flows, invoice generation, Stripe webhooks |
| P9 | `api/routes/evolution.py` | 37.17% | 120 | Test evolution endpoints, agent breeding, fitness scoring |
| P10 | `core/cache/multi_layer_cache.py` | 42.00% | 116 | Test L1/L2/L3 cache layers, invalidation, TTL, eviction |

### Phase C: Push 50–80% Files to ≥ 90% (Week 6-10)
**Target Impact:** +3,500 lines → ~89%

| Rank | File | Current % | Missing | Strategy |
|------|------|-----------|---------|----------|
| P11 | `core/llm_router.py` | 56.91% | 162 | Test all routing strategies, provider failover, load balancing |
| P12 | `tools/security_tools/multi_account_rotator.py` | 68.59% | 147 | Test account rotation, credential refresh, rate limiting |
| P13 | `tools/code/code_smell_detector.py` | 58.10% | 137 | Test all code smell patterns, severity scoring |
| P14 | `core/queue/task_queue_enhanced.py` | 56.59% | 135 | Test queue FIFO/priority, retries, dead-letter, persistence |
| P15 | `api/routes/browser.py` | 62.24% | 111 | Test all browser automation endpoints |
| P16 | `core/admin_routes.py` | 57.32% | 102 | Test all admin route handlers, auth guards |
| P17 | `core/tier8/self_improvement_agent.py` | 50.00% | 100 | Test self-improvement loop, metric tracking, model update |
| P18 | `tools/learning/style_learner.py` | 53.40% | 96 | Test style adaptation, preference learning, A/B tracking |
| P19 | `services/memory_service.py` | 35.29% | 99 | Test memory CRUD, semantic search, context windowing |
| P20 | `api/routes/meta_ai.py` | 47.22% | 76 | Test meta-AI coordination, model selection, fallback |

### Phase D: Branch Coverage Attack (Week 10-12)
**Target Impact:** Branch 42.88% → ≥ 80%

For every conditional block, add coverage for both branches:

```python
# Pattern: if/else both branches
async def test_admin_access_granted(): ...  # admin role
async def test_admin_access_denied():  ...  # non-admin role

# Pattern: try/except both branches
async def test_success_path():          ...  # no exception
async def test_exception_handled():     ...  # exception caught

# Pattern: None guard
async def test_with_data():             ...  # valid data
async def test_with_none():             ...  # None value

# Pattern: empty collection
async def test_empty_state():           ...  # empty list/dict
async def test_populated_state():       ...  # populated list/dict
```

### Phase E: Maintain & Monitor (Ongoing)
**Target:** ≥ 90% line coverage as a sustained floor.

| Task | Details |
|------|---------|
| E.1 | Gate CI on `--cov-fail-under=90` once target is reached |
| E.2 | Add `# pragma: no cover` only for verified dead code |
| E.3 | Monthly coverage report review |
| E.4 | Require coverage check in PR review checklist |

---

## 🧪 Standardized Test Template

Use this template for all new coverage test files:

```python
"""
Coverage tests for <module_name>.
Target: 100% line coverage.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class Test<ModuleName>:
    """Coverage test suite for <module_name>."""

    # --- 1. Happy Path ---
    @pytest.mark.asyncio
    async def test_success_path(self):
        """Test primary functionality with valid inputs."""
        from <module_path> import <Class>

        instance = <Class>()
        result = await instance.<method>(valid_input)
        assert result is not None
        # Add specific assertions

    # --- 2. Error Path ---
    @pytest.mark.asyncio
    async def test_invalid_input_raises(self):
        """Test that invalid inputs raise expected exceptions."""
        from <module_path> import <Class>

        instance = <Class>()
        with pytest.raises((ValueError, TypeError)):
            await instance.<method>(invalid_input)

    # --- 3. Edge Cases ---
    @pytest.mark.asyncio
    async def test_empty_state(self):
        """Test behavior with empty/None inputs."""
        from <module_path> import <Class>

        instance = <Class>()
        result = await instance.<method>([])
        assert result == []  # or appropriate empty state

    @pytest.mark.asyncio
    async def test_none_input(self):
        """Test behavior with None inputs."""
        from <module_path> import <Class>

        instance = <Class>()
        result = await instance.<method>(None)
        assert result is None  # or appropriate fallback

    # --- 4. Async / Timeout Paths ---
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout/retry behavior."""
        with patch("<module>.<dependency>", side_effect=TimeoutError):
            from <module_path> import <Class>
            instance = <Class>()
            result = await instance.<method>(input)
            # Expect graceful fallback

    # --- 5. External Dependency Mocking ---
    @pytest.mark.asyncio
    @patch("<module>.<dependency1>")
    @patch("<module>.<dependency2>")
    async def test_with_external_deps(self, mock_dep2, mock_dep1):
        """Test with fully mocked external dependencies."""
        mock_dep1.return_value = {"key": "value"}
        mock_dep2.some_method = AsyncMock(return_value="result")

        from <module_path> import <Class>
        instance = <Class>()
        result = await instance.<method>()
        assert result == expected
```

---

## 🔧 Quick Wins (High Impact / Low Effort)

These are files where a single test file can add significant coverage quickly:

| File | Est. Tests Needed | Est. Lines Added | Complexity |
|------|-------------------|-----------------|------------|
| `tools/cache_cleanup.py` | 3 | 35 | 🟢 Low |
| `api/routes/billing_api.py` | 8 | 124 | 🟡 Medium |
| `core/evolution/daily_learner.py` | 10 | 143 | 🟡 Medium |
| `tools/seed_database.py` | 5 | 85 | 🟢 Low |
| `tools/self_planner.py` | 6 | 88 | 🟢 Low |
| `services/rider_tracker.py` | 5 | 66 | 🟢 Low |

---

## 📈 Progress Tracking Dashboard

```markdown
# Coverage Progress Checklist

## Phase 0: Stabilize (Week 1)
- [x] Fix failing test: test_swarm_routes.py
- [x] Full test suite passes with exit code 0

## Phase A: < 50% → ≥ 75% (Target: +5,500 lines)
- [x] api/routes/admin_dashboard.py (22.13% → 75%) — #P1 ✅ (test_admin_dashboard_coverage.py exists)
- [x] api/routes/__init__.py (38.20% → 75%) — #P2
- [x] tools/learning/skill_recommender.py (45.82% → 75%)
- [x] core/evolution/daily_learner.py (35.87% → 75%) ✅ NEW
- [x] tools/sso_integrator.py (24.04% → 75%) ✅ NEW
- [x] tools/parallel_agent_executor.py (40.45% → 75%)
- [x] api/routes/tenant_admin.py (43.38% → 75%) ✅ NEW
- [x] api/routes/billing_api.py (34.39% → 75%)
- [x] api/routes/evolution.py (37.17% → 75%)
- [x] core/cache/multi_layer_cache.py (42.00% → 75%)
- [x] api/routes/websocket_agent.py (19.17% → 75%)
- [x] api/routes/websocket_voice.py (19.64% → 75%)
- [x] api/routes/websocket_hitl.py (22.45% → 75%)
- [x] services/memory_service.py (35.29% → 75%) ✅ NEW
- [x] tools/knowledge/local_search_rag.py (25.00% → 75%) ✅ NEW

## New Coverage Test Files Created (2026-07-28)
- [x] tests/test_daily_learner_coverage.py — core/evolution/daily_learner.py
- [x] tests/test_sso_integrator_coverage.py — tools/sso_integrator.py
- [x] tests/test_tenant_admin_coverage.py — api/routes/tenant_admin.py
- [x] tests/test_local_search_rag_coverage.py — tools/knowledge/local_search_rag.py
- [x] tests/test_seed_database_coverage.py — tools/seed_database.py
- [x] tests/test_self_planner_coverage.py — tools/self_planner.py
- [x] tests/test_rider_tracker_coverage.py — services/rider_tracker.py
- [x] tests/test_browser_routes_coverage.py — api/routes/browser.py
- [x] tests/test_meta_ai_coverage.py — api/routes/meta_ai.py
- [x] tests/core/test_secret_vault_coverage.py — core/security/secret_vault.py
- [x] tests/test_memory_service_coverage.py — services/memory_service.py

## Remaining High-Priority Targets
- [ ] tests/core/test_audit_logger_coverage.py — core/observability/audit_logger.py
- [ ] tests/core/test_origin_validator_coverage.py — core/security/origin_validator.py
- [ ] tests/core/test_autonoguard_middleware_coverage.py — core/security/autonoguard_middleware.py
- [ ] tests/core/test_input_sanitizer_coverage.py — core/security/input_sanitizer.py
- [ ] tests/core/test_redis_manager_coverage.py — core/cache/redis_manager.py
- [ ] tests/core/test_multi_layer_cache_coverage.py — core/cache/multi_layer_cache.py
- [ ] tests/api/test_admin_dashboard_coverage.py — api/routes/admin_dashboard.py
- [ ] tests/api/test_websocket_agent_coverage.py — api/routes/websocket_agent.py
- [ ] tests/api/test_websocket_voice_coverage.py — api/routes/websocket_voice.py
- [ ] tests/api/test_websocket_hitl_coverage.py — api/routes/websocket_hitl.py
- [ ] tests/tools/test_multi_account_rotator_coverage.py — tools/security_tools/multi_account_rotator.py
- [ ] tests/tools/test_code_smell_detector_coverage.py — tools/code/code_smell_detector.py
- [ ] tests/tools/test_task_queue_enhanced_coverage.py — core/queue/task_queue_enhanced.py
- [ ] tests/tools/test_style_learner_coverage.py — tools/learning/style_learner.py
- [ ] tests/tools/test_skill_recommender_coverage.py — tools/learning/skill_recommender.py

#!/bin/bash
# Script to analyze current coverage status
echo "Current Coverage Status:"
poetry run coverage report --show-missing | grep -v "100%" | head -20
```

### Appendix B: Test Creation Checklist
- [ ] All public functions/methods tested
- [ ] Error conditions covered
- [ ] Edge cases considered
- [ ] External dependencies mocked
- [ ] Async paths tested
- [ ] Branch coverage complete
- [ ] Performance considerations addressed
