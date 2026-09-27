# Mesh Daemon Configuration Contract

> **Status:** Active · **Owner:** mesh/coder lane · **Last verified:** 2026-09-27 (#2255 Phase-0)

## The two-host split (the #2255 fix)

`supreme-node` talks to **two distinct services**. Conflating them was the Phase-0 bug:

| Service | Host var | Routes that live here | Notes |
|---|---|---|---|
| **Python backend** (FastAPI) | `BACKEND_URL` | `POST /api/v1/nodes/heartbeat` · `GET /api/v1/nodes` · `/api/v1/mesh/tasks/*` | Heartbeat + presence + task queue. Canonical source: `backend/api/routes/mesh.py` |
| **MCP Tower** (TypeScript) | `TOWER_URL` / `TOWER_WS_URL` | `/clients` · `/tenants` · `/messages` · `/agents/*` · Tower-side tools | Tool dispatch + agent registry + Tower-side heartbeats (different contract from mesh node heartbeat) |

Before #2255, `config.yaml` pointed `heartbeat_path` at `tower_url` → every out-of-the-box mesh daemon received HTTP 404 because the route doesn't exist on Tower.

## Config keys

```yaml
# All three may point to the same host in dev (single-process deploy), but
# production SHOULD split them — backend is the FastAPI service, Tower is
# the MCP control plane.

tower_url: ${TOWER_URL}        # MCP Tower REST base
tower_ws_url: ${TOWER_WS_URL}  # MCP Tower WebSocket (task channel)
backend_url: ${BACKEND_URL}    # Python backend REST base (heartbeat target)
heartbeat_path: /api/v1/nodes/heartbeat  # appended to backend_url
```

## Override chain

1. Env var (e.g. `BACKEND_URL=https://api.supremeai.onrender.com`)
2. `config.yaml` value
3. Built-in default (none — must be set explicitly)

## Verification (post-fix)

- `POST {backend_url}/api/v1/nodes/heartbeat` returns 200 (was 404 on Tower).
- `GET {backend_url}/api/v1/nodes` returns node list (Tower doesn't have this route).
- `ws://{tower_ws_url}` connects to MCP Tower (Python backend doesn't host this WS).

## Related

- `backend/api/routes/mesh.py` — canonical heartbeat + mesh task routes
- `infrastructure/mcp-control-plane/` — MCP Tower source
- Issue #939 (MESH-1) — original spec for node heartbeat
- Issue #2255 — this Phase-0 fix
