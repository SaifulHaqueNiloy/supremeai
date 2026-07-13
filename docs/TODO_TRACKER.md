# SupremeAI 2.0 Master TODO Tracker

This document is the **single source of truth** for all unfinished tasks, architectural debt, and planned features across the SupremeAI project. It has been strictly audited to remove zombie/completed tasks from old lists.

## 🚨 P0 - Critical Security & Auth (Fatal Mistakes Mitigation)
- [ ] **MANUAL: Key Rotation:** Access the Render Dashboard and immediately rotate (change/delete) any exposed API Keys.
- [x] **MANUAL: Git History Scrubbing:** Run `git filter-repo` to permanently remove leaked secrets from git history, followed by `git push --force`.
- [x] **Implement Actual Frontend RBAC:** Replace mocked `TODO: Phase 3 - Implement RBAC check here` in `AdminShell.tsx` with real role-based checks.
- [x] **VS Code Extension Auth:** Connect the VS Code extension to the backend for real user authentication and API key management (currently mocked).
- [ ] **Admin Login Token:** Fix the vulnerability where the plain password is used as the JWT token. *(Note: pending investigation on frontend side)*

## 🛠️ P1 - High Priority (Infrastructure & Logic Fixes)
- [ ] **Write Core Tests:** Increase coverage from 38% to 90%. Focus on `telemetry.py`, `universal_rules.py`, `upstash_redis_queue.py`, and brain modules.
- [ ] **Test Coverage Automation:** Update `--cov-fail-under=38` to `90` in CI/CD pipeline (`supreme-core-ci.yml`) once tests are written.
- [ ] **Infrastructure as Code (IaC):** Implement Terraform for Firebase/GCP resources.

## 🏗️ P2 - Medium Priority (Feature Debt & UI)
- [ ] **Semantic Memory:** Update `memory/supabase_store.py` to use actual `pgvector` semantic similarity search instead of the current `ilike` substring mock.
- [ ] **Sliding Window Summary Tree:** Implement in `memory/sliding_window.py`.
- [ ] **Language Detection Routing:** Implement language routing for GLM-5 / Yi-34B.
- [ ] **Knowledge Base:** Integrate seed data (DevOps, API, Practices) into a searchable knowledge base.
- [ ] **Fake/Hardcoded Users in Auth:** Remove mock user data in UI.
- [ ] **Bilingual Codebase:** Resolve the bilingual codebase comments to ensure international scalability, or fully commit to one language standard.
- [ ] **CICDVisualizer Static Data:** Replace mock data with live CI metrics in frontend.
- [x] **ActionCard Fake Execution:** Remove mock execution logic in frontend components.

## 🔮 P3 - Low Priority / Future Enhancements
- [ ] **Frontier Quality Replication:** Integrate o1/R1 reasoning and Perplexity search.
- [ ] **Edge Computing:** Utilize Cloudflare Workers for ultra-low latency.
- [ ] **Bengali TTS Full Offline:** Integrate Coqui TTS for offline voice support.
- [ ] **Clean Up `fix_dups.py`:** Remove script once AI Scribe duplicate docstring issues are permanently fixed.
- [ ] **Deprecated `on_event("shutdown")`:** Replace with `lifespan` context manager in FastAPI.
- [ ] **Deprecated `datetime.utcnow()`:** Replace with `datetime.now(datetime.UTC)`.
- [ ] **Clean Up Scattered Scripts:** Consolidate redundant maintenance scripts.

---
*Last Audited: July 2026. (Removed over 10 falsely pending P0/P1 tasks such as hardcoded JWT secrets, weak bypasses, and mutable default bugs which were already fixed in codebase).*
