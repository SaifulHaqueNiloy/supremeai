# backend/ — File Index
> AI: পুরো ফোল্ডার স্ক্যান না করে এই index পড়ুন। প্রয়োজনীয় ফাইলটি খুঁজে সরাসরি যান।

## Entry Points
| File | কী করে |
|---|---|
| `main.py` | FastAPI app entry point, server startup |
| `core/app.py` | App factory, middleware registration |
| `core/lifespan.py` | Startup/shutdown lifecycle handlers |
| `core/config.py` | All environment settings (Pydantic Settings) |

## Key Directories
| Directory | কী আছে |
|---|---|
| `core/` | App config, middleware, LLM router, health check, security — **সবচেয়ে গুরুত্বপূর্ণ** |
| `api/` | Route handlers — `v1/`, `routes/`, dependencies |
| `services/` | Business logic — memory, LLM, billing, vision, sandbox |
| `models/` | SQLAlchemy DB models |
| `schemas/` | Pydantic request/response schemas |
| `tests/` | pytest test suite |
| `agents/` | AI agent implementations |
| `workers/` | Background task workers |
| `memory/` | Vector memory + context management |

## Core Files (Most Edited)
| File | কী করে |
|---|---|
| `core/config.py` | Settings class — সব env vars এখানে |
| `core/config_secrets.py` | Secret loading from Infisical/env |
| `core/universal_rules.py` | Global business rules (24KB) |
| `core/llm_router.py` | LLM provider routing logic |
| `core/router.py` | Main API router registration |
| `core/health_check.py` | `/health` endpoint logic |
| `core/security/` | JWT, auth, RBAC |
| `core/cost_guard.py` | $0 cost enforcement, budget tracking |
| `services/memory_service.py` | AI memory read/write (19KB) |
| `services/llm/` | LLM abstraction layer |

## Tests
```bash
cd backend && poetry run pytest          # all tests
cd backend && poetry run pytest tests/   # specific folder
```
