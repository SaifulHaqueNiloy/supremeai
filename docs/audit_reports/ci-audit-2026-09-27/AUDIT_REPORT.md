# CI Audit — 2026-09-27 (HEAD 4c9f78d3)

Fresh-clone audit of `SaifulHaqueNiloy/supremeai` main branch.
Latest CI run **#36293479018** (4c9f78d3) is **FAILED** — 4th consecutive
red run since the last green on `e179bd1f`.

All issues below were verified locally and fixed in commit `2c53da35`.
The commit is local only (no push credentials available in this
environment); push + GitHub-issue creation must be done by a human with
repo write access.

---

## Issue 1 — ruff lint gate fails (3 errors)

**CI Job:** Operational Tooling Quality Gate → "Centralized Backend Lint & Format Gate"
**Severity:** blocking (exit 1)

Three ruff errors in backend source/tests:

| File | Rule | Problem |
|------|------|---------|
| `backend/api/routes/missions.py:31-32` | I001 | Two separate `from missions.models import` lines not merged |
| `backend/api/routes/webhooks_github.py:31-33` | I001 | `core.logging_config` imported after `core.orchestration` |
| `backend/tests/api/routes/test_webhooks_github.py:48` | B018 | Useless expression `client.app.router` |

**Fix:** merged imports, reordered, removed dead B018 block.

---

## Issue 2 — ruff format gate fails (19 files)

**CI Job:** Operational Tooling Quality Gate → "Centralized Backend Lint & Format Gate"
**Severity:** blocking (exit 1)

19 files fail `ruff format --check`. These were **masked** by Issue 1
(bash `-e` stops the step after `ruff check` fails, so `ruff format --check`
never ran until the lint errors were fixed).

**Fix:** `ruff format backend` — whitespace-only reformats, no semantic
changes.

---

## Issue 3 — capability inventory references deleted route

**CI Job:** Advanced Pre-Merge → "Validate capability-surface inventory (issue #1101)"
**Severity:** blocking (exit 1)

`docs/capability_inventory.json` → `voice` capability lists
`backend/api/routes/stream_voice_sse.py` in `surfaces[]`, but that file was
deleted in rollup #2067 (commit d6ba00e0).

**Fix:** removed the stale surface entry; renamed capability to
"Voice (websocket voice)".

---

## Issue 4 — duplicate `run_dag_for_workspace` method

**CI Job:** Backend Tests (fast) → `test_sworm_adapter_contract`
**Severity:** blocking (test AssertionError)

`backend/core/zero_cost_architecture/swarm_orchestrator_integration.py`
defines `run_dag_for_workspace` **twice** (lines 136 + 171). The 2nd def
silently overrides the 1st. The 1st forwards `user_id=user_id` as a
keyword arg (correct); the 2nd forwards it positionally (breaks the
adapter contract test which asserts `assert_awaited_once_with("WS-OBJ",
user_id="u-9")`).

**Root cause:** a merge or rollup landed two copies of the same fix with
slightly different signatures.

**Fix:** deleted the 2nd (incorrect) definition; the remaining single
def forwards `user_id=user_id` as a kwarg.

---

## Issue 5 — `/swarm/execute` response missing top-level `task_id`

**CI Job:** Backend Tests (fast) → `test_swarm_execute_returns_real_orchestration_result`
**Severity:** blocking (KeyError: 'task_id')

`backend/api/routes/agent_tasks.py` `execute_swarm()` returns
`{"status":..., "session_id":..., "results":{"task_id":...}}` — but the
test asserts `body["task_id"]` (top-level), not `body["results"]["task_id"]`.

**Fix:** added `"task_id": result.task_id` to the top-level response dict.

---

## Issue 6 — gateway-context test expects deleted `websocket_agent.py`

**CI Job:** Backend Tests (services) → `test_gateway_context_m03`
**Severity:** blocking (2 assertions)

`backend/tests/scripts/test_gateway_context_m03.py`:
- `test_current_tree_has_zero_violations`: asserts `total >= 14` but
  actual is **12** (the deleted `websocket_agent.py` had 2 gateway
  call-sites).
