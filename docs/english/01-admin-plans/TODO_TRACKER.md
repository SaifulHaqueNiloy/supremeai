# SupremeAI 2.0 Master TODO Tracker

This document is the **single source of truth** for all unfinished tasks, architectural debt, and planned features across the SupremeAI project. All pending items from legacy TODO files have been consolidated here.

---

## 🚨 P0 - Critical Security & Auth (Fatal Mistakes Mitigation)
- [ ] **MANUAL: Key Rotation:** Access the Render Dashboard and immediately rotate (change/delete) any exposed API Keys.
- [x] **MANUAL: Git History Scrubbing:** Run `git filter-repo` to permanently remove leaked secrets from git history, followed by `git push --force`.
- [x] **Implement Actual Frontend RBAC:** Replace mocked `TODO: Phase 3 - Implement RBAC check here` in `AdminShell.tsx` with real role-based checks.
- [x] **VS Code Extension Auth:** Connect the VS Code extension to the backend for real user authentication and API key management (currently mocked).
- [ ] **Admin Login Token:** Fix the vulnerability where the plain password is used as the JWT token. *(Note: pending investigation on frontend side)*

---

## 🛠️ P1 - High Priority (Infrastructure & Logic Fixes)
- [ ] **Write Core Tests:** Increase coverage from 38% to 90%. Focus on `telemetry.py`, `universal_rules.py`, `upstash_redis_queue.py`, and brain modules.
- [ ] **Test Coverage Automation:** Update `--cov-fail-under=38` to `90` in CI/CD pipeline (`supreme-core-ci.yml`) once tests are written.
- [ ] **Infrastructure as Code (IaC):** Implement Terraform for Firebase/GCP resources.

### Backend Test Suite (from `backend/TODO.md`)
- [ ] **B.1** `tests/api/test_admin_analytics.py`
- [ ] **B.2** `tests/api/test_swarm_routes.py`
- [ ] **B.3** `tests/api/test_billing_email.py`
- [ ] **B.4** `tests/api/test_websocket_routes.py`
- [ ] **C.1** `tests/memory/test_unified_db.py`
- [ ] **C.2** `tests/memory/test_rag_memory.py`
- [ ] **C.3** `tests/memory/test_storage_adapters.py`
- [ ] **D.1** `tests/tools/test_mcp_devops.py`
- [ ] **D.2** `tests/tools/test_knowledge_tools.py`
- [ ] **D.3** `tests/tools/test_learning_engine.py`
- [ ] **D.4** `tests/tools/test_media_voice.py`
- [ ] **D.5** `tests/tools/test_security_rotators.py`
- [ ] **E.1** Configure `--cov-fail-under=80` in CI
- [ ] **E.2** Generate auto test cases for zero-coverage files

### Coverage 90% Plan (from `backend/TODO_Coverage_90.md`)
- [ ] **Phase 1:** Fix Cache Cleanup Test (Dynamic Import → Normal Import)
- [ ] **Phase 2:** Extend Admin Dashboard Tests (`test_admin_dashboard_full.py`)
  - Add `impersonate_user`, `emergency_deploy`, `trigger_backup`, `get_feature_flags`, `get_full_data_export`, `run_security_scan`, `admin_websocket`, `execute_manual_gate_override`, `get_ci_logs`, `get_events`, `get_roles`/`get_permissions`, Workspace CRUD, Settings CRUD, Sessions/Customers, `require_admin_token`/`admin_rate_limit` tests
- [ ] **Phase 3:** Extend API Keys Tests (`test_api_keys_coverage.py`)
  - Add `list_all_keys`, `get_key`, `delete_key`, `key_usage`/`key_stats`, `record_usage_hook`, `quota_alert`, `bulk_delete`, wrapper function tests
- [ ] **Phase 4:** Create `tests/test_sso_integrator_coverage.py`
- [ ] **Phase 5:** Extend LLM Router Tests (`test_llm_router.py`) - failover, weights, cost-sensitive ordering
- [ ] **Phase 6:** Create `tests/test_api_routes_init.py`
- [ ] **Final Verification:** Run full test suite and coverage report

### Test Fixes (from `docs/archived_reports/TODO.md`)
- [ ] **Step 2:** Fix `test_config_cache.py` failures (`test_config_cache_get_fallback`, `test_config_cache_set_and_invalidate`)
- [ ] **Step 3:** Fix `test_health.py` tests (rewrite without module reload, remove `@pytest.mark.skip`)
- [ ] **Step 4:** Fix `test_celery_app.py` AttributeError
- [ ] **Step 5:** Fix `test_code_validator.py` async function test
- [ ] **Step 6:** Fix RBAC and assertion failures (`test_rbac.py`, `test_provider_failover_chain.py`)
- [ ] **Step 7:** Fix telemetry test failures (update mock structure)
- [ ] **Step 8:** Run full test suite and verify fixes

