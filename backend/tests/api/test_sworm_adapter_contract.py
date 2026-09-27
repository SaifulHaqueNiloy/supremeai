"""Issue #1816: ZeroCostSwarmOrchestrator adapter contract tests.

Pins the two reconnected surfaces:
- POST /api/v1/agents/swarm/execute uses the adapter's REAL API
  (constructor takes config only; execute_task(prompt, user_id) →
  ExecutionResult{workspace{work_product,test_results},errors})
- ZeroCostSwarmOrchestrator.run_dag_for_workspace forwards to the composed
  original SwarmOrchestrator (agent_action.py sync actions)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from api.deps import get_current_user_token
from core.app import app
from core.zero_cost_architecture.swarm_orchestrator_integration import (
    ZeroCostSwarmOrchestrator,
)

client = TestClient(app)

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture()
def user_auth():
    saved = app.dependency_overrides.get(get_current_user_token)
    app.dependency_overrides[get_current_user_token] = lambda: {
        "sub": "test-user-id",
        "role": "user",
    }
    yield
    if saved is None:
        app.dependency_overrides.pop(get_current_user_token, None)
    else:
        app.dependency_overrides[get_current_user_token] = saved


class _FakeWorkspace:
    def __init__(self):
        self.test_results = {"passed": True, "feedback": "all good"}
        self.work_product = {"generated_code": "print('hi')", "architecture": "monolith"}
        self.errors: list[str] = []


class _FakeResult:
    def __init__(self):
        self.task_id = "t-123"
        self.status = "completed"
        self.workspace = _FakeWorkspace()
        self.errors: list[str] = []


class _FakeOrchestrator:
    """Stands in for the adapter — same public API the endpoint must use."""

    def __init__(self, *args, **kwargs):
        if kwargs:
            raise TypeError("adapter takes config-only kwargs")
        self.execute_task = AsyncMock(return_value=_FakeResult())

    async def execute(self, *a, **k):  # must NOT be called
        raise AssertionError("adapter has no execute(); endpoint must use execute_task")


def test_swarm_execute_uses_real_adapter_contract(user_auth, monkeypatch):
    import api.routes.agent_tasks as agent_tasks_module

    fake = _FakeOrchestrator()
    monkeypatch.setattr(agent_tasks_module, "ZeroCostSwarmOrchestrator", lambda *a, **k: fake)
    resp = client.post(
        "/api/v1/agents/swarm/execute",
        json={"task": "build a widget", "user_id": "u-1"},
        headers=AUTH,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    fake.execute_task.assert_awaited_once_with("build a widget", "u-1")
    results = body["results"]
    assert results["task_id"] == "t-123"
    assert results["passed_qa"] is True
    assert results["generated_code"] == "print('hi')"
    assert results["architecture"] == "monolith"
    assert results["work_product"]["generated_code"] == "print('hi')"


async def test_run_dag_for_workspace_forwards_to_original():
    """agent_action.py sync actions depend on this forwarded method."""

    # anyio mode=auto runs async tests
    fake_self = MagicMock()
    fake_self._original_orchestrator = MagicMock()
    fake_self._original_orchestrator.run_dag_for_workspace = AsyncMock(return_value="WS")
    out = await ZeroCostSwarmOrchestrator.run_dag_for_workspace(fake_self, "WS-OBJ", user_id="u-9")
    assert out == "WS"
    fake_self._original_orchestrator.run_dag_for_workspace.assert_awaited_once_with(
        "WS-OBJ", user_id="u-9"
    )
