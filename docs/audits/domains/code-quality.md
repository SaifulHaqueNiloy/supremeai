# Code Quality Audit — SupremeAI
**Domains:** 01 Conflict, 02 DRY, 04 Dead Code | **Last Scan:** 2026-09-19

## Domain 01 — Conflict & Mismatch (24 issues)
→ See full report: `codebase_conflict_audit.md` (in brain artifacts)

### Top 5 Unresolved Critical
1. `config_secrets.py` — 13 duplicate `@property` definitions (C-01)
2. `retry_handler.py` — duplicate `decorator()` function (C-03)
3. `mcp_policy.py` — duplicate `evaluate()` method (C-04)
4. `CRITICAL` severity constant: `int 3` vs `str "critical"` in 12 files (H-04)
5. `CircuitBreaker` state strings: `"open"` vs `"OPEN"` incompatible (H-05)

## Domain 02 — DRY & Duplication

### Backend
| Violation | Files | Lines |
|---|---|---|
| 12 overlapping config files | config*.py (12 files) | ~3,500 |
| 3 CircuitBreaker implementations | circuit_breaker.py × 3 | ~400 |
| 4 router implementations | intent_router, intent_router_v2, unified_router, llm_router | ~1,600 |
| CORS parsing (4 implementations) | config_validation.py + config_fields.py | ~120 |
| DB session factory (multiple) | db.py, database/, services/ | ~80 |

### Frontend
| Violation | Files | Lines |
|---|---|---|
| 3 HTTP implementations | apiClient.ts, api.ts, apiInterceptor.ts | ~950 |
| 3 backend URL env vars | VITE_API_BASE, VITE_API_URL, VITE_BACKEND_URL | ~30 |
| Idempotency injection 3x | post(), put(), patch() in apiClient.ts | ~60 |

## Domain 04 — Dead Code & Orphan Files

### Stub Files (82 total, <5 real lines)
```
Priority: VERIFY and KEEP or DELETE
```

**Likely safe to keep (legitimate __init__.py):**
- `core/agents/__init__.py` (0 lines) — package marker
- `core/errors/__init__.py` (0 lines) — package marker
- `alembic_migrations/__init__.py` (0 lines) — required

**Need investigation (non-__init__ stubs):**
- `api/routes/dock_actions.py` (3 real lines) — route file with 3 lines? Stub?
- `brain/agent_departments.py` (2 lines) — unimplemented?
- `brain/langgraph_agent.py` (2 lines) — placeholder?
- `byoc/__init__.py` (0 lines) — is BYOC module live or scaffolded?

### Deprecated-Named Files
| File | Action |
|---|---|
| `api/routes/admin_v1.py` | Is there admin_v2? If yes, delete v1 or mark deprecated |
| `core/intent_router_v2.py` | v2 is now canonical — rename to `intent_router.py`, delete old |
| `tests/agents/test_telegram_bot_v2.py` | Is v1 test deleted? Verify |

### Root-Level Test Files (should be in tests/)
In `backend/` root:
- `test_capabilities.py`
- `test_db.py`
- `test_imports.py`

→ Move to `tests/smoke/` or `tests/core/`.
