# Agent Heartbeat Integration — real-time online status (issue #1402)

> **Goal:** the agent dashboard must distinguish *"tool assigned but IDE
> closed"* from *"tool assigned AND actively running"*. The policy registry
> (`AGENT_SLOT_REGISTRY.yaml`) answers *who may run*; heartbeats answer
> *who is running right now*.
>
> Introduced by PR #1397 (agent-11 registration + heartbeat infrastructure).
> Reference clients live in [`tools/agent_heartbeat/`](../../tools/agent_heartbeat/).

## 1. State model (6 states)

```
standby → assigned → connected → idle ↔ working → stale → assigned
                                       ↑___________________|
```

| State | Color | Meaning | Shown when |
|---|---|---|---|
| ⚪ `standby` | slate | Slot inactive | `active: false` in registry YAML |
| 🔵 `assigned` | cyan | Slot allocated, no heartbeat | Tool closed / never pinged |
| 🟢 `connected` | teal (pulse) | First heartbeat received | < 10 s after first ping |
| 🟢 `idle` | emerald | Heartbeat live, no active task | Default running state |
| 🟣 `working` | violet (pulse) | Executing a task | `status:"working"` + `task:"…"` |
| 🟡 `stale` | amber | Heartbeat age 90 s–300 s | Degraded — tool may have crashed |

Derived server-side from the Redis hash `agent:status:{slot}`
(`lastSeen`, `agentId`, `status`, `task`, `updatedAt`; key TTL 300 s).

## 2. Endpoint contract

```json
POST /api/agents/heartbeat
Content-Type: application/json

{
  "slot": "agent-4",              // required, must match /^agent-\d+$/
  "agentId": "Cline",             // optional human-readable label
  "status": "working",            // connected | idle | working (default idle)
  "task": "database migration 7"  // optional, shown in "Current task" column
}
```

- **Cadence:** keep-alive ping every **45 s**; status transitions on events.
- **TTL:** 300 s — a missed ping does not immediately drop the slot.
- **Where it lives:** preview dashboard route
  `src/app/api/agents/heartbeat/route.ts` (Upstash Redis, 5-account fallback
  chain). Production target: the same route on the **MCP control tower** so
  MCP-connected agents can ping with the existing protocol (tracked in #1402).

## 3. Lifecycle a tool should emit

| Event | POST |
|---|---|
| Startup | `{"status":"connected"}` (one-time) |
| 3 s later, no task | `{"status":"idle"}` |
| Task starts | `{"status":"working","task":"<description>"}` |
| Task completes | `{"status":"idle"}` |
| Every 45 s | `{"status":"idle"}` (or current status) |
| Shutdown | stop pinging → key expires in ≤ 300 s → slot reverts to `assigned` |

## 4. Reference clients (this repo)

`tools/agent_heartbeat/` — shared, zero-dependency:

```bash
export HEARTBEAT_URL="https://<dashboard-host>/api/agents/heartbeat"

# keep-alive for the whole session (any slot)
AGENT_SLOT=agent-2 AGENT_ID="Claude Code" tools/agent_heartbeat/heartbeat.sh &

# task transitions from wrapper scripts / CI steps
tools/agent_heartbeat/heartbeat.py working "archiving shim batch 5"
tools/agent_heartbeat/heartbeat.py stop
```

Fail-soft guarantee: heartbeat failures never crash the host tool (exit 0,
stderr warning only). If `HEARTBEAT_URL` is unset the clients are no-ops.

## 5. Per-tool integration

### agent-1: Antigravity
Startup hook running the shared pinger on a 45 s timer, or a Python sidecar
(`heartbeat.py` + `HeartbeatClient().start()`) launched beside the Antigravity
process.

### agent-2: Claude Code ✅ (reference implementation in this repo)
1. `mkdir -p ~/.claude/hooks`
2. `cp tools/agent_heartbeat/claude-code/heartbeat-hook.sh ~/.claude/hooks/heartbeat.sh && chmod +x ~/.claude/hooks/heartbeat.sh`
3. Merge `tools/agent_heartbeat/claude-code/settings-snippet.json` into
   `~/.claude/settings.json` (registers the `SessionStart` hook + env vars).
4. On every session start: `connected` → background keep-alive (`idle`, 45 s);
   the pidfile guard kills a previous session's pinger so one session == one
   pinger.

### agent-3: Cursor
Extension `cursor-heartbeat`: ping on `activation` + every 45 s via
`setInterval`; stop on dispose. Publish to the marketplace or install locally.

### agent-4: Cline
VSCode extension `cline-heartbeat`: activate on `onStartupFinished`, ping
every 45 s while the extension host is alive, stop on `deactivate`. Package
as `.vsix`. Alternative: add the ping directly to the Cline fork's core.

### agent-5: Windsurf
Same VSCode-extension approach as Cursor; only ping while the slot is
`active: true` in the registry.

### agent-6: Devin
Server-side: ping from Devin's session manager / startup script using
`heartbeat.py working "<session goal>"` at session start, `idle` keep-alive
during, `stop` at session end.

### agent-7: GitHub Copilot Workspace
GitHub Action workflow that pings `connected` when a Copilot Workspace session
starts, plus a `working` ping per task step (via `workflow_dispatch` or the
workspace startup hook).

### agent-8: Aider
`--heartbeat` flag on the CLI that starts a `HeartbeatClient` background
thread (`heartbeat.py`), or wire into Aider's existing hook system if
available.

### agent-9: Continue
VSCode/JetBrains extension — same pattern as Cline (activation ping + 45 s
keep-alive + deactivate stop).

### agent-10: SupremeAI (self-development mode)
Ping from the backend's own startup sequence (`backend/core/startup/`):
`connected` at boot, `idle` keep-alive thread, `working` around long
self-maintenance jobs. Reuse `tools/agent_heartbeat/heartbeat.py` (stdlib
only — no new dependency for the backend).

### agent-11: Z.ai 5.2 Full Stack ✅ DONE
Already pings every 45 s from the preview dashboard
(`src/app/page.tsx` → `postHeartbeat()`); demonstrates the full 6-state
lifecycle live (`connected` → `idle` after 3 s → `working` on refresh click).

## 6. Acceptance criteria (issue #1402)

- [x] Every tool (agent-1 … agent-10) has a documented integration path (this doc + shared clients)
- [x] Reference clients committed: `tools/agent_heartbeat/{heartbeat.sh,heartbeat.py,claude-code/}`
- [ ] Each tool actually installed & showing 🟢 when running (per-tool rollout above)
- [ ] Slot degrades to 🔵 `assigned` within 90 s of tool close (dashboard TTL behaviour, agent-11)
- [ ] CI test: heartbeat endpoint responds 200 for valid slot names (dashboard repo)
- [ ] Endpoint deployed to production (MCP tower route — tracked in #1402)

## 7. Notes for maintainers

- Heartbeat is **observability, not auth** — never gate work on it; the
  registry YAML remains the policy source of truth.
- Ping bodies are tiny JSON; a 45 s cadence is ~2 k requests/day/slot —
  watch the Upstash account limits (primary hit 500 k/day once; the
  5-account fallback chain exists for this reason).
- Keep pingers fail-soft. A dashboard outage must not take down an agent.
