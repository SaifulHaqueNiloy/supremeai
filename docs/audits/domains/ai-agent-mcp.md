# AI / Agent / MCP Audit — SupremeAI
**Domain:** 13 | **Last Scan:** 2026-09-19

## MCP Registration (30 files found)

### Tool Authorization Gaps
Every MCP tool must have:
- [ ] Tenant isolation check
- [ ] User permission check
- [ ] Input validation / size limit
- [ ] Output size limit
- [ ] Execution timeout
- [ ] Rate limiting per tool per user

**Files to audit:**
- `memory/mcp_server.py` — memory tools
- `core/circles/centers/mcp_center.py` — circle MCP
- `core/mcp_client.py` — client implementation
- `api/routes/mcp_marketplace.py` — marketplace registration

### Positive: `core/mcp_allowlist.py` exists
This is good — MCP tools must be on allowlist before execution.
**Verify:** Is allowlist enforced at runtime or only at registration?

## Agent Safety

### exec()/eval() in Agent Code (HIGH RISK)
| File | Pattern | Risk |
|---|---|---|
| `agents/ephemeral_executor.py:96-97` | `eval()`, `exec()` | Agent executing untrusted code? |
| `core/skill_manager.py:100` | `exec()` | Dynamically loading skill code |
| `services/tool_forge.py:153` | `exec()` | Tool forge creating executable code |
| `services/ide_trio/kilo_reviewer.py:134-135` | `eval()`, `exec()` | IDE reviewer executing code |

### Autonomy Kill Switch (9 references)
Files referencing kill switch/autonomy:
- `agents/governance/ethics_monitor_agent.py` ✅ Good
- `api/routes/cloud_mesh.py`
- `api/routes/browser/_crown_jewel.py` — crown jewel route? Needs review
- `core/self_evolution/daily_learner.py`

**Must verify:** Is kill switch truly global and immediate? Or per-agent?

## Failure Chain Analysis (P1)

Define and test each provider failure:
```
Gemini fails → OpenRouter fallback → OpenRouter fails → Groq → Groq fails → queue? → user error
```

**Current status:** Circuit breaker exists (3 implementations), but failure chain not documented per feature.

## Agent Recursion Guard
- Max depth enforced in `agent_supervisor.py`?
- What prevents: Agent A → calls Agent B → calls Agent A?
