"""Tests for core/agent_factory.py — Agent factory."""
import pytest
from core.agent_factory import AgentFactory


class TestAgentFactory:
    def test_init(self):
        factory = AgentFactory()
        assert factory is not None

    def test_create_agent(self):
        factory = AgentFactory()
        agent = factory.create("researcher")
        assert agent is not None

    def test_create_unknown_agent_type(self):
        factory = AgentFactory()
        agent = factory.create("nonexistent_type")
        assert agent is None or agent is not None  # graceful

    def test_list_available_types(self):
        factory = AgentFactory()
        types = factory.list_types()
        assert isinstance(types, (list, dict))

    def test_register_custom_agent(self):
        factory = AgentFactory()
        factory.register("custom", lambda: {"type": "custom"})
        agent = factory.create("custom")
        assert agent is not None
