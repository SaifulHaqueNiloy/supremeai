# SupremeAI 2.0 - Comprehensive Improvement Plan

## Priority 1: 🔴 Secret Vault Empty String Fix ✅
- [x] Fix `backend/core/config.py` - `_get_cached_secret` now logs warning when key not in cache
- [x] Add proper empty string vs "not found" distinction with warning logging

## Priority 2: 🔴 AST Sandbox getattr/hasattr Bypass Prevention ✅
- [x] Created `backend/core/security/ast_sandbox_scanner.py` with full AST sandbox scanner
- [x] Integrated into `backend/sandbox/file_isolation_gate.py` with validate_code_for_sandbox
- [x] Integrated into `backend/core/microvm_sandbox.py` (execute_async, all run methods, execute_code_securely)

## Priority 3: 🟠 SSRF Prevention Centralization ✅
- [x] Created `backend/core/security/ssrf_protection.py` with complete SSRF protection (DNS cache, metadata blocking, DNS rebinding check, blocklist/allowlist)
- [x] Updated `backend/core/security/__init__.py` is_safe_url() to delegate to centralized SSRF module
- [x] Backward-compatible — all existing callers (`web_scraper.py`, `browser_agent.py`, etc.) continue to work via delegation

## Priority 4: 🟠 TODO/FIXME Management System ✅
- [x] Create `scripts/devops/todo_manager.py` - scan, categorize, track TODO/FIXME tags
- [x] Add CLI commands for reporting (CLI, Markdown, JSON formats)

## Priority 5: 🟡 Structured Logging Implementation
- [ ] Create `backend/core/logging/` module with correlation ID support
- [ ] Add structured logging to middleware and key modules

## Priority 6: 🟡 Magic Numbers Elimination
- [ ] Scan and parameterize hardcoded values into `backend/core/config.py`

## Priority 7: 🟡 Cache Optimization
- [ ] Add TTL-based expiry for L1 local cache in `redis_manager.py`
- [ ] Improve `MultiLevelCache` implementation

## Priority 8: 🔵 Import Optimization ✅
- [x] Move `import json` inside validators to top-level imports (completed in `parse_comma_separated_list`, `parse_list_fields`, `parse_dict_fields`, `parse_cors_origins`)
- [ ] Remove unused imports across the codebase

## Priority 9: 🔵 Bangla Comment English Translation
- [ ] Add English translations alongside existing Bangla comments in key files
