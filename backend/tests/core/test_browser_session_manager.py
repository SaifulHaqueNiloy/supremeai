"""Tests for core/browser_session_manager.py — Browser session management."""
import pytest
from unittest.mock import AsyncMock, patch
from core.browser_session_manager import BrowserSessionManager


class TestBrowserSessionManager:
    def test_init(self):
        mgr = BrowserSessionManager()
        assert mgr is not None

    @pytest.mark.asyncio
    async def test_create_session(self):
        mgr = BrowserSessionManager()
        session = await mgr.create_session(user_id="user-1")
        assert session is not None
        assert "id" in session or hasattr(session, "id")

    @pytest.mark.asyncio
    async def test_get_session(self):
        mgr = BrowserSessionManager()
        created = await mgr.create_session(user_id="user-1")
        session = await mgr.get_session(created.get("id", "") if isinstance(created, dict) else created.id)
        assert session is not None

    @pytest.mark.asyncio
    async def test_close_session(self):
        mgr = BrowserSessionManager()
        session = await mgr.create_session(user_id="user-1")
        sid = session.get("id", "") if isinstance(session, dict) else session.id
        await mgr.close_session(sid)
        result = await mgr.get_session(sid)
        assert result is None or result.get("closed") is True

    @pytest.mark.asyncio
    async def test_list_sessions(self):
        mgr = BrowserSessionManager()
        await mgr.create_session(user_id="user-1")
        sessions = await mgr.list_sessions()
        assert isinstance(sessions, list)
