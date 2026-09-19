# Architecture & Dependency Audit — SupremeAI
**Domains:** 03 Architecture, 21 Config Lifecycle | **Last Scan:** 2026-09-19

## Layer Violations (3 confirmed)

**Rule:** `core → services → api` (one-way). `core` must NEVER import `api`.

| File | Violation | Fix |
|---|---|---|
| `core/admin_routes.py` | `from api.*` import | Move this file → `api/routes/admin_routes.py` |
| `core/app.py` | `from api.*` import | This is an app factory — belongs in `api/` or root |
| `core/observability/observability_middleware.py` | `from api.*` import | Extract shared interface to `core/`, keep middleware in `middleware/` |

## Config Lifecycle Violation (Domain 21)

```
12 config files overlap:
config_validator.py      ← validates boot
env_validator.py         ← also validates boot (duplicate!)
config.py                ← Pydantic Settings singleton
config_fields.py         ← field declarations (36KB!)
config_secrets.py        ← secret properties (42KB, has 13 duplicate defs)
config_validation.py     ← Pydantic validators
config_classification.py ← 90KB of metadata!
config_control_plane.py  ← health snapshot
config_cache.py          ← TTL cache
config_proxy.py          ← tenant proxy
config_registry.py       ← ConfigDefinition + REGISTRY
config_service.py        ← L1–L4 service
```

**Target State (from SOFTWARE_ENGINEERING_EXCELLENCE_PLAN.md):**
```
4 files after consolidation:
config_registry.py  ← single source of truth
config.py           ← Settings singleton
config_cache.py     ← TTL cache
config_service.py   ← L1-L4 service
```

## God Modules (Need Decomposition)

| Module | Files | Problem |
|---|---|---|
| `core/` | 468 Python files | Far too large — mixes concerns |
| `config_classification.py` | 90KB single file | Auto-generate from registry |
| `config_fields.py` | 36KB single file | Split by domain |
| `config_secrets.py` | 42KB single file | Split by provider |
| `worker_service.py` | 28KB single file | Decompose into workers/ |
| `app_builder.py` | 30KB single file | Split middleware registration |

## Circular Import Risk

`intent_router.py` → imports `unified_router` → imports `intent_router_v2` → imports `intent_router`

**Fix:** Make `intent_router.py` a pure shim with no circular dependency:
```python
# intent_router.py (shim only)
from core.intent_router_v2 import IntentRouterV2, PromptAction, ACTION_PATTERNS  # noqa: F401
```
