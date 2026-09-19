# Frontend Bundle & Observability Audit — SupremeAI
**Domains:** 11 Frontend Bundle, 15 Observability | **Last Scan:** 2026-09-19

## Domain 11 — Frontend Bundle

### Heavy Dependencies (Not Lazy-Loaded)
| Package | Size Estimate | Issue | Fix |
|---|---|---|---|
| `monaco-editor@0.55.1` | ~1MB+ gzipped | In main chunk — loads on every page | Route-level lazy load in IDE route only |
| `@xyflow/react@12.11.2` | ~300KB | Loads on every page | Lazy load in agent/workflow routes |
| `recharts@3.10.1` | ~200KB | Charts loaded globally | Lazy load in dashboard routes |
| `@webcontainer/api` | Large | WebContainer for browser IDE | Lazy load in IDE-specific feature |
| `framer-motion@12.43.0` | ~100KB | Animation lib globally loaded | Use CSS animations where possible |
| `xterm@5.3.0` + `@xterm/addon-fit` | ~150KB | Terminal | Lazy load in terminal feature |

**Target:** First-load bundle < 200KB gzipped (currently estimated 600KB+)

### Duplicate Risk
- `dexie` + `dexie-react-hooks` — local IndexedDB. Is this used alongside `localFirstDb.ts`?
- `@upstash/redis` in frontend — Redis client in browser? Security risk — should be backend only.

### Lazy Loading Pattern
```typescript
// ✅ Correct — IDE only loads when user goes to IDE route
const IDEPage = lazy(() => import('./pages/IDEPage'));
const MonacoEditor = lazy(() => import('@monaco-editor/react'));
```

## Domain 15 — Observability

### API Files Missing Correlation ID (32 files)
Top priority files (high-traffic routes):
- `api/routes/auth.py` — auth endpoint, NO correlation ID
- `api/routes/agent.py` — agent execution, NO logging at all
- `api/routes/agent_tasks.py` — task endpoint, NO logging
- `api/routes/analytics.py` — analytics, NO logging
- `api/routes/async_task_router.py` — async tasks, NO logging
- `api/deps.py` — dependency injection, NO logging

### Fix Pattern
```python
# Add to every router:
from core.request_context import get_correlation_id

@router.post("/endpoint")
async def handler(request: Request):
    corr_id = get_correlation_id(request)  # X-Request-ID or generated
    logger.info("handler called", extra={"correlation_id": corr_id, "path": request.url.path})
```

### What's Missing Globally
- [ ] `correlation_id` passed through to LLM provider calls
- [ ] `correlation_id` returned in error responses to frontend
- [ ] Frontend `X-Request-ID` header sent with every request
- [ ] Request traces: request → service → DB → provider → response
- [ ] Sentry: source maps not confirmed uploaded in CI

### What's Good
- `loguru` configured with structured output
- OpenTelemetry SDK installed and partially configured
- Prometheus metrics client installed
- `monitoring.py` exists with metric collection
