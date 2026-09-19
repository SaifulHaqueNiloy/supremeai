# Security Audit — SupremeAI
**Domain:** 07 | **Severity:** CRITICAL | **Last Scan:** 2026-09-19

## 🔴 CRITICAL — Immediate Action Required

### SEC-01 · eval()/exec() in Production Code (17 files)

> **Risk:** Remote Code Execution if attacker controls input flowing into these calls.

| File | Line | Pattern | Context |
|---|---|---|---|
| `core/health/self_healer.py` | 71–73 | `exec()`, `eval()`, `os.system()` | Self-healing logic — extremely dangerous |
| `core/skill_manager.py` | 100 | `exec()` | Dynamic skill loading |
| `core/middleware/security.py` | 56 | `exec()` | Security middleware — ironic |
| `agents/ephemeral_executor.py` | 96–97 | `eval()`, `exec()` | Agent execution |
| `core/cache/rate_limit_atomic.py` | 50 | `eval()` | Cache operation |
| `core/llm/token_deductor.py` | 288 | `eval()` | Token counting |
| `core/messaging/upstash_redis_queue.py` | 66 | `eval()` | Queue message deserialization |
| `services/tool_forge.py` | 153 | `exec()` | Tool creation |
| `tools/code/safe_executor.py` | 170 | `exec()` | "Safe" executor — verify sandboxing |
| `pyerrorfix/core/catalog.py` | 621 | `eval()`, `exec()` | Error catalog |

**Fix Strategy:**
- `exec()` for dynamic code → use `importlib.import_module()` or subprocess in isolated sandbox
- `eval()` for parsing → use `ast.literal_eval()` for safe evaluation
- `eval()` for math → use `numexpr` or operator module
- Self-healing `exec()` → NEVER auto-exec generated code in production without human approval gate

### SEC-02 · pickle.loads() in Production (2 files)

| File | Line | Risk |
|---|---|---|
| `pyerrorfix/core/catalog.py` | 632 | Arbitrary code execution on deserialization |
| `examples/sample_buggy.py` | 82 | (Example file — but deployed?) |

**Fix:** Replace with `json.loads()` + schema validation, or `msgpack` for binary.

### SEC-03 · Global window.fetch Override

**File:** `frontend/src/utils/apiInterceptor.ts:34`

```typescript
window.fetch = async function (...args) {  // DANGER
  options.credentials = 'include';         // Cookies sent to EVERY domain
```

**Risk:** When `VITE_USE_RELATIVE_PATH=true`, guard `url.startsWith(apiBase)` matches ALL URLs. Auth cookies sent to Supabase, Cloudflare Analytics, external CDNs.

**Fix:** Delete `setupGlobalFetchInterceptor()`. The `apiClient.ts` already handles this correctly.

---

## 🟠 HIGH — Fix This Sprint

### SEC-04 · subprocess/os.system in Production (25 files)

> Most of these are legitimate (docker, git, package install). But each needs audit.

**Files requiring immediate review (production API path):**
- `core/kaggle_orchestrator.py:134` — subprocess in orchestrator
- `core/microvm_sandbox.py:305` — should be sandboxed (verify)
- `core/repo_manager.py:54` — git operations (verify input sanitization)
- `core/health/self_healer.py:73` — `os.system()` in health handler 🚨
- `middleware/rate_limiter.py:174` — subprocess in rate limiter 🚨

**Safe subprocess pattern:**
```python
# ✅ Safe
subprocess.run(['git', 'clone', repo_url], capture_output=True, check=True, timeout=30)

# ❌ Dangerous
os.system(f"git clone {repo_url}")  # Shell injection possible
subprocess.run(user_input, shell=True)  # NEVER
```

### SEC-05 · unsafe yaml.load()

**File:** `pyerrorfix/detectors/security.py:7`
**Fix:** Always use `yaml.safe_load()`.

---

## 🟡 MEDIUM — AI-Specific Security

### SEC-06 · Prompt Injection Risk

Tools that include `user_input` directly in LLM prompts without sanitization.

**Check needed:**
- [ ] `tool_loop.py` — does it sanitize tool outputs before re-injection?
- [ ] `mcp_client.py` — does it validate MCP tool result before passing to agent?
- [ ] `agent_supervisor.py` — max recursion depth enforced?

### SEC-07 · MCP Tool Authorization

30 files register MCP tools. **Verify for each:**
- [ ] Auth check before tool execution?
- [ ] Tenant isolation enforced?
- [ ] Tool output size limits?
- [ ] Rate limiting per tool?

---

## ✅ What's Good

- `gitleaks` secret scanning in CI
- `DAST ZAP` workflow exists
- JWT secret minimum length enforced (64 chars)
- CORS wildcard banned in production (config_validation.py)
- Infisical for secrets management
- `mcp_allowlist.py` — allowlist-based MCP tool access
- CSRF token support in apiClient.ts
