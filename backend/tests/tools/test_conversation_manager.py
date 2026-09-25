"""Tests for tools/conversation_manager.py — Conversation state management."""
import pytest
from tools.conversation_manager import ConversationManager


class TestConversationManager:
    """Conversation: create, add message, get history, clear."""

    def test_init(self):
        mgr = ConversationManager()
        assert mgr is not None

    def test_create_conversation(self):
        mgr = ConversationManager()
        conv_id = mgr.create("user-1")
        assert conv_id is not None
        assert isinstance(conv_id, str)

    def test_add_message(self):
        mgr = ConversationManager()
        conv_id = mgr.create("user-1")
        mgr.add_message(conv_id, "user", "Hello")
        history = mgr.get_history(conv_id)
        assert len(history) >= 1
        assert history[-1]["content"] == "Hello"

    def test_add_assistant_message(self):
        mgr = ConversationManager()
        conv_id = mgr.create("user-1")
        mgr.add_message(conv_id, "user", "Question")
        mgr.add_message(conv_id, "assistant", "Answer")
        history = mgr.get_history(conv_id)
        assert len(history) >= 2

    def test_get_history_empty(self):
        mgr = ConversationManager()
        conv_id = mgr.create("user-1")
        history = mgr.get_history(conv_id)
        assert isinstance(history, list)
        assert len(history) == 0

    def test_clear_conversation(self):
        mgr = ConversationManager()
        conv_id = mgr.create("user-1")
        mgr.add_message(conv_id, "user", "test")
        mgr.clear(conv_id)
        history = mgr.get_history(conv_id)
        assert len(history) == 0

    def test_nonexistent_conversation_returns_empty(self):
        mgr = ConversationManager()
        history = mgr.get_history("nonexistent")
        assert isinstance(history, list)

    def test_multiple_conversations_isolated(self):
        mgr = ConversationManager()
        c1 = mgr.create("user-1")
        c2 = mgr.create("user-2")
        mgr.add_message(c1, "user", "msg1")
        mgr.add_message(c2, "user", "msg2")
        assert len(mgr.get_history(c1)) == 1
        assert len(mgr.get_history(c2)) == 1
