"""Tests for agents/research_assistant.py — Research assistant agent."""
import pytest
from agents.research_assistant import ResearchAssistant


class TestResearchAssistant:
    def test_init(self):
        agent = ResearchAssistant()
        assert agent is not None

    @pytest.mark.asyncio
    async def test_research_returns_results(self):
        agent = ResearchAssistant()
        result = await agent.research("What is machine learning?")
        assert result is not None

    @pytest.mark.asyncio
    async def test_research_with_sources(self):
        agent = ResearchAssistant()
        result = await agent.research("quantum computing basics")
        assert result is not None
        assert "sources" in result or "findings" in result

    @pytest.mark.asyncio
    async def test_summarize_findings(self):
        agent = ResearchAssistant()
        result = await agent.summarize(["fact 1", "fact 2", "fact 3"])
        assert result is not None
        assert isinstance(result, str)
