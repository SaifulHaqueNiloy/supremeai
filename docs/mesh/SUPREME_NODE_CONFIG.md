# Supreme Node — Mesh Configuration Contract

> Issue #2255 (audit Phase 0) · status: **ACTIVE CONTRACT** · যে কোনো endpoint
> বদলালে এই ফাইল আর `client/supreme-node/config.yaml` একসাথে আপডেট হবে।

## ১. সত্য এখন কোথায় কী আছে (Endpoint Inventory)

| Channel | Route | কোথায় আছে | কোথায় **নেই** |
|---|---|---|---|
| Node heartbeat (REST) | `POST /api/v1/nodes/heartbeat` | **Python backend** — `backend/api/routes/mesh.py` | MCP Tower-এ নেই (404) |
| Node list / detail / role | `GET /api/v1/nodes`, `GET/PATCH /api/v1/nodes/{id}` | **Python backend** — `backend/api/routes/mesh.py` | MCP Tower-এ নেই |
| Task submit / claim (REST) | `POST /api/v1/mesh/tasks/{id}/claim` (CAS, `'any'` = best-match) | **Python backend** — `backend/api/routes/mesh_tasks.py` | — |
| Task receive (WebSocket) | `/ws/node` | **কোথাও নেই — implement হয়নি** | Tower-এও নেই, backend-এও নেই |

**এক লাইনে:** presence + task queue-এর সত্য এখন **Python backend-এ**; MCP Tower
হলো tool-federation control plane — node presence সে সামলায় না।

## ২. `client/supreme-node/config.yaml` চুক্তি

### `tower_url` — backend REST base URL (নামটা historical, কাজটা backend-এর)

- `${TOWER_URL}` placeholder → daemon `os.path.expandvars()` দিয়ে expand করে
  (#2255 পর্যন্ত placeholder-টা literal string হিসেবেই থেকে যেত — interpolation
  ছিলই না)।
- Override chain: `TOWER_URL` env var → config-এর literal মান।
- Production-এ অবশ্যই **backend** host দিতে হবে (যেমন `https://supremeai-api.<host>`);
  Tower host দিলে heartbeat 404 খাবে।

### `heartbeat_path` — fixed `/api/v1/nodes/heartbeat`

Backend route-এর সাথে lockstep; বদলাতে হলে এই doc + mesh.py একসাথে বদলাতে হবে।

### `tower_ws_url` — খালি মানে heartbeat-only mode

- `/ws/node` channel এখনো কোনো peer-এ implement হয়নি।
- খালি (`""`) রাখলে: daemon WS connect skip করে, শুধু heartbeat loop চালায় —
  node presence register হয়, MESH-2 dashboard-এ দেখা যায়, task listener বন্ধ থাকে।
- Channel implement হলে: `wss://<backend-host>/ws/node` বসালেই full mode।
- **Daemon behavior note (#2255):** main loop heartbeat-কে WS connect-এর success-এর
  উপর gate করে (`FIRST_COMPLETED`) — তাই unreachable WS মানে পুরো daemon
  reconnect-loop-এ আটকে heartbeat-ও চলত না। খালি URL এখন সেটার থেকে মুক্তি।

## ৩. Env vars

| Var | কাজ | Default |
|---|---|---|
| `TOWER_URL` | `tower_url` interpolation | (config literal) |
| `TOWER_AUTH_TOKEN` | heartbeat/WS `Authorization: Bearer` header (optional, pre-auth per MESH-1) | empty |
| `SUPREME_NODE_OLLAMA_URL` | local ollama override | empty |

## ৪. Verification (এই চুক্তি ভাঙলে ধরার উপায়)

- `client/supreme-node/tests/test_config.py` — placeholder expansion + empty-ws
  normalization-এর regression আছে (#2255)।
- Out-of-the-box smoke: `python daemon.py --dry-run` — `TOWER_URL` সেট করে একবার
  heartbeat পাঠিয়ে exit; 200 + `lease_active` ফিরলে config ঠিক আছে।

## ৫. ভবিষ্যৎ (এই PR-এর scope বাইরে)

1. `/ws/node` channel backend-এ implement হলে → full mode default হবে।
2. Audit Phase-6 (MCP unification): Tower-ের নিজস্ব heartbeat slot-model retire
   হয়ে mesh lease model-কে follow করবে — তখন এই doc-এর inventory টেবিল বদলাবে।
