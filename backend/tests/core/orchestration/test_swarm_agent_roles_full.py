"""Coverage-completion tests for core/orchestration/swarm_agent_roles.py.

Task 7-b. All LLM gateway / skill-manager / experience-db dependencies are
mocked — no network, no DB.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.orchestration import swarm_agent_roles as sar
from core.orchestration.swarm_agent_roles import (
    ArchitectureAgent,
    CodeGeneratorAgent,
    GuardianAgent,
    IntegrationAgent,
    QAAgent,
    ReflectionAgent,
    ResearchAgent,
    SwarmAgentBase,
    ToolExecutorAgent,
    ToolSynthesizerAgent,
)
from models.shared_workspace import SharedWorkspace


def make_workspace(**kwargs) -> SharedWorkspace:
    return SharedWorkspace(task_id="task-1", original_prompt="build me a thing", **kwargs)


@pytest.fixture
def gateway(monkeypatch):
    gw = MagicMock()
    gw.acompletion = AsyncMock(return_value={"choices": [{"message": {"content": "LLM-OUTPUT"}}]})
    monkeypatch.setattr(sar, "llm_gateway", gw)
    return gw


@pytest.fixture
def skills(monkeypatch):
    sm = MagicMock()
    skill = MagicMock()
    skill.execute = AsyncMock(return_value="SKILL-OUTPUT")
    sm.get_skill = AsyncMock(return_value=skill)
    monkeypatch.setattr(sar, "skill_manager", sm)
    return sm


@pytest.fixture
def experience_db(monkeypatch):
    recorded: list = []
    mod = types.ModuleType("adaptive_engine.experience_db")

    class Experience:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class ExperienceDatabase:
        def __init__(self):
            pass

        def record_experience(self, exp):
            recorded.append(exp)

    mod.Experience = Experience
    mod.ExperienceDatabase = ExperienceDatabase
    monkeypatch.setitem(sys.modules, "adaptive_engine.experience_db", mod)
    return recorded


# ---------------------------------------------------------------------------
# SwarmAgentBase
# ---------------------------------------------------------------------------
class TestSwarmAgentBase:
    async def test_run_is_abstract(self):
        with pytest.raises(NotImplementedError, match="must be implemented"):
            await SwarmAgentBase().run(make_workspace(), "user", "model")

    async def test_call_gateway_returns_content(self, gateway):
        out = await SwarmAgentBase().call_gateway("sys", "user", "uid", "model")
        assert out == "LLM-OUTPUT"
        messages = gateway.acompletion.await_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    async def test_call_gateway_malformed_response_is_empty_string(self, gateway):
        gateway.acompletion = AsyncMock(return_value={})
        out = await SwarmAgentBase().call_gateway("sys", "user")
        assert out == ""

    async def test_use_skill_executes(self, skills):
        out = await SwarmAgentBase().use_skill("SomeSkill", workspace=make_workspace())
        assert out == "SKILL-OUTPUT"

    async def test_use_skill_value_error_reraised(self, skills):
        skills.get_skill = AsyncMock(side_effect=ValueError("skill missing"))
        with pytest.raises(ValueError, match="skill missing"):
            await SwarmAgentBase().use_skill("SomeSkill", workspace=make_workspace())

    async def test_safe_skill_run_success(self, skills):
        ws = make_workspace()
        out = await SwarmAgentBase()._safe_skill_run("SomeSkill", workspace=ws)
        assert out == "SKILL-OUTPUT"

    async def test_safe_skill_run_value_error_falls_back_to_none(self, skills):
        skills.get_skill = AsyncMock(side_effect=ValueError("unavailable"))
        ws = make_workspace()
        out = await SwarmAgentBase()._safe_skill_run("SomeSkill", workspace=ws)
        assert out is None
        assert any("fallback" in msg.lower() for msg in ws.execution_logs)


# ---------------------------------------------------------------------------
# ArchitectureAgent
# ---------------------------------------------------------------------------
class TestArchitectureAgent:
    async def test_design(self, gateway):
        ws = make_workspace()
        await ArchitectureAgent().design(ws, "user-1", "model-x")
        assert ws.work_product["architecture_design"] == "LLM-OUTPUT"
        assert any("architecture" in m.lower() for m in ws.execution_logs)

    async def test_run_uses_skill(self, skills):
        ws = make_workspace()
        await ArchitectureAgent().run(ws, "user-1", "model-x")
        assert ws.work_product["architecture_design"] == "SKILL-OUTPUT"


# ---------------------------------------------------------------------------
# CodeGeneratorAgent
# ---------------------------------------------------------------------------
class TestCodeGeneratorAgent:
    async def test_generate_code(self, gateway):
        ws = make_workspace()
        await CodeGeneratorAgent().generate_code(ws, "user-1")
        assert ws.work_product["generated_code"] == {"main.py": "LLM-OUTPUT"}

    async def test_refine(self, gateway):
        ws = make_workspace()
        ws.work_product["generated_code"] = {"main.py": "original code"}
        await CodeGeneratorAgent().refine(ws, "fix the bug", "user-1")
        assert ws.work_product["generated_code"]["main.py"] == "LLM-OUTPUT"

    async def test_run_uses_skill(self, skills):
        ws = make_workspace()
        await CodeGeneratorAgent().run(ws, "user-1")
        assert ws.work_product["generated_code"] == {"main.py": "SKILL-OUTPUT"}


# ---------------------------------------------------------------------------
# QAAgent
# ---------------------------------------------------------------------------
class TestQAAgent:
    @pytest.fixture
    def scanner(self, monkeypatch):
        # verify() does ImmuneSystemScanner() then instance.scan_code(...), so
        # the patched class must RETURN the instance that owns scan_code.
        instance = MagicMock()
        instance.scan_code = MagicMock(return_value={"safe": True})
        cls = MagicMock(return_value=instance)
        monkeypatch.setattr("core.immune_system.ImmuneSystemScanner", cls, raising=False)
        return instance

    async def test_verify_safe(self, gateway, scanner):
        ws = make_workspace()
        ws.work_product["generated_code"] = {"main.py": "print('hi')"}
        await QAAgent().verify(ws, "user-1")
        assert ws.test_results["safe"] is True
        assert ws.test_results["passed"] is True
        assert ws.test_results["feedback"] == "LLM-OUTPUT"

    async def test_verify_unsafe(self, gateway, scanner):
        scanner.scan_code = MagicMock(return_value={"safe": False, "error": "injection"})
        ws = make_workspace()
        ws.work_product["generated_code"] = {"main.py": "eval('x')"}
        await QAAgent().verify(ws, "user-1")
        assert ws.test_results["safe"] is False
        assert ws.test_results["error"] == "injection"
        assert ws.test_results["feedback"] == "LLM-OUTPUT"

    async def test_run_uses_skill(self, skills):
        ws = make_workspace()
        await QAAgent().run(ws, "user-1")
        assert ws.test_results["feedback"] == "SKILL-OUTPUT"


# ---------------------------------------------------------------------------
# GuardianAgent
# ---------------------------------------------------------------------------
class TestGuardianAgent:
    async def test_validate_no_code_approved(self, gateway):
        ws = make_workspace()
        approved, feedback = await GuardianAgent().validate(ws, "user-1")
        assert approved is True
        assert "No code to analyze" in feedback

    async def test_validate_all_subagents_pass(self, gateway):
        gateway.acompletion = AsyncMock(
            return_value={"choices": [{"message": {"content": "SECURITY_OK"}}]}
        )
        ws = make_workspace()
        ws.work_product["generated_code"] = {"main.py": "print('hi')"}
        approved, feedback = await GuardianAgent().validate(ws, "user-1")
        assert approved is True
        assert feedback == "APPROVED"
        assert gateway.acompletion.await_count == 4  # four specialized sub-agents

    async def test_validate_violations_found(self, gateway):
        gateway.acompletion = AsyncMock(
            return_value={"choices": [{"message": {"content": "VIOLATION: secret leak"}}]}
        )
        ws = make_workspace()
        ws.work_product["generated_code"] = {"main.py": "print('hi')"}
        approved, feedback = await GuardianAgent().validate(ws, "user-1")
        assert approved is False
        assert feedback.startswith("FAILED")
        assert "VIOLATIONS FROM SecuritySentinel" in feedback

    async def test_run_persists_verdict(self, gateway):
        gateway.acompletion = AsyncMock(
            return_value={"choices": [{"message": {"content": "QUALITY_OK"}}]}
        )
        ws = make_workspace()
        ws.work_product["generated_code"] = {"main.py": "print('hi')"}
        await GuardianAgent().run(ws, "user-1")
        assert ws.work_product["is_approved"] is True
        assert ws.work_product["guardian_feedback"] == "APPROVED"


# ---------------------------------------------------------------------------
# ResearchAgent
# ---------------------------------------------------------------------------
class TestResearchAgent:
    async def test_analyze(self, gateway):
        ws = make_workspace()
        await ResearchAgent().analyze(ws, "user-1")
        assert ws.work_product["research_summary"] == "LLM-OUTPUT"

    async def test_run_uses_skill(self, skills):
        ws = make_workspace()
        await ResearchAgent().run(ws, "user-1")
        assert ws.work_product["research_summary"] == "SKILL-OUTPUT"


# ---------------------------------------------------------------------------
# ReflectionAgent
# ---------------------------------------------------------------------------
class TestReflectionAgent:
    async def test_reflect_and_persist_valid_json(self, gateway, experience_db):
        gateway.acompletion = AsyncMock(
            return_value={
                "choices": [
                    {
                        "message": {
                            "content": '{"what_worked": ["w1"], "what_failed": ["f1"], '
                            '"suggested_improvements": ["i1"]}'
                        }
                    }
                ]
            }
        )
        ws = make_workspace(intent="code_generation")
        out = await ReflectionAgent().reflect_and_persist(ws, "user-1")
        assert "what_worked" in out
        assert len(experience_db) == 1
        exp = experience_db[0]
        assert exp.what_worked == ["w1"]
        assert exp.what_failed == ["f1"]
        assert exp.suggested_improvements == ["i1"]
        assert any("successfully saved" in m for m in ws.execution_logs)

    async def test_reflect_and_persist_invalid_json_falls_back(self, gateway, experience_db):
        gateway.acompletion = AsyncMock(
            return_value={"choices": [{"message": {"content": "not json at all"}}]}
        )
        ws = make_workspace()
        await ReflectionAgent().reflect_and_persist(ws, "user-1")
        exp = experience_db[0]
        assert exp.what_worked == ["not json at all"]
        assert exp.what_failed == []

    async def test_reflect_and_persist_db_failure_logged(self, gateway, monkeypatch):
        mod = types.ModuleType("adaptive_engine.experience_db")
        mod.Experience = lambda **kw: types.SimpleNamespace(**kw)

        class ExplodingDB:
            def __init__(self):
                raise RuntimeError("vector db down")

        mod.ExperienceDatabase = ExplodingDB
        monkeypatch.setitem(sys.modules, "adaptive_engine.experience_db", mod)

        ws = make_workspace()
        await ReflectionAgent().reflect_and_persist(ws, "user-1")
        assert any("Failed to persist" in m for m in ws.execution_logs)

    async def test_run_uses_skill(self, skills):
        ws = make_workspace()
        await ReflectionAgent().run(ws, "user-1")  # result intentionally discarded


# ---------------------------------------------------------------------------
# ToolSynthesizerAgent
# ---------------------------------------------------------------------------
class TestToolSynthesizerAgent:
    async def test_synthesize(self, gateway):
        gateway.acompletion = AsyncMock(
            return_value={
                "choices": [{"message": {"content": '{"name": "auto_tool", "params": []}'}}]
            }
        )
        ws = make_workspace()
        await ToolSynthesizerAgent().synthesize(ws, "user-1")
        assert ws.work_product["synthesized_tool"]["name"] == "auto_tool"

    async def test_run_uses_skill(self, skills):
        skill = MagicMock()
        skill.execute = AsyncMock(return_value={"name": "skill_tool"})
        skills.get_skill = AsyncMock(return_value=skill)
        ws = make_workspace()
        await ToolSynthesizerAgent().run(ws, "user-1")
        assert ws.work_product["synthesized_tool"]["name"] == "skill_tool"


# ---------------------------------------------------------------------------
# ToolExecutorAgent
# ---------------------------------------------------------------------------
class TestToolExecutorAgent:
    async def test_execute_with_no_tools(self):
        ws = make_workspace()
        await ToolExecutorAgent().execute(ws, "user-1")
        assert any("No tools available" in m for m in ws.execution_logs)
        assert "execution_result" not in ws.work_product

    async def test_execute_first_tool(self):
        ws = make_workspace()
        ws.work_product["available_tools"] = ["tool_a", "tool_b"]
        await ToolExecutorAgent().execute(ws, "user-1")
        assert ws.work_product["execution_result"] == "Successfully executed tool: tool_a"

    async def test_run_uses_skill(self, skills):
        ws = make_workspace()
        await ToolExecutorAgent().run(ws, "user-1")


# ---------------------------------------------------------------------------
# IntegrationAgent
# ---------------------------------------------------------------------------
class TestIntegrationAgent:
    @pytest.mark.parametrize(
        "intent,skill_name",
        [
            ("sync_to_slack", "SlackIntegrationSkill"),
            ("sync_to_notion", "NotionSyncSkill"),
            ("sync_to_github", "GithubSyncSkill"),
        ],
    )
    async def test_known_intents(self, skills, intent, skill_name):
        ws = make_workspace(intent=intent)
        await IntegrationAgent().run(ws, "user-1")
        assert skills.get_skill.await_args.args[0] == skill_name
        assert ws.work_product["integration_result"] == "SKILL-OUTPUT"

    async def test_unknown_intent_error_result(self, skills):
        ws = make_workspace(intent="sync_to_telepathy")
        await IntegrationAgent().run(ws, "user-1")
        result = ws.work_product["integration_result"]
        assert result["status"] == "error"
        assert "sync_to_telepathy" in result["message"]
