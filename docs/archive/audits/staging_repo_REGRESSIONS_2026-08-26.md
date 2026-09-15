# SupremeAI Staging Repo — Regression List (2026-08-26)

Source: fresh `git clone --depth 1` of `github.com/SaifulHaqueNiloy/supremeai` @ `95d1594`
("chore: consolidate agents (Phase 1) and remove hardcoded fallbacks") — the Phase 1 agent
consolidation from our last session landed, and someone/something also did a partial pass on
the Redis-fallback hardcode issue. Everything below is freshly verified against actual code,
not carried over from memory.

---

## 🔴 CRITICAL — New auth-bypass regression, not previously flagged

**`backend/core/security/authentication/rbac.py`, `get_current_user_token()` (line 262)**

The function is supposed to only auto-grant admin access inside test environments. The actual flow:
```python
try:
    if is_test_environment():
        ...
        return {"sub": admin_email, "role": "admin"}
except Exception:
    ...
# falls through here even when is_test_environment() is False (i.e. in PRODUCTION)
admin_email = os.getenv("ADMIN_EMAIL", "admin@supremeai.com")
return {"sub": admin_email, "role": "admin"}
```
When `is_test_environment()` returns `False` — the normal production case — the function does **not**
raise or reject; it falls through to the last two lines and unconditionally returns admin credentials
to *any* caller, authenticated or not. Compare this to the correctly-guarded sibling implementations in
`api/deps.py` and `api/dependencies.py`, which both `raise HTTPException(401)` in the non-test branch.

**Impact:** `get_current_user_token` (and `get_current_admin`, which just calls it directly) is imported
by 11+ route files — `auth.py`, `keys.py`, `agents.py`, `simulator.py`, `codeflow.py`, `internal.py`,
`living_engine.py`, `tools_registry.py`, `agent_tasks.py`, `conversations.py`, `email.py`,
`advanced_router.py`. Any of these routes that rely on this specific import path effectively have **no
authentication** in production — every request is silently treated as admin.

**Fix:** add the same `raise HTTPException(401, ...)` (or equivalent) after the `try/except` block,
matching the pattern already correctly used in `deps.py`/`dependencies.py`. This is a 2-line fix but
security-critical — recommend patching before anything else on this list.

---

## 🟠 Partially-fixed regression — Redis localhost fallback (same bug class flagged 2026-08-07/08-24)

**Good news:** the 7 files from the original hardcoded-values audit (`core/cache.py`, `core/rate_limit.py`,
`core/rate_limit_quota.py`, `core/optimization/optimized_redis_client.py`,
`core/queue/task_queue_enhanced.py`, `api/routes/websocket_agent.py`, `tools/collaborative_editor.py`)
are now genuinely clean — verified zero `redis://localhost` occurrences in any of them.

**Bad news:** the exact same unguarded pattern (`getattr(settings, "redis_url", None) or
os.environ.get("REDIS_URL", "redis://localhost:6379")`, no `env == "local"` guard) now exists,
copy-pasted, in **3 files not covered by the original audit**:
- `backend/core/queue/task_queue.py` (line 30) — a *different* file from the already-fixed
  `task_queue_enhanced.py`; both exist side by side in `core/queue/`
- `backend/core/llm/token_budget.py` (line 207)
- `backend/core/evolution/self_evolution_agent.py` (line 122)

Plus one lower-severity instance: `backend/core/testing/qa_suite.py` line 754 passes the literal
`"redis://localhost:6379"` directly into a cache-integration test call — likely intentional for a
local-only test helper, but worth confirming it's never invoked as a real production health check.

**Fix:** same established idiom as the already-fixed files — only fall back to localhost when
`settings.env == "local"`, otherwise raise/log. Given the fix already exists correctly in 7 sibling
files, this should be a quick copy-the-pattern job.

---

## 🟡 Known, unresolved (not new, but still open — carried forward from prior audits)

- **`brain/agent_department.py` vs `agent_departments.py`** — both still define a class literally named
  `AgentDepartment` (flagged during our Phase 1 session). Still only has the `AgentDepartmentLegacy`
  stopgap alias, not a real resolution. Needs a proper read-and-rename before Phase 2 work continues.
- **Module-name collisions** — `config.py` still exists in 3 places (`core/config.py`,
  `api/routes/config.py`, `pyerrorfix/config.py`), `llm_gateway.py` in 2 (`api/routes/`, `core/llm/`),
  `evolution` as a directory name in 4 places (`backend/evolution`, `backend/agents/evolution`,
  `backend/core/evolution`, `backend/tests/evolution` — the last is an expected test-mirror, not itself
  a risk). Same risk class that already caused the `secret_vault`/`honeypot_middleware` bugs in the
  sibling repo. Unchanged since last audit.

## ✅ Checked and confirmed clean (no regression found)
- Hardcoded Render service IDs in CI workflows — 0 occurrences (still fixed).
- SSL certificate verification bypass (`ssl.CERT_NONE`) — still properly fixed, comment references the
  original fix commit.
- `api/deps.py` and `api/dependencies.py`'s own `get_current_user_token`-equivalents — correctly guarded,
  not affected by the rbac.py bug.
- Bare `return` immediately after `yield` in test fixtures (the recurring cross-test state-leak bug class
  from the other repo) — found 7 occurrences via grep, manually inspected all 7: every one is a harmless
  no-op `return` with nothing after it, not the dangerous "unreachable teardown code" pattern. Not a
  regression.
- Whole-backend syntax check (`ast.parse` on all 1552 `.py` files) — 0 syntax errors, including the
  facade files from our Phase 1 agent-consolidation session (still structurally intact).

## Not independently re-verified this pass (would need a full local pytest run + CI log access, neither available in this sandbox)
- Whether CI is currently green or red on this repo.
- Whether the coverage gate (`MIN_BACKEND_COVERAGE: 45`) is actually being met or is just a threshold nobody's hit yet.
