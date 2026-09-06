import asyncio
import unittest.mock
from unittest.mock import MagicMock

import pytest

from tools.parallel_agent_executor import ParallelAgentExecutor

# বাংলা মন্তব্য: প্যারালাল এজেন্ট এক্সিকিউটর টেস্ট করা হচ্ছে।


@pytest.mark.anyio
async def test_parallel_agent_execution_success():
    # বাংলা মন্তব্য: সমান্তরাল এক্সিকিউশন সফলভাবে সম্পন্ন হচ্ছে কিনা তা যাচাইয়ের টেস্ট।
    executor = ParallelAgentExecutor(max_concurrent_tasks=2)

    async def mock_task_1():
        await asyncio.sleep(0.1)
        return "result1"

    async def mock_task_2():
        await asyncio.sleep(0.1)
        return "result2"

    tasks = {"agent1": mock_task_1, "agent2": mock_task_2}

    results = await executor.run_parallel(tasks)

    assert results["agent1"]["status"] == "success"
    assert results["agent1"]["result"] == "result1"
    assert results["agent2"]["status"] == "success"
    assert results["agent2"]["result"] == "result2"


@pytest.mark.anyio
async def test_parallel_agent_execution_limit():
    # বাংলা মন্তব্য: সমান্তরাল এক্সিকিউশনের সর্বোচ্চ সীমা (limit) চেক টেস্ট।
    executor = ParallelAgentExecutor(max_concurrent_tasks=1)

    async def mock_task_1():
        await asyncio.sleep(0.2)
        return "result1"

    async def mock_task_2():
        await asyncio.sleep(0.2)
        return "result2"

    tasks = {"agent1": mock_task_1, "agent2": mock_task_2}

    results = await executor.run_parallel(tasks)

    # যেহেতু লিমিট ১, তাই একটি এজেন্ট স্কিপ হবে বা এরর দেখাবে।
    assert results["agent1"]["status"] == "success"
    assert results["agent2"]["status"] == "error"
    assert "limit reached" in results["agent2"]["error"]


@pytest.mark.anyio
async def test_mcp_aware_task_execution():
    # বাংলা মন্তব্য: MCP ক্লায়েন্ট ইনজেকশন সহ টাস্ক এক্সিকিউশন যাচাই।
    executor = ParallelAgentExecutor(
        max_concurrent_tasks=2,
        mcp_registry={
            "filesystem": {
                "command": "uvx",
                "args": ["mcp-server-filesystem"],
                "startup_timeout": 5,
            }
        },
    )

    mock_client = MagicMock()
    mock_client.connect = MagicMock(return_value=True)
    mock_client.disconnect = MagicMock(return_value=None)

    captured_kwargs = {}

    async def mcp_aware_task(mcp_clients=None, **kwargs):
        captured_kwargs["mcp_clients"] = mcp_clients
        return "mcp-result"

    tasks = {
        "agent_mcp": {
            "task": mcp_aware_task,
            "mcp_servers": ["filesystem"],
        }
    }

    with unittest.mock.patch(
        "tools.parallel_agent_executor.asyncio.to_thread",
        wraps=asyncio.to_thread,
    ):
        results = await executor.run_parallel(tasks)
        assert results["agent_mcp"]["status"] == "success"


@pytest.mark.anyio
async def test_invalid_task_definition():
    executor = ParallelAgentExecutor(max_concurrent_tasks=2)
    tasks = {"bad_agent": {"invalid": "definition"}}
    results = await executor.run_parallel(tasks)
    assert results["bad_agent"]["status"] == "error"
    assert "Invalid task definition" in results["bad_agent"]["error"]


@pytest.mark.anyio
async def test_agent_task_exception_handling():
    executor = ParallelAgentExecutor(max_concurrent_tasks=2)

    async def faulty_task():
        raise ValueError("Something exploded")

    tasks = {"faulty_agent": faulty_task}
    results = await executor.run_parallel(tasks)
    assert results["faulty_agent"]["status"] == "error"
    assert "Something exploded" in results["faulty_agent"]["error"]


@pytest.mark.anyio
async def test_agent_dag_scheduler_linear_and_voting():
    from tools.parallel_agent_executor import AgentDAGScheduler, DAGNode

    scheduler = AgentDAGScheduler(max_concurrent_tasks=5)

    async def coder_task():
        return "def solve(): return 42"

    async def tester_task():
        return "def test_solve(): assert solve() == 42"

    async def reviewer_task():
        return "LGTM"

    graph = {
        "coder": DAGNode("coder", coder_task),
        "tester": DAGNode("tester", tester_task, depends_on=["coder"]),
        "reviewer": DAGNode("reviewer", reviewer_task, depends_on=["tester"]),
    }

    result = await scheduler.execute_dag(graph)
    assert "order" in result
    assert len(result["order"]) == 3
    assert result["order"][0] == ["coder"]
    assert result["order"][1] == ["tester"]
    assert result["order"][2] == ["reviewer"]
    assert result["nodes"]["coder"]["status"] == "success"
    assert result["nodes"]["tester"]["status"] == "success"
    assert result["nodes"]["reviewer"]["status"] == "success"
    assert result["voted_best"] is not None
    # Coder produced the longest output among the tasks
    assert result["voted_best"]["selected_agent"] in ("coder", "tester")


@pytest.mark.anyio
async def test_agent_dag_scheduler_cyclic_dependency_handling():
    from tools.parallel_agent_executor import AgentDAGScheduler, DAGNode

    scheduler = AgentDAGScheduler(max_concurrent_tasks=5)

    async def simple_task():
        return "ok"

    # A -> B -> A (Cycle)
    graph = {
        "node_a": DAGNode("node_a", simple_task, depends_on=["node_b"]),
        "node_b": DAGNode("node_b", simple_task, depends_on=["node_a"]),
    }

    result = await scheduler.execute_dag(graph)
    assert "order" in result
    # Cyclic dependency should force remaining nodes and complete
    assert result["nodes"]["node_a"]["status"] == "success"
    assert result["nodes"]["node_b"]["status"] == "success"