- `test_route_files_build_context_ast_level`: expected set includes
  `"websocket_agent.py"` but the file was deleted in rollup #2067.

**Fix:** removed `"websocket_agent.py"` from expected set; lowered
ratchet to `>= 12`.

---

## Issue 7 — task_queue broadcast test asserts deleted `websocket_agent.manager`

**CI Job:** Backend Tests (core-unit) → `test_success_persists_and_broadcasts`
**Severity:** blocking (AssertionError: awaited 0 times)

`backend/tests/core/queue/test_task_queue_full.py` installs a fake
`api.routes.websocket_agent.manager` and asserts `broadcast_to_user` was
awaited. But rollup #2067 rewrote `task_queue.py`'s completion broadcast
to use `core.messaging.pubsub.global_pubsub.publish("dashboard_events",…)`
(#1832), and deleted `websocket_agent.py` entirely.

**Fix:** replaced `_install_fake_ws_manager` with `_install_fake_pubsub`
(patches `core.messaging.pubsub.global_pubsub`); updated assertions to
check `publish` was awaited with `("dashboard_events", {type, task_id,
user_id, result})`.

---

## Issue 8 — stale generated docs reference deleted routes (4 files)

**Severity:** non-blocking (latent consistency debt)

The deleted routes' metadata survived in generated/committed artifacts:

| File | Stale content |
|------|---------------|
| `backend/openapi.json` | `/api/v1/stream/voice` path + `stream_voice_sse_api_v1_stream_voice_get` operationId |
| `docs/generated/route_inventory.json` | derived from stale openapi |
| `docs/generated/route_knowledge_graph.json` | derived from stale inventory |
| `docs/audit_reports/module_wiring_audit.json` | 8 refs to `websocket_agent` / `stream_voice_sse` |
| `docs/generated/module_capability_matrix.json` | derived from stale audit |

**Fix:** removed stale path from openapi.json; regenerated all 4 derived
artifacts via their generator scripts.

---

## Pre-existing failures (NOT rollup-caused — documented, not fixed)

These 5 test failures were present on `e179bd1f` (last green) and persist
on `4c9f78d3`. They predate the rollup and are test/production
mismatches from an earlier refactor (last touched by auto-regen
`d3078ee`). They require CI-environment debugging (not reproducible
locally due to secret/config differences).

| Test | Error |
|------|-------|
| `test_multicloud::test_cloud_distribution_endpoint` | `assert 403 == 200` |
| `test_security_rate_limit_backend::test_redis_authoritative_allows_under_limit` | `assert 0 == 1` (eval_calls empty) |
| `test_security_rate_limit_backend::test_redis_authoritative_rejects_over_limit` | `assert True is False` |
| `test_security_rate_limit_backend::test_critical_path_limit_override` | `IndexError: list index out of range` |
| `test_security_rate_limit_backend::test_fallback_memory_is_per_instance` | `assert '5.5.5.5' in {}` |

---

## Verification (all local, post-fix)

| Check | Result |
|-------|--------|
| `ruff check backend --select … --ignore …` | All checks passed! |
| `ruff format --check backend` | 2033 files already formatted |
| `python scripts/ci/validate_capability_inventory.py` | OK — 26 capabilities |
| `python -m constitution.engine --pr-diff --base-ref HEAD` | PASSED (0 findings) |
| gateway-context scan | violations=0, total=12, 8 files (matches test) |
| stale-ref grep (stream_voice_sse / websocket_agent in generated) | 0 matches |

---

## Action required from repo maintainer

1. **Push commit `2c53da35`** to `origin/main` (this environment has no
   push credentials).
2. **Monitor the next CI run** — Issues 1-8 should go green; the 5
   pre-existing failures (multicloud + security_rate_limit) will remain
   red until separately addressed.
3. **Optional:** create GitHub issues for the 5 pre-existing failures so
   they're tracked and assigned.
