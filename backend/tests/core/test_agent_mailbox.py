"""Tests for core/agent_mailbox.py — Agent mailbox messaging."""
import pytest
from core.agent_mailbox import AgentMailbox


class TestAgentMailbox:
    def test_init(self):
        mb = AgentMailbox()
        assert mb is not None

    def test_send_message(self):
        mb = AgentMailbox()
        mb.send("agent-1", {"type": "task", "data": "hello"})
        messages = mb.read("agent-1")
        assert len(messages) >= 1

    def test_read_empty_mailbox(self):
        mb = AgentMailbox()
        messages = mb.read("agent-nonexistent")
        assert isinstance(messages, list)
        assert len(messages) == 0

    def test_clear_mailbox(self):
        mb = AgentMailbox()
        mb.send("agent-1", {"type": "task"})
        mb.clear("agent-1")
        assert len(mb.read("agent-1")) == 0

    def test_multiple_agents_isolated(self):
        mb = AgentMailbox()
        mb.send("a1", {"msg": "for a1"})
        mb.send("a2", {"msg": "for a2"})
        assert len(mb.read("a1")) == 1
        assert len(mb.read("a2")) == 1

    def test_message_order_fifo(self):
        mb = AgentMailbox()
        mb.send("a1", {"order": 1})
        mb.send("a1", {"order": 2})
        mb.send("a1", {"order": 3})
        messages = mb.read("a1")
        assert messages[0]["order"] == 1
        assert messages[2]["order"] == 3
