# Agent Heartbeat Integration Guide

> **Issue:** [#1402 — feat(agents): instrument all agent tools to POST heartbeat → real-time online status](https://github.com/SaifulHaqueNiloy/supremeai/issues/1402)
> **Related:** PR #1397 (agent-11 registration), AGENT_SLOT_REGISTRY.yaml, OPS-06 §5

Every agent slot can now report **real-time liveness** while its tool is
actually running. The dashboard (`/api/agents` on the Z.ai preview) merges
two sources:

| State | Meaning | Source |
|---|---|---|
| 🟢 **online** | heartbeat written within 90s | runtime signal (this guide) |
| 🟡 **stale** | heartbeat 90–300s old | runtime signal (tool idle or degraded) |
| 🔵 **assigned** | slot allocated in `AGENT_SLOT_REGISTRY.yaml`, no live heartbeat | policy |
| ⚪ **standby** | slot inactive (`active: false`) | policy |

## The contract

All writers produce the same Redis record (TTL 300s):

```
Key    supremeai:agent-heartbeat:agent-N
Value  {"slot":"agent-N","agentId":"Tool Name","source":"mcp-tower|backend|dashboard|cli",
        "clientId":"optional-audit-id","updatedAtMs":1758857500000,"updatedAt":"…Z"}
TTL    300 seconds   (a missed ping does NOT immediately drop the slot)
```

Readers derive the state from `updatedAtMs`: **≤90s → online**, **90–300s →
stale**, **key gone → assigned/standby**.

### Multi-account failover (important)

The canonical Upstash PRIMARY repeatedly hits its 500k/day command ceiling.
Every heartbeat writer therefore walks the account chain
**primary → secondary → tertiary → quaternary → quinary** until one accepts
the write, and readers **merge across accounts keeping the freshest record
per slot**. Configure any subset of:

```
UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN                 # primary
UPSTASH_REDIS_SECONDARY_REST_URL / UPSTASH_REDIS_SECONDARY_REST_TOKEN
UPSTASH_REDIS_TERTIARY_REST_URL / UPSTASH_REDIS_TERTIARY_REST_TOKEN
UPSTASH_REDIS_QUATERNARY_REST_URL / UPSTASH_REDIS_QUATERNARY_REST_TOKEN
UPSTASH_REDIS_QUINARY_REST_URL / UPSTASH_REDIS_QUINARY_REST_TOKEN
```

## Three ways to ping

### 1. MCP tool (recommended for MCP-connected tools — zero setup)

The control tower (`supremeai-mcp-tower.onrender.com`) exposes:

- **`agent_heartbeat`** — args: `slot` (required, `agent-N`), `agentId`
  (optional label). Ping it every 45s while your session runs.
- **`agent_status`** — lists all live heartbeats with derived state.

```jsonc
// tools/call
{ "name": "agent_heartbeat", "arguments": { "slot": "agent-4", "agentId": "Cline" } }
```

### 2. Universal pinger scripts (for tools that can run a subprocess)

```bash
# Loop while the tool runs (45s cadence):
python3 scripts/agents/heartbeat_ping.py --slot agent-1 --agent-id Antigravity

# Single ping (cron / CI / session-start hook):
python3 scripts/agents/heartbeat_ping.py --slot agent-8 --agent-id Aider --once

# Shell-only environments (curl + python3):
scripts/agents/heartbeat_ping.sh agent-1 Antigravity      # loop
scripts/agents/heartbeat_ping.sh agent-8 Aider once       # single ping

# Already MCP-connected but no Redis creds? Ping via the tower:
python3 scripts/agents/heartbeat_ping.py --slot agent-2 --agent-id "Claude Code" \
    --mode mcp --once    # uses MCP_URL + MCP_API_KEY
```

### 3. Raw Upstash REST (single curl, for locked-down environments)

```bash
curl -X POST "$UPSTASH_REDIS_REST_URL" \
  -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '["SET","supremeai:agent-heartbeat:agent-N","{\"slot\":\"agent-N\",\"agentId\":\"Tool\",\"source\":\"cli\",\"updatedAtMs":0,\"updatedAt\":\"…\"}","EX","300"]'
```

(Prefer the scripts — they build the payload and timestamps correctly.)

## Cadence & lifecycle rules

- **Ping every 45s** while the tool is running (`AGENT_HEARTBEAT_INTERVAL` for
  the backend loop; `--interval` / `HEARTBEAT_INTERVAL` for the scripts).
- Start pinging on session/tool start; stop when the tool exits.
- A stopped tool degrades 🟢→🟡 within 90s and 🔵 within 300s — automatic.
- **Only ping your own assigned slot** from `AGENT_SLOT_REGISTRY.yaml`. Pings
  are attributed with the authenticated MCP client id for auditability.

## Per-tool integration status

> **Registry update (PRs #1426/#1427/#1424, 2026-09-26):** external IDE
> tools were retired from fixed registry slots — Claude Code, Cursor and
> Cline no longer occupy agent-2/3/4, while agent-5/6 were renamed
> (z.ai issue solver / z.ai platform watchdog) and agent-12
> (z.ai action log watcher) joined. Per #1402 v2 ("agents CONNECT, they
> don't BUILD"), **any tool can still connect**: register a slot via PR to
> `docs/master_docs/AGENT_SLOT_REGISTRY.yaml`, then apply the pack below,
> substituting your own `agent-N` wherever a retired slot id appears.

### agent-1: Antigravity
- ✅ Documented: run the pinger loop alongside the IDE process
  (`heartbeat_ping.py --slot agent-1 --agent-id Antigravity`) as a startup
  task, or wire the shell pinger into your launcher script.

**Copy-paste pack (no hooks in Antigravity — rules + keep-alive):**

`.antigravity/rules/heartbeat.md` (project rule):

````markdown
# Slot heartbeat (agent-1)
At session start and after every completed task, report this agent slot:
1. connected on boot, task set to the current objective
2. idle when waiting for input
3. working + task whenever a multi-step task starts

```bash
curl -sf "$AGENT_DASHBOARD_URL/api/agents/heartbeat" -X POST \
  -H 'Content-Type: application/json' \
  -d '{"slot":"agent-1","agentId":"Antigravity","status":"connected","task":"session start"}'
```
````

Keep-alive floor so the slot never decays silently between runs:

```bash
AGENT_DASHBOARD_URL="http://localhost:3000" nohup \
  ./download/agent-heartbeat.sh --loop agent-1 "Antigravity" >/dev/null 2>&1 &
```

### Claude Code (self-registered — previously agent-2)
- ✅ Documented: add a `SessionStart` hook (`~/.claude/settings.json`) that
  launches the pinger loop with `--slot agent-N --agent-id "Claude Code"`;
  kill it in the `SessionEnd` hook. MCP-connected sessions can instead call
  the `agent_heartbeat` tool directly. **Substitute `agent-2` with your own
  registered slot id** (external IDE tools were retired from fixed slots by
  #1426).

**Copy-paste pack (native lifecycle hooks — cleanest integration):**

`.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [{ "hooks": [{ "type": "command", "command": "curl -sf $AGENT_DASHBOARD_URL/api/agents/heartbeat -X POST -H 'Content-Type: application/json' -d '{\"slot\":\"agent-2\",\"agentId\":\"Claude Code\",\"status\":\"connected\",\"task\":\"session start\"}'" }] }],
    "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "curl -sf $AGENT_DASHBOARD_URL/api/agents/heartbeat -X POST -H 'Content-Type: application/json' -d '{\"slot\":\"agent-2\",\"agentId\":\"Claude Code\",\"status\":\"working\",\"task\":\"processing prompt\"}'" }] }],
    "Stop": [{ "hooks": [{ "type": "command", "command": "curl -sf $AGENT_DASHBOARD_URL/api/agents/heartbeat -X POST -H 'Content-Type: application/json' -d '{\"slot\":\"agent-2\",\"agentId\":\"Claude Code\",\"status\":\"idle\"}'" }] }]
  }
}
```

Export the dashboard base once in the shell profile:
`export AGENT_DASHBOARD_URL="http://localhost:3000"`.

### Cursor (self-registered — previously agent-3)
- ✅ Documented: a minimal VSCode-style extension (works in Cursor) whose
  `activate()` starts a 45s `setInterval` REST ping and `deactivate()` clears
  it. Publish or install locally; see the contract above. **Substitute
  `agent-3` with your own registered slot id** (#1426).

**Copy-paste pack (rule + process watcher — no extension build needed):**

`.cursor/rules/heartbeat.mdc` (always-apply project rule):

```markdown
---
description: SupremeAI slot heartbeat (agent-3)
globs:
alwaysApply: true
---
On the FIRST terminal command of a session:
  curl -sf "$AGENT_DASHBOARD_URL/api/agents/heartbeat" -X POST -H 'Content-Type: application/json' \
    -d '{"slot":"agent-3","agentId":"Cursor","status":"connected","task":"session start"}'
Before substantive multi-step work: status=working, task=<objective>.
When going idle / finishing: status=idle. Never narrate the calls.
```

Editor-presence watcher (pings while a Cursor window is open):

```bash
#!/usr/bin/env bash
BASE="${AGENT_DASHBOARD_URL:-http://localhost:3000}"
while pgrep -x "Cursor" >/dev/null 2>&1; do
  curl -sf "$BASE/api/agents/heartbeat" -X POST -H 'Content-Type: application/json' \
    -d '{"slot":"agent-3","agentId":"Cursor","status":"idle"}' || true
  sleep 45
done
```

### Cline (self-registered — previously agent-4)
- ✅ Documented: same extension approach as Cursor (`onStartupFinished` +
  45s `setInterval`, stop on `deactivate`), packaged as `.vsix`.
  **Substitute `agent-4` with your own registered slot id** (#1426).

**Copy-paste pack (native MCP — Cline speaks MCP, so expose heartbeat as a tool):**

`cline-heartbeat.mjs` (stdio MCP server, 20 lines):

```js
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import StdioServerTransport from '@modelcontextprotocol/sdk/server/stdio.js'
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js'

const BASE = process.env.AGENT_DASHBOARD_URL ?? 'http://localhost:3000'
const SLOT = process.env.HEARTBEAT_SLOT ?? 'agent-N'   // ← your registered slot id
const beat = (status, task) => fetch(BASE + '/api/agents/heartbeat', {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ slot: SLOT, agentId: 'Cline', status, ...(task ? { task } : {}) }),
}).then(r => r.json()).catch(() => null)

const server = new Server({ name: 'heartbeat', version: '1.0.0' }, { capabilities: { tools: {} } })
server.setRequestHandler(ListToolsRequestSchema, () => ({
  tools: [{ name: 'heartbeat', description: 'Report presence to the SupremeAI board',
    inputSchema: { type: 'object', properties: { status: { enum: ['connected', 'idle', 'working'] }, task: { type: 'string' } }, required: ['status'] } }],
}))
server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { status, task } = req.params.arguments ?? {}
  return { content: [{ type: 'text', text: JSON.stringify(await beat(status ?? 'idle', task)) }] }
})
await server.connect(new StdioServerTransport())
```

Register it in Cline → MCP Servers → stdio command `node /path/to/cline-heartbeat.mjs`,
then add `.clinerules`: call `heartbeat` with `connected` on session start,
`working` + task for substantive work, `idle` when done.

> **Interactive source of truth:** all packs above are rendered with copy
> buttons and live slot-state chips on the Z.ai preview dashboard
> (**Integrations tab**), each with a "send test heartbeat" button that fires
> a real `connected → idle` sequence so you can watch your slot flip on the
> board before wiring the permanent hook. External-tool packs take a
> "your slot" input so the test ping targets a slot that actually exists in
> the registry.

### agent-5: z.ai issue solver (renamed from Windsurf, #1427)
- ✅ Documented: internal z.ai platform agent — connect via the MCP tower
  (`agent_heartbeat` tool) or the pinger loop:
  `heartbeat_ping.py --slot agent-5 --agent-id "z.ai issue solver"`.

### agent-6: z.ai platform watchdog (renamed from Devin, #1427)
- ✅ Documented: internal z.ai platform agent — long-running 3rd-party
  platform monitoring. Use the pinger loop with a 45s scheduler
  (cron/systemd timer) around its watch cycles.

### agent-7: GitHub Copilot Workspace
- ✅ Documented: a repository GitHub Action triggered on session start that
  runs a single `--once` ping; re-run per session.

### agent-8: z.ai 5.4 flash. full stack+longrun (renamed from Aider, #1427)
- ✅ Documented: wrap launches with `heartbeat_ping.sh agent-8 "z.ai 5.4 flash" &`
  in the wrapper script; stop the process on exit.

### agent-9: Continue
- ✅ Documented: VSCode/JetBrains extension approach (agent-3 pattern).

### agent-10: SupremeAI backend ✅ IMPLEMENTED IN REPO
- `backend/core/agent_heartbeat.py` — supervisor-managed loop (45s cadence),
  started in `backend/core/startup/agents.py` ("Agent 5: Self-Heartbeat").
  Kill switch: `ENABLE_AGENT_HEARTBEAT=false`. Interval: `AGENT_HEARTBEAT_INTERVAL`.

### agent-11: Z.ai 5.2 Full Stack ✅ ALREADY PINGING
- The preview dashboard pings its own slot every 45s from
  `src/app/page.tsx → postHeartbeat()` (reference implementation for HTTP
  transports). It also exposes `POST/GET /api/agents/heartbeat` and
  `GET /api/agents` for the whole fleet. The dashboard additionally serves
  the **live canonical registry** — `GET /api/agents` reads
  `AGENT_SLOT_REGISTRY.yaml` straight from main (5-min cache, compiled-mirror
  fallback) and flags drift, so newly added slots accept heartbeats without
  a dashboard redeploy.

### agent-12: z.ai action log watcher (added #1424)
- ✅ Documented: watches GitHub Actions logs, detects failures, reports and
  creates issues. Connect via the MCP tower (`agent_heartbeat`) or:
  `heartbeat_ping.py --slot agent-12 --agent-id "z.ai action log watcher"`.

## Dashboard endpoints (Z.ai preview)

```
POST /api/agents/heartbeat      {"slot":"agent-N","agentId":"Tool"}   → ping
GET  /api/agents/heartbeat      → live heartbeat records + state
GET  /api/agents                → full merged view (YAML policy × runtime)
```

The production state store is the shared Upstash chain — the dashboard and
the tower read the same records, so an MCP ping shows up in the dashboard
within one poll cycle.

## Testing

- Tower contract tests: `npm run test:heartbeat` (in
  `infrastructure/mcp-control-plane`, wired into `test:unit`) — slot
  validation, state derivation, key layout, chain assembly, fail-loud when
  Redis is unconfigured.
- Live check: call `agent_status` on the tower, or `curl GET /api/agents`
  on the dashboard.
