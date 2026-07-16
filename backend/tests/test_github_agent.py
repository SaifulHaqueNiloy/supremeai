import pytest
from tools.devops.github_agent import GitHubAgent


@pytest.mark.asyncio
async def test_github_agent_repo_connect():
    agent = GitHubAgent()
    res = await agent.connect_repo("test-owner", "test-repo")
    assert res["status"] == "success"


@pytest.mark.asyncio
async def test_github_agent_analyze():
    agent = GitHubAgent()
    analysis = await agent.analyze_repo("https://github.com/test/repo")
    assert "score" in analysis
    assert len(analysis["issues"]) > 0


@pytest.mark.asyncio
async def test_github_agent_pr_creation():
    agent = GitHubAgent()
    improvements = {"src/db.py": "Optimize pooling"}
    res = await agent.create_improvement_pr("test/repo", improvements)
    assert res["status"] == "success"
    assert "supremeai-improvements" in res["branch"]
    assert "pr_url" in res
