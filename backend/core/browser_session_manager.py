"""Bounded, owner-scoped Playwright browser sessions.

The manager deliberately owns browser contexts rather than pages globally. A
context is isolated per session and is closed on explicit release or expiry.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Any

from core.logging_config import logger
from core.playwright_manager import get_global_browser


@dataclass
class BrowserSession:
    id: str
    owner_id: str
    context: Any
    page: Any
    created_at: float
    last_used_at: float


class BrowserSessionManager:
    def __init__(self, max_sessions: int = 3, idle_timeout_seconds: int = 900) -> None:
        self.max_sessions = max_sessions
        self.idle_timeout_seconds = idle_timeout_seconds
        self._sessions: dict[str, BrowserSession] = {}
        self._lock = asyncio.Lock()
        self._slots = asyncio.Semaphore(max_sessions)

    async def create(self, owner_id: str) -> BrowserSession:
        if not owner_id:
            raise ValueError("owner_id is required")
        await self._cleanup_expired()
        await self._slots.acquire()
        try:
            browser = await get_global_browser()
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            page = await context.new_page()
            session = BrowserSession(
                id=f"bs_{uuid.uuid4().hex}",
                owner_id=owner_id,
                context=context,
                page=page,
                created_at=time.time(),
                last_used_at=time.time(),
            )
            async with self._lock:
                self._sessions[session.id] = session
            return session
        except Exception:
            self._slots.release()
            raise

    async def get(self, session_id: str, owner_id: str) -> BrowserSession:
        async with self._lock:
            session = self._sessions.get(session_id)
        if session is None or session.owner_id != owner_id:
            raise KeyError("Browser session not found")
        if time.time() - session.last_used_at > self.idle_timeout_seconds:
            await self.close(session_id, owner_id)
            raise KeyError("Browser session expired")
        session.last_used_at = time.time()
        return session

    async def close(self, session_id: str, owner_id: str) -> bool:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.owner_id != owner_id:
                return False
            self._sessions.pop(session_id, None)
        try:
            await session.context.close()
        except Exception as exc:
            logger.warning("Browser context close failed for %s: %s", session_id, exc)
        finally:
            self._slots.release()
        return True

    async def _cleanup_expired(self) -> None:
        now = time.time()
        async with self._lock:
            expired = [
                session
                for session in self._sessions.values()
                if now - session.last_used_at > self.idle_timeout_seconds
            ]
        for session in expired:
            await self.close(session.id, session.owner_id)

    async def shutdown(self) -> None:
        async with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            try:
                await session.context.close()
            except Exception as exc:
                logger.warning("Browser context shutdown failed for %s: %s", session.id, exc)
            finally:
                self._slots.release()

    def snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "id": session.id,
                "owner_id": session.owner_id,
                "url": session.page.url,
                "created_at": session.created_at,
                "last_used_at": session.last_used_at,
            }
            for session in self._sessions.values()
        ]


session_manager = BrowserSessionManager()


async def shutdown_browser_sessions() -> None:
    await session_manager.shutdown()


__all__ = [
    "BrowserSession",
    "BrowserSessionManager",
    "session_manager",
    "shutdown_browser_sessions",
]


# বাংলা মন্তব্য: সেশন সীমা environment দিয়ে সামঞ্জস্য করা যায়, কিন্তু নিরাপদ default বজায় থাকে।


def configure_session_manager(max_sessions: int, idle_timeout_seconds: int) -> None:
    if max_sessions < 1 or idle_timeout_seconds < 1:
        raise ValueError("Browser session limits must be positive")
    session_manager.max_sessions = max_sessions
    session_manager.idle_timeout_seconds = idle_timeout_seconds
    session_manager._slots = asyncio.Semaphore(max_sessions)


__all__.append("configure_session_manager")
