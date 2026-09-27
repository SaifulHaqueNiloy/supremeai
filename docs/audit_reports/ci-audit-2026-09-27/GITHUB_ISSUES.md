# GitHub Issue Drafts — CI Audit 2026-09-27

These issue drafts are ready to be created on the GitHub issue tracker.
Copy the title + body for each into `https://github.com/SaifulHaqueNiloy/supremeai/issues/new`.

---

## Issue A — [CI-blocker] ruff lint gate fails: 3 errors in backend source

**Labels:** `ci-failure`, `lint`, `rollup-fallout`

**Body:**

The latest CI run (#36293479018, 4c9f78d3) fails the "Centralized Backend
Lint & Format Gate" step with 3 ruff errors:

1. `backend/api/routes/missions.py:31-32` — I001: two separate
   `from missions.models import` lines not merged
2. `backend/api/routes/webhooks_github.py:31-33` — I001: `core.logging_config`
   imported after `core.orchestration`
3. `backend/tests/api/routes/test_webhooks_github.py:48` — B018: useless
   expression `client.app.router`

These were introduced by rollup #2067 (d6ba00e0) and never fixed by the
6 subsequent rollup batches.

**Fix:** applied in local commit `2c53da35` (not yet pushed — no push
credentials in audit environment).

---

## Issue B — [CI-blocker] capability inventory references deleted stream_voice_sse.py

**Labels:** `ci-failure`, `capability-inventory`, `rollup-fallout`

**Body:**

`docs/capability_inventory.json` → `voice` capability still lists
`backend/api/routes/stream_voice_sse.py` in `surfaces[]`, but that file
was deleted in rollup #2067. The validator
(`scripts/ci/validate_capability_inventory.py`) fails:

```
CAPABILITY INVENTORY INVALID — 1 problem(s):
  - voice: surface path does not exist on disk: backend/api/routes/stream_voice_sse.py
```

**Fix:** remove the stale surface entry (applied in local commit `2c53da35`).

---

## Issue C — [CI-blocker] duplicate run_dag_for_workspace method in ZeroCostSwarmOrchestrator

**Labels:** `ci-failure`, `bug`, `swarm`, `rollup-fallout`

**Body:**

`backend/core/zero_cost_architecture/swarm_orchestrator_integration.py`
defines `run_dag_for_workspace` **twice** (lines 136 + 171). The 2nd def
silently overrides the 1st:

- 1st def (line 136): forwards `user_id=user_id` as a keyword arg ✓
- 2nd def (line 171): forwards `user_id` positionally ✗

This breaks `test_run_dag_for_workspace_forwards_to_original` which
asserts:
```python
fake_self._original_orchestrator.run_dag_for_workspace.assert_awaited_once_with(
    "WS-OBJ", user_id="u-9"
)
```
The positional call produces `("WS-OBJ", "u-9")` not `("WS-OBJ",
user_id="u-9")`.

**Likely cause:** two copies of the same #1816 fix landed in a merge
train with slightly different signatures.

**Fix:** delete the 2nd (incorrect) definition (applied in local commit
`2c53da35`).

---

## Issue D — [CI-blocker] /swarm/execute response missing top-level task_id

**Labels:** `ci-failure`, `bug`, `api`, `swarm`

**Body:**

`backend/api/routes/agent_tasks.py` `execute_swarm()` returns:
```python
{"status":..., "session_id":..., "results":{"task_id":...}}
```
But `test_swarm_execute_returns_real_orchestration_result` asserts
`body["task_id"]` (top-level) → `KeyError: 'task_id'`.

**Fix:** add `"task_id": result.task_id` to the top-level response dict
(applied in local commit `2c53da35`).

---

## Issue E — [CI-blocker] gateway-context test expects deleted websocket_agent.py

**Labels:** `ci-failure`, `test`, `rollup-fallout`

**Body:**

`backend/tests/scripts/test_gateway_context_m03.py` has two failing
assertions after rollup #2067 deleted `websocket_agent.py`:

1. `test_current_tree_has_zero_violations`: `assert total >= 14` fails
   (actual = 12 — the deleted route had 2 gateway call-sites).
2. `test_route_files_build_context_ast_level`: expected set includes
   `"websocket_agent.py"` which no longer exists.

Actual scan result: `violations=0, total=12, 8 files`.

**Fix:** remove `"websocket_agent.py"` from expected set; lower ratchet
to `>= 12` (applied in local commit `2c53da35`).

---

## Issue F — [CI-blocker] task_queue broadcast test asserts deleted websocket_agent.manager

**Labels:** `ci-failure`, `test`, `rollup-fallout`

**Body:**

`backend/tests/core/queue/test_task_queue_full.py` installs a fake
`api.routes.websocket_agent.manager` and asserts `broadcast_to_user` was
awaited. But rollup #2067:
- rewrote `task_queue.py`'s completion broadcast to use
  `core.messaging.pubsub.global_pubsub.publish("dashboard_events",…)`
  (#1832)
- deleted `websocket_agent.py` entirely

Result: `AssertionError: Expected broadcast_to_user to have been awaited
once. Awaited 0 times.`

**Fix:** replaced `_install_fake_ws_manager` with `_install_fake_pubsub`
(patches `core.messaging.pubsub.global_pubsub`); updated assertions to
check `publish` was awaited with `("dashboard_events", {type, task_id,
user_id, result})` (applied in local commit `2c53da35`).

---

## Issue G — [tech-debt] stale generated docs reference deleted routes

**Labels:** `tech-debt`, `generated-docs`, `rollup-fallout`

**Body:**

Rollup #2067 deleted `stream_voice_sse.py` and `websocket_agent.py` but
the generated/committed artifacts were never regenerated, leaving stale
references:

| File | Stale content |
|------|---------------|
| `backend/openapi.json` | `/api/v1/stream/voice` path + `stream_voice_sse_api_v1_stream_voice_get` operationId |
| `docs/generated/route_inventory.json` | derived from stale openapi |
| `docs/generated/route_knowledge_graph.json` | derived from stale inventory |
| `docs/audit_reports/module_wiring_audit.json` | 8 refs to deleted modules |
| `docs/generated/module_capability_matrix.json` | derived from stale audit |

**Fix:** removed stale path from openapi.json; regenerated all derived
artifacts via their generator scripts (applied in local commit
`2c53da35`).

**Process gap:** the "post-merge auto-regen" pipeline
(`chore(artifacts): post-merge auto-regen` commits) apparently does not
cover all generated artifacts. Recommend adding a CI step that regenerates
+ diffs these files, failing if the committed copy drifts.

---

## Issue H — [pre-existing] test_multicloud 403 + 4x test_security_rate_limit_backend failures

**Labels:** `pre-existing`, `test`, `investigation-needed`

**Body:**

These 5 test failures predate rollup #2067 (present on `e179bd1f`, the
last green run). They are test/production mismatches from an earlier
refactor (last touched by auto-regen `d3078ee`):

| Test | Error |
|------|-------|
| `test_multicloud::test_cloud_distribution_endpoint` | `assert 403 == 200` |
| `test_security_rate_limit_backend::test_redis_authoritative_allows_under_limit` | `assert 0 == 1` (eval_calls empty) |
| `test_security_rate_limit_backend::test_redis_authoritative_rejects_over_limit` | `assert True is False` |
| `test_security_rate_limit_backend::test_critical_path_limit_override` | `IndexError: list index out of range` |
| `test_security_rate_limit_backend::test_fallback_memory_is_per_instance` | `assert '5.5.5.5' in {}` |

**Not fixed** in this audit — they require CI-environment debugging (the
`atomic_window_incr` function uses `client.eval()` which the test's
`_FakeRedis.eval` stubs, but the production code path may have diverged
from the test's expectation of how `eval` is called). The multicloud 403
is likely an auth-dependency change (`get_current_admin` role check).

**Note:** these are NOT caused by the rollup and should be tracked
separately.
