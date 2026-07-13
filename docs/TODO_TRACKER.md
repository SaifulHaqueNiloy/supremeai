# SupremeAI 2.0 Master TODO Tracker

This document is the **single source of truth** for all unfinished tasks, architectural debt, and planned features across the SupremeAI project. It consolidates previous scattered checklists (`MANUAL_TASKS_TODO.md`, `todo-audit-gaps.md`, `master_work_todo_list.md`, `actionable_checklist.md`).

## 🚨 P0 - Critical Security & Auth (Fatal Mistakes Mitigation)
- [ ] **Implement Actual Frontend RBAC:** Replace mocked `TODO: Phase 3 - Implement RBAC check here` in `AdminShell.tsx` with real role-based checks.
- [ ] **VS Code Extension Auth:** Connect the VS Code extension to the backend for real user authentication and API key management (currently mocked).
- [ ] **Hardcoded JWT Secret Key:** Remove fallback secrets in `app.py` and `auth_middleware.py`.
- [ ] **Admin Login Token:** Fix the vulnerability where the plain password is used as the JWT token.
- [ ] **Auth Route Prefix Conflict:** Resolve `/auth` prefix conflict in `email.py` vs `/integrations/email`.
- [ ] **Weak Token Bypass:** Remove `"test-token"` bypass logic in `auth_middleware.py`.

## 🛠️ P1 - High Priority (Infrastructure & Logic Fixes)
- [ ] **Test Coverage Automation:** Add `--cov-fail-under=90` to CI/CD pipeline for coverage enforcement.
- [ ] **Write Core Tests:** Increase coverage from 38% to 90%. Focus on `telemetry.py`, `universal_rules.py`, `upstash_redis_queue.py`, and brain modules.
- [ ] **Config Duplicate:** Resolve the split between `backend/config.py` and `core/config.py`.
- [ ] **Mutable Default Bug:** Fix `field(default_factory=...)` in `Experience` model.
- [ ] **Non-Async Endpoints:** Fix `stream_chat` & `get_completion` lacking `async def`.
- [ ] **OTP Crash:** Fix `otp.strip()` NoneType crash.
- [ ] **Infrastructure as Code (IaC):** Implement Terraform for Firebase/GCP resources.

## 🏗️ P2 - Medium Priority (Feature Debt & UI)
- [ ] **Self-Evolution Engine:** Complete full logic in `core/evolution_engine.py` + `evolution/auto_skill_creator.py`.
- [ ] **Semantic Memory:** Ensure `memory/supabase_store.py` (Supabase pgvector) handles semantic search correctly instead of relying on placeholders.
- [ ] **Sliding Window Summary Tree:** Implement in `memory/sliding_window.py`.
- [ ] **Language Detection Routing:** Implement language routing for GLM-5 / Yi-34B.
- [ ] **Knowledge Base:** Integrate seed data (DevOps, API, Practices) into a searchable knowledge base.
- [ ] **Fake/Hardcoded Users in Auth:** Remove mock user data in UI.
- [ ] **Bilingual Codebase:** Resolve the bilingual codebase comments to ensure international scalability, or fully commit to one language standard.
- [ ] **CICDVisualizer Static Data:** Replace mock data with live CI metrics in frontend.
- [ ] **ActionCard Fake Execution:** Remove mock execution logic in frontend components.

## 🔮 P3 - Low Priority / Future Enhancements
- [ ] **Frontier Quality Replication:** Integrate o1/R1 reasoning and Perplexity search.
- [ ] **Edge Computing:** Utilize Cloudflare Workers for ultra-low latency.
- [ ] **Bengali TTS Full Offline:** Integrate Coqui TTS for offline voice support.
- [ ] **Clean Up `fix_dups.py`:** Remove script once AI Scribe duplicate docstring issues are permanently fixed.
- [ ] **Deprecated `on_event("shutdown")`:** Replace with `lifespan` context manager in FastAPI.
- [ ] **Deprecated `datetime.utcnow()`:** Replace with `datetime.now(datetime.UTC)`.
- [ ] **Clean Up Scattered Scripts:** Consolidate redundant maintenance scripts.
