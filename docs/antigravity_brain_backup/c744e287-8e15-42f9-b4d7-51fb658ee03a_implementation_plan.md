# Implementation Plan — Security & Quality Hotfixes

This plan addresses several security, configuration, and code quality issues identified in the repository:

1. **Security Vulnerabilities (Critical)**: hardcoded credentials in env files, blackbox configuration, and Firebase logs.
2. **Version Control Compliance**: explicit additions to `.gitignore`.
3. **Firebase Schema Warnings**: fix `firebase.json`'s functions config properties.
4. **Code Quality & Paths**: clean up `sys.path` hacks and make ChromaDB storage path configurable.
5. **Robust Error Handling**: prevent infinite retry loops in AI response requests.

---

## Proposed Changes

### Configuration & Security

#### [MODIFY] [.env.local](file:///c:/Users/n/supremeai/supremeai_2.0/.env.local)
- Remove the hardcoded `VERCEL_OIDC_TOKEN` value and replace it with a placeholder.

#### [MODIFY] [.env.development](file:///c:/Users/n/supremeai/supremeai_2.0/.env.development)
- Replace the exposed database password with a placeholder or configurable reference.

#### [MODIFY] [blackbox_mcp_settings.json](file:///c:/Users/n/supremeai/supremeai_2.0/blackbox_mcp_settings.json)
- Replace the hardcoded LaunchDarkly API key with the placeholder `"YOUR_LAUNCHDARKLY_API_KEY_HERE"`.

#### [DELETE] [firebase-debug.log](file:///c:/Users/n/supremeai/supremeai_2.0/firebase-debug.log)
- Delete the file entirely to purge the exposed OAuth access tokens and emails from the local tree.

#### [MODIFY] [.gitignore](file:///c:/Users/n/supremeai/supremeai_2.0/.gitignore)
- Add explicit entries for `.env*`, `*.log`, `firebase-debug.log`, `blackbox_mcp_settings.json`, `__pycache__/`, and `.venv/` to ensure they are never tracked in Git, even if someone tries to add them manually.

#### [MODIFY] [firebase.json](file:///c:/Users/n/supremeai/supremeai_2.0/firebase.json)
- Ensure the `functions` property matches the expected Firebase schema (since the logs show past validation issues with `"region"` or type requirements).

---

### Backend Configuration

#### [MODIFY] [backend/core/config.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/config.py)
- Add a configurable `chromadb_path` settings field with a default of `"supremeai_knowledge_base"`.

---

### Scripts & Tooling

#### [MODIFY] [scripts/knowledge_indexer.py](file:///c:/Users/n/supremeai/supremeai_2.0/scripts/knowledge_indexer.py)
- Import `settings` from `backend.core.config` and use `settings.chromadb_path` instead of hardcoding `DB_PATH`.
- Fix paths dynamically (with clean absolute import fallback).

#### [MODIFY] [ask_scribe.py](file:///c:/Users/n/supremeai/supremeai_2.0/ask_scribe.py)
- Use `settings.chromadb_path` instead of hardcoded `DB_PATH`.
- Remove `# ruff: noqa: E402, F821` by placing all imports cleanly at the top of the file and resolving the path dynamically.

#### [MODIFY] [ai_scribe_historian.py](file:///c:/Users/n/supremeai/supremeai_2.0/ai_scribe_historian.py)
- Clean up imports to remove `sys.path.insert(0, ...)` hacks using absolute-to-relative try/except fallbacks.
- Update `get_ai_response()` retry logic: do not retry on unrecoverable errors (like 403, permission denied, invalid keys, etc.) and restrict `litellm.retry_strategy` to transient errors only.

---

## Verification Plan

### Automated Tests
- Run `pytest` on existing backend core/smoke tests to ensure no configuration validation regressions are introduced.
- Run `python scripts/knowledge_indexer.py` (dry run or verification) and `python ask_scribe.py --help` to ensure they execute without path or configuration issues.

### Manual Verification
- Check `git status --ignored` after the cleanups to confirm the target files are properly ignored.
- Run a dry-run check of the linter on updated files.