### Phase 2 Improvements (from `docs/archived_reports/PHASE2_TODO.md`)
- [ ] **Task 1:** Database Connection Pool Unification - `UnifiedPoolManager` class
- [ ] **Task 3:** Deployment Platform Consolidation - Document Netlify/Cloudflare Worker removal
- [ ] **Task 5:** Config Layer Simplification - Split `backend/core/config.py` into sub-modules
- [ ] **Task 6:** Test Coverage 60% → 75% - Core, API, Security, Cache module tests

### Phase 3 Improvements (from `docs/archived_reports/PHASE3_TODO.md`)
- [ ] **Task 5:** SQL Injection Prevention - ORM migration helper, input sanitization utility, query inspection layer
- [ ] **Task 6:** API Documentation Improvement - Pydantic response examples, OpenAPI tags, changelog

### Phase 4 Improvements (from `docs/archived_reports/PHASE4_TODO.md`)
- [ ] **Task 1:** Config Layer Refactoring - Split `backend/core/config.py` into sub-modules
- [ ] **Task 2:** Import Optimization - `TYPE_CHECKING` blocks, `from __future__ import annotations`, lazy imports
- [ ] **Task 3:** Event Bus Enhancement - DLQ, retry mechanism, event sourcing, validation schema

---

## 🏗️ P2 - Medium Priority (Feature Debt & UI)
- [ ] **Semantic Memory:** Update `memory/supabase_store.py` to use actual `pgvector` semantic similarity search instead of the current `ilike` substring mock.
- [ ] **Sliding Window Summary Tree:** Implement in `memory/sliding_window.py`.
- [ ] **Language Detection Routing:** Implement language routing for GLM-5 / Yi-34B.
- [ ] **Knowledge Base:** Integrate seed data (DevOps, API, Practices) into a searchable knowledge base.
- [ ] **Fake/Hardcoded Users in Auth:** Remove mock user data in UI.
- [ ] **Bilingual Codebase:** Resolve the bilingual codebase comments to ensure international scalability, or fully commit to one language standard.
- [ ] **CICDVisualizer Static Data:** Replace mock data with live CI metrics in frontend.
- [x] **ActionCard Fake Execution:** Remove mock execution logic in frontend components.

---

## 🔮 P3 - Low Priority / Future Enhancements
- [ ] **Frontier Quality Replication:** Integrate o1/R1 reasoning and Perplexity search.
- [ ] **Edge Computing:** Utilize Cloudflare Workers for ultra-low latency.
- [ ] **Bengali TTS Full Offline:** Integrate Coqui TTS for offline voice support.
- [ ] **Clean Up `fix_dups.py`:** Remove script once AI Scribe duplicate docstring issues are permanently fixed.
- [ ] **Deprecated `on_event("shutdown")`:** Replace with `lifespan` context manager in FastAPI.
- [ ] **Deprecated `datetime.utcnow()`:** Replace with `datetime.now(datetime.UTC)`.
- [ ] **Clean Up Scattered Scripts:** Consolidate redundant maintenance scripts.

### Improvement Plan Items (from `docs/archived_reports/IMPROVEMENT_PLAN_TODO.md`)
- [ ] **Priority 5:** Structured Logging - Create `backend/core/logging/` module with correlation ID support
- [ ] **Priority 6:** Magic Numbers Elimination - Scan and parameterize hardcoded values
- [ ] **Priority 7:** Cache Optimization - TTL-based expiry for L1 local cache
- [ ] **Priority 8 (partial):** Remove unused imports across codebase
- [ ] **Priority 9:** Bangla Comment English Translation

---

## 📋 Legacy Phase Trackers (Consolidated Status)

### Phase 2 Status (from `backend/audit_progress.md` / `PHASE2_TODO.md`)
- [x] Task 2: Caching Strategy Optimization (L1 TTL) - **COMPLETE**
- [x] Task 4: Import Optimization (lazy loading) - **COMPLETE**
- [x] Task 7: Strip Webhook Trace Leak Fix - **COMPLETE**
- [ ] Task 1: Database Connection Pool Unification
- [ ] Task 3: Deployment Platform Consolidation
- [ ] Task 5: Config Layer Refactoring
- [ ] Task 6: Test Coverage 60% → 75%

### Phase 3 Status (from `PHASE3_TODO.md`)
- [x] Task 1: Database Query Optimization (N+1 prevention) - **COMPLETE**
- [x] Task 2: Memory Management - **COMPLETE**
- [x] Task 3: Structured Logging (Phase 1) - **COMPLETE**
- [x] Task 4: Secret Scanning Automation - **COMPLETE**
- [x] Task 5: SQL Injection Prevention - **COMPLETE**
- [x] Task 7: Strip Webhook Trace Leak Fix (Phase 2 verified) - **COMPLETE**
- [ ] Task 6: API Documentation Improvement

### Phase 4 Status (from `PHASE4_TODO.md`)
- [ ] Task 1: Config Layer Refactoring
- [ ] Task 2: Import Optimization Completion
- [ ] Task 3: Event Bus Enhancement

---

*Last Audited: July 2026. All pending items from legacy TODO files have been consolidated into this master tracker. Completed items remain documented for reference.*