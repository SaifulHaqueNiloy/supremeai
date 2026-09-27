"""Issue #1816 — ZeroCostSwarmOrchestrator adapter contract tests.

The "drop-in replacement" wrapper was API-incompatible with BOTH routes that
call it, killing two user-facing features:

  1. ``POST /api/v1/agents/swarm/execute`` used nonexistent constructor kwargs
     (``user_id/session_id/task_prompt``) and a nonexistent ``execute()``
     method → TypeError before anything ran; the response also read
     ``workspace.generated_code`` / ``architecture_design`` which do not exist
     on ``SharedWorkspace``.
  2. ``POST /agent/action`` platform-sync actions called
     ``run_dag_for_workspace`` — only the ORIGINAL SwarmOrchestrator has it;
     the ZeroCost wrapper never forwarded it → AttributeError → 500 for every
     Slack/Notion/GitHub sync.

Locks the repaired contracts end-to-end at the route layer.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from models.shared_workspace import SharedWorkspace


def _workspace() -> SharedWorkspace:
    return SharedWorkspace(
        task_id="t-1",
        original_prompt="write a haiku about CI",
        work_product={"code": "print('hello')", "analysis": "looks good"},
        test_results={"passed": True, "feedback": "all green"},
        intent="code_generation",
    )


def _execution_result():
    from core.orchestration.swarm_orchestrator import ExecutionResult

    return ExecutionResult(
        task_id="t-1",
        status="completed",
        workspace=_workspace(),
        errors=[],
    )


# ─────────────────────── path 1: /api/v1/agents/swarm/execute ───────────────────────


class FakeZeroCostOrchestrator:
    """Stand-in asserting the REAL wrapper contract (config-only ctor + execute_task)."""

    def __init__(self, config=None):
        assert config is None or hasattr(config, "__dict__"), (
            "wrapper ctor takes ZeroCostConfig | None only — issue #1816 kwargs regressed"
        )
        self.last_prompt: str | None = None
        self.last_user_id: str | None = None

    async def execute_task(self, prompt: str, user_id: str = "default_user_session"):
        self.last_prompt = prompt
        self.last_user_id = user_id
        return _execution_result()


@pytest.mark.unit
class TestSwarmExecuteRoute:
    def test_swarm_execute_returns_real_orchestration_result(self, monkeypatch):
        import api.routes.agent_tasks as agent_tasks
        from api.dependencies import get_current_user_token

        monkeypatch.setattr(agent_tasks, "ZeroCostSwarmOrchestrator", FakeZeroCostOrchestrator)

        app = FastAPI()
        app.include_router(agent_tasks.router)
        app.dependency_overrides[get_current_user_token] = lambda: {"sub": "user-1"}
        client = TestClient(app)

        res = client.post(
            "/api/v1/agents/swarm/execute",
            json={"task": "write a haiku about CI", "user_id": "user-1", "session_id": "s-1"},
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["status"] == "completed"
        assert body["session_id"] == "s-1"
        assert body["task_id"] == "t-1"
        results = body["results"]
        assert results["passed_qa"] is True
        assert results["feedback"] == "all green"
        assert results["work_product"] == {"code": "print('hello')", "analysis": "looks good"}
        assert results["errors"] == []

    def test_swarm_execute_does_not_read_nonexistent_workspace_attrs(self, monkeypatch):
        """The old response read workspace.generated_code / architecture_design —
        attributes that never existed on SharedWorkspace (AttributeError)."""
        import api.routes.agent_tasks as agent_tasks
        from api.dependencies import get_current_user_token

        captured: dict = {}

        class SpyOrch(FakeZeroCostOrchestrator):
            async def execute_task(self, prompt, user_id="default_user_session"):
                ws = _workspace()
                # The REAL model has none of the old phantom attributes:
                for phantom in ("generated_code", "architecture_design"):
                    assert not hasattr(ws, phantom), f"SharedWorkspace grew '{phantom}'?"
                captured["ws_fields"] = sorted(ws.model_dump().keys())
                return _execution_result()

        monkeypatch.setattr(agent_tasks, "ZeroCostSwarmOrchestrator", SpyOrch)
        app = FastAPI()
        app.include_router(agent_tasks.router)
        app.dependency_overrides[get_current_user_token] = lambda: {"sub": "user-1"}
        client = TestClient(app)
        res = client.post("/api/v1/agents/swarm/execute", json={"task": "x"})
        assert res.status_code == 200
        assert "work_product" in captured["ws_fields"]


# ───────────────────── path 2: wrapper forwarding + /agent/action ─────────────────────


@pytest.mark.unit
class TestRunDagForwarding:
    async def test_wrapper_forwards_run_dag_for_workspace(self):
        from core.zero_cost_architecture.swarm_orchestrator_integration import (
            ZeroCostSwarmOrchestrator,
        )

        calls: list[tuple] = []

        class FakeOriginal:
            async def run_dag_for_workspace(self, workspace, user_id="default_user_session"):
                calls.append((workspace, user_id))
                workspace.log("dag ran")
                return workspace

        orch = object.__new__(ZeroCostSwarmOrchestrator)  # skip heavy __init__
        orch._original_orchestrator = FakeOriginal()

        ws = _workspace()
        out = await orch.run_dag_for_workspace(ws, user_id="u-9")
        assert out is ws
        assert calls == [(ws, "u-9")]
        assert "dag ran" in ws.execution_logs

    def test_agent_action_sync_no_longer_500(self, monkeypatch):
        """Slack/Notion/GitHub sync actions used to 500 with AttributeError —
        lock the full route path with the forwarding in place."""
        import api.routes.agent_action as agent_action
        from api.dependencies import get_current_user_token
        from database.session import get_db_session

        class FakeOrch:
            async def run_dag_for_workspace(self, workspace, user_id="default_user_session"):
                workspace.work_product["integration_result"] = {"status": "sent", "ts": "123"}
                return workspace

        monkeypatch.setattr(agent_action, "ZeroCostSwarmOrchestrator", FakeOrch)
        monkeypatch.setattr(
            agent_action.tool_policy_gateway,
            "enforce",
            _noop_enforce,
        )
        monkeypatch.setattr(agent_action, "decrypt_token", lambda enc: "plain-token")

        class FakeScalarResult:
            def scalar_one_or_none(self):
                return SimpleNamespace(encrypted_access_token="enc-token")

        class FakeDB:
            async def execute(self, stmt):
                return FakeScalarResult()

        app = FastAPI()
        app.include_router(agent_action.router)
        app.dependency_overrides[get_current_user_token] = lambda: {"sub": "user-1"}
        app.dependency_overrides[get_db_session] = lambda: FakeDB()
        client = TestClient(app)

        res = client.post(
            "/agent/action",
            json={"target_platform": "slack", "content": "deploy done", "context": {}},
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["status"] == "success"
        assert body["result"]["status"] == "sent"


async def _noop_enforce(**kwargs):
    return None
