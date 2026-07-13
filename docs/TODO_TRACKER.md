# SupremeAI 2.0 Central TODO Tracker

This document centralizes the major technical debt, unfinished features, and architecture gaps scattered across the codebase.

## High Priority (Fatal Mistakes Mitigation)
- [ ] Implement actual RBAC (Role-Based Access Control) in the frontend instead of the mocked `TODO: Phase 3 - Implement RBAC check here` in `AdminShell.tsx`.
- [ ] Connect the VS Code extension to the backend for real user authentication (currently mocked).
- [ ] Ensure the memory system (Supabase pgvector) handles semantic search correctly instead of relying on placeholders.
- [ ] Fix the testing coverage. Basic unit test coverage is 38%. We need to increase coverage for core modules (e.g., `telemetry.py`, `universal_rules.py`).

## Medium Priority (Feature Debt)
- [ ] `AutocacheProxy`: Either implement semantic caching and request deduplication or remove the claims.
- [ ] Resolve the bilingual codebase comments to ensure international scalability, or fully commit to one language standard in code documentation.
- [ ] Clean up redundant scripts in `scripts/` and `.github/scripts/`.

## Low Priority
- [ ] Clean up `fix_dups.py` once AI Scribe duplicate docstring issues are fundamentally fixed.
- [ ] Organize all other inline `TODO:` comments into GitHub Issues.
