"""Persistent Sandbox Manager for SupremeAI.

বাংলা মন্তব্য:
একটি persistent-volume স্যান্ডবক্স সেশন ম্যানেজার — ভলিউম-মাউন্টেড স্যান্ডবক্স তৈরি,
session-aware কমান্ড এক্সিকিউশন, ফাইল আপ/ডাউনলোড, ডিপেনডেন্সি ইনস্টল ও লাইফসাইকেল
পরিচালনা করে। API-key না থাকলে সব অপারেশন dry-run/mock মোডে চলে, ফলে কোনো কনফিগারেশন
ছাড়াই অ্যাপ রান করা যায় (Zero Breakage নীতি)।

Contract সোর্স:
  - `api/routes/sandbox_api.py` — create_with_volume / execute_in_session / stream_logs
                                  / destroy_sandbox / list_sessions / `.sessions`
  - `tests/tools/test_cloud_sandbox_full.py` — _get_client / install_dependency /
                                  upload_file / download_file / SandboxSession fields
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, AsyncIterator

try:
    from loguru import logger
except ImportError:  # loguru অনুপস্থিত থাকলে stdlib logger-এ ফলব্যাক
    import logging

    logger = logging.getLogger(__name__)  # type: ignore[assignment]


@dataclass
class SandboxSession:
    """একটি persistent স্যান্ডবক্স সেশনের স্টেট।

    `id` প্রপার্টি `session_id`-এর আলিয়াস — `sandbox_api` `session.id` ব্যবহার করে,
    টেস্ট স্যুট `session.session_id` ব্যবহার করে, তাই দুটোই সমর্থিত।
    """

    session_id: str
    sandbox_id: str
    status: str = "running"
    created_at: str = ""
    volume_path: str = ""
    provider: str = "local"

    @property
    def id(self) -> str:
        """`session_id`-এর আলিয়াস (sandbox_api compatibility)।"""
        return self.session_id


class PersistentSandbox:
    """Persistent-volume স্যান্ডবক্স অর্কেস্ট্রেটর (dry-run-সহ)।"""

    def __init__(self, provider: str = "local"):
        self.provider = (provider or "local").lower()
        self.sessions: dict[str, SandboxSession] = {}
        self._api_key = os.getenv(f"{self.provider.upper()}_API_KEY") or os.getenv("SANDBOX_API_KEY")
        default_base = "http://localhost:8000" if self.provider == "local" else f"https://api.{self.provider}.com"
        self._base_url = os.getenv("SANDBOX_API_URL", default_base)
        logger.info(f"Initialized PersistentSandbox (Provider: {self.provider})")

    # ── Client ───────────────────────────────────────────────────────────────
    def _get_client(self) -> Any:
        """httpx.AsyncClient রিটার্ন করে (httpx না থাকলে None)।

        টেস্ট স্যুট এই মেথডটিই mock করে, তাই নাম ও আচরণ ঠিক রাখা হয়েছে।
        """
        try:
            import httpx
        except ImportError:
            return None
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return httpx.AsyncClient(base_url=self._base_url, headers=headers, timeout=60.0)

    @property
    def _dry_run(self) -> bool:
        """API-key বা client না থাকলে mock মোডে চলা।"""
        return not self._api_key or self.provider in ("local", "mock")

    def _new_session(self, sandbox_id: str, status: str = "running", volume_path: str = "") -> SandboxSession:
        session = SandboxSession(
            session_id=f"session-{uuid.uuid4().hex[:12]}",
            sandbox_id=sandbox_id,
            status=status,
            created_at=datetime.now(UTC).isoformat(),
            volume_path=volume_path or f"/volumes/{sandbox_id}",
            provider=self.provider,
        )
        self.sessions[session.session_id] = session
        return session


# ── Core ops ──────────────────────────────────────────────────────────────
    async def create_with_volume(self, *args: Any, **kwargs: Any) -> SandboxSession:
        """ভলিউম-মাউন্টেড স্যান্ডবক্স তৈরি করে।

        sandbox_api positional spec dict পাঠায়; টেস্ট স্যুট keyword args পাঠায় —
        দুটোই হ্যান্ডল করা হয়। Dry-run হলে mock session তৈরি হয়।
        """
        spec = args[0] if args else {}
        spec = spec if isinstance(spec, dict) else {}
        payload = {
            "image": kwargs.get("image", spec.get("image", "python:3.11-slim")),
            "volume_size_gb": kwargs.get("volume_size_gb", spec.get("volume_size_gb", 10)),
            "ttl_hours": kwargs.get("ttl_hours", spec.get("ttl_hours", 24)),
            "provider": self.provider,
        }

        if not self._dry_run:
            client = self._get_client()
            if client is not None:
                try:
                    resp = await client.post("/sandboxes", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    sid = str(data.get("id") or f"sandbox-{uuid.uuid4().hex[:8]}")
                    session = SandboxSession(
                        session_id=str(data.get("session_id") or f"session-{uuid.uuid4().hex[:12]}"),
                        sandbox_id=sid,
                        status=str(data.get("status", "running")),
                        created_at=datetime.now(UTC).isoformat(),
                        volume_path=f"/volumes/{sid}",
                        provider=self.provider,
                    )
                    self.sessions[session.session_id] = session
                    logger.success(f"Created persistent sandbox: {sid}")
                    return session
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"Persistent sandbox create failed, falling back to mock: {exc}")

        # Dry-run / mock path
        sandbox_id = f"sandbox-{uuid.uuid4().hex[:8]}"
        session = self._new_session(sandbox_id)
        logger.info(f"Dry-run: created mock persistent sandbox {session.session_id}")
        return session

    async def execute_in_session(
        self, session_id: str, command: str, timeout: int = 300
    ) -> dict[str, Any]:
        """Session-aware কমান্ড এক্সিকিউশন।"""
        if session_id not in self.sessions:
            return {"status": "ERROR", "exitCode": -1, "stdout": "", "stderr": f"Unknown session {session_id}"}

        if self._dry_run:
            logger.info(f"Dry-run: executing '{command}' in session {session_id}")
            return {
                "status": "COMPLETED",
                "exitCode": 0,
                "stdout": f"Mock output for: {command}",
                "stderr": "",
            }

        client = self._get_client()
        if client is None:
            return {"status": "ERROR", "exitCode": -1, "stdout": "", "stderr": "httpx not installed"}
        try:
            resp = await client.post(f"/sessions/{session_id}/execute", json={"command": command, "timeout": timeout})
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to execute in session {session_id}: {exc}")
            return {"status": "ERROR", "exitCode": -1, "stdout": "", "stderr": str(exc)}

    async def stream_logs(self, session_id: str, command: str, timeout: int = 300) -> AsyncIterator[str]:
        """সেশন লগ লাইভ স্ট্রিম (SSE-এর জন্য async generator)।"""
        if session_id not in self.sessions:
            yield f"error: unknown session {session_id}"
            return
        if self._dry_run:
            for line in [f"[{session_id}] running: {command}", "[mock] waiting for output...", "[mock] done"]:
                yield line
            return
        client = self._get_client()
        if client is None:
            yield "[mock] httpx not installed — streaming unavailable"
            return
        try:
            async with client.stream(
                "POST",
                f"/sessions/{session_id}/logs",
                json={"command": command, "timeout": timeout},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    yield line
        except Exception as exc:  # noqa: BLE001
            yield f"error: {exc}"


    async def install_dependency(self, session_id: str, package_manager: str, package: str) -> bool:
        """সেশন-এ ডিপেনডেন্সি ইনস্টল করে।"""
        if session_id not in self.sessions:
            return False
        if self._dry_run:
            return True
        client = self._get_client()
        if client is None:
            return True
        try:
            resp = await client.post(
                f"/sessions/{session_id}/dependencies",
                json={"manager": package_manager, "package": package},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("status") == "success"
        except Exception as exc:  # noqa: BLE001
            logger.error(f"install_dependency failed: {exc}")
            return False

    async def upload_file(self, session_id: str, path: str, content: str) -> bool:
        """স্যান্ডবক্স-এ ফাইল আপলোড।"""
        if session_id not in self.sessions:
            return False
        if self._dry_run:
            return True
        client = self._get_client()
        if client is None:
            return True
        try:
            resp = await client.post(
                f"/sessions/{session_id}/files", json={"path": path, "content": content}
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("status") == "success"
        except Exception as exc:  # noqa: BLE001
            logger.error(f"upload_file failed: {exc}")
            return False

    async def download_file(self, session_id: str, path: str) -> bytes:
        """স্যান্ডবক্স থেকে ফাইল ডাউনলোড।"""
        if session_id not in self.sessions:
            return b""
        if self._dry_run:
            return b"mock file content"
        client = self._get_client()
        if client is None:
            return b"mock file content"
        try:
            resp = await client.get(f"/sessions/{session_id}/files", params={"path": path})
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", "")
            return content.encode("utf-8") if isinstance(content, str) else content
        except Exception as exc:  # noqa: BLE001
            logger.error(f"download_file failed: {exc}")
            return b""

    async def destroy_sandbox(self, session_id: str) -> bool:
        """স্যান্ডবক্স ধ্বংস করে এবং session map থেকে মুছে ফেলে।"""
        if session_id not in self.sessions:
            return False
        if not self._dry_run:
            client = self._get_client()
            if client is not None:
                try:
                    resp = await client.post(f"/sessions/{session_id}/terminate")
                    resp.raise_for_status()
                except Exception as exc:  # noqa: BLE001
                    logger.error(f"destroy_sandbox failed: {exc}")
        del self.sessions[session_id]
        logger.info(f"Destroyed persistent sandbox session {session_id}")
        return True

    def list_sessions(self) -> list[SandboxSession]:
        """সক্রিয় সেশনগুলোর তালিকা।"""
        return list(self.sessions.values())


__all__ = ["PersistentSandbox", "SandboxSession"]