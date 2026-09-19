"""Issue #704 regression: in-process LLM codegen exec must fail-closed by default.

``tools.ephemeral_synthesizer`` and ``services.tool_forge`` execute
LLM-generated Python via in-process ``exec()``. Restricted builtins are not a
security boundary, so with no ``SUPREMEAI_ALLOW_INPROCESS_CODEGEN`` env var
(the production/staging default) nothing may execute:

- the ephemeral synthesizer returns a structured ``status="rejected"`` result,
- the tool forge raises its existing ``ToolForgeError``.
"""

import pytest

from core.security.codegen_gate import ALLOW_INPROCESS_CODEGEN_ENV
from services.tool_forge import ToolForgeError, ToolForgeService, ToolSpec
from tools.ephemeral_synthesizer import EphemeralToolSynthesizer

_SAFE_CODE = """
def run(x: int, y: int) -> int:
    return x * y + 10
"""


@pytest.mark.asyncio
async def test_ephemeral_synthesizer_fail_closed_by_default(monkeypatch):
    """No env var -> script is NOT executed, structured rejection returned."""
    monkeypatch.delenv(ALLOW_INPROCESS_CODEGEN_ENV, raising=False)
    synthesizer = EphemeralToolSynthesizer()

    res = await synthesizer.execute_ephemeral_script(
        tool_name="must_not_run",
        script_code=_SAFE_CODE,
        input_args={"x": 5, "y": 6},
    )

    assert res.status == "rejected"
    assert res.result is None
    assert res.ast_safe is False
    assert ALLOW_INPROCESS_CODEGEN_ENV in (res.error or "")


@pytest.mark.asyncio
async def test_ephemeral_synthesizer_opt_in_executes(monkeypatch):
    """Explicit local-dev opt-in keeps the restricted exec path working."""
    monkeypatch.setenv(ALLOW_INPROCESS_CODEGEN_ENV, "true")
    synthesizer = EphemeralToolSynthesizer()

    res = await synthesizer.execute_ephemeral_script(
        tool_name="multiply_add",
        script_code=_SAFE_CODE,
        input_args={"x": 5, "y": 6},
    )

    assert res.status == "succeeded"
    assert res.result == 40


def test_tool_forge_fail_closed_by_default(monkeypatch):
    """No env var -> forged tool is registered but exec raises ToolForgeError."""
    monkeypatch.delenv(ALLOW_INPROCESS_CODEGEN_ENV, raising=False)
    service = ToolForgeService()
    spec = ToolSpec(name="adder", description="Adds two numbers")
    tool = service.forge_tool(
        spec,
        "def adder(a, b):\n    raise RuntimeError('executed while gate is off')\n",
    )
    assert tool.is_safe is True

    with pytest.raises(ToolForgeError, match=ALLOW_INPROCESS_CODEGEN_ENV):
        service.execute_tool(tool, {"a": 1, "b": 2})


def test_tool_forge_opt_in_executes(monkeypatch):
    """Explicit local-dev opt-in keeps the restricted exec path working."""
    monkeypatch.setenv(ALLOW_INPROCESS_CODEGEN_ENV, "true")
    service = ToolForgeService()
    spec = ToolSpec(name="adder", description="Adds two numbers")
    tool = service.forge_tool(spec, "def adder(a, b):\n    return a + b\n")

    assert service.execute_tool(tool, {"a": 2, "b": 3}) == 5
