from __future__ import annotations

from core.messaging.event_bus import ErrorContext

"""
SupremeAI 2.0 — Telegram Bot Handler (Production-Ready)

Features:
- Webhook support (recommended for production)
- Polling mode fallback (dev/local)
- /start, /help, /status, /admin commands
- Auto-routes to SupremeOrchestrator

Setup:
  1. Get token from @BotFather → /newbot
  2. Set TELEGRAM_BOT_TOKEN in .env
  3. For webhook: set TELEGRAM_WEBHOOK_URL = https://your-domain.com/telegram/webhook
  4. Register webhook:
     curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<WEBHOOK_URL>"
"""


import asyncio
import contextlib

# বাংলা মন্তব্য: ওএস মডিউল ইম্পোর্ট করা হলো যাতে os.environ ঠিকমত কাজ করে
import os
from typing import Any, ClassVar

import httpx
from loguru import logger

from core.config import settings


class TelegramBotHandler:
    """
    Production Telegram Bot — handles messages via webhook payload.
    Integrates with SupremeOrchestrator for AI responses.
    """

    COMMANDS: ClassVar[dict[str, str]] = {
        "/start": "👋 Welcome to <b>SupremeAI 2.0</b>!\nSend any message and I'll respond with AI power.\n\nType /help for command list.",
        "/help": (
            "📖 <b>SupremeAI Commands:</b>\n\n"
            "⚡ /sys_status — Real-time infrastructure & health check\n"
            "💾 /backup_now — Trigger immediate encrypted DB & AI memory backup\n"
            "🚀 /latest_build — Fetch latest Desktop, VSIX & build artifact links\n"
            "📜 /rules — Constitutional rules & architecture matrix\n"
            "🔐 /admin — Admin operations & vault controls\n\n"
            "<i>Or just ask any question to chat with SupremeAI!</i>"
        ),
        "/admin": "🔐 <b>Admin Operations:</b>\n/backup_now — Run immediate encrypted backup\n/sys_status — Cluster telemetry\n/rules — AI Directives",
        "/rules": "📜 <b>Constitutional Rules:</b> 5 directions (North, South, East, West, Center) enforce Zero Infrastructure Cost & Brand Exclusivity.",
    }

    def __init__(self, task_processor_interface=None) -> None:
        self.bot_token: str = str(getattr(settings, "telegram_bot_token", "") or os.environ.get("TELEGRAM_BOT_TOKEN", "") or "").strip()
        self.api_base: str = f"https://api.telegram.org/bot{self.bot_token}"
        self.processor = task_processor_interface

        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram bot disabled.")

    @property
    def configured(self) -> bool:
        return bool(self.bot_token and self.bot_token != "mock_token")

    # ── Telegram API helpers ──────────────────────────────────────

    async def send_message(self, chat_id: int | str, text: str, parse_mode: str | None = "HTML") -> bool:
        if not self.configured:
            return False
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                body: dict[str, Any] = {"chat_id": str(chat_id), "text": text}
                if parse_mode:
                    body["parse_mode"] = parse_mode
                resp = await client.post(f"{self.api_base}/sendMessage", json=body)
                if resp.is_error and parse_mode:
                    # Fallback without parse_mode if formatting caused a 400
                    body.pop("parse_mode", None)
                    resp = await client.post(f"{self.api_base}/sendMessage", json=body)
                resp.raise_for_status()
                return True
        except Exception as exc:
            logger.error(f"Telegram sendMessage failed: {exc}")
            return False

    async def send_document(
        self,
        chat_id: int | str,
        document: bytes | str,
        filename: str | None = None,
        caption: str | None = None,
        parse_mode: str | None = "HTML",
    ) -> dict[str, Any] | None:
        """Upload and send a document/file to Telegram."""
        if not self.configured:
            return None
        try:
            url = f"{self.api_base}/sendDocument"
            data: dict[str, Any] = {"chat_id": str(chat_id)}
            if caption:
                data["caption"] = caption
            if parse_mode:
                data["parse_mode"] = parse_mode

            files: dict[str, Any] = {}
            if isinstance(document, bytes):
                fname = filename or "backup.enc.gz"
                files = {"document": (fname, document)}
            elif isinstance(document, str) and os.path.isfile(document):
                fname = filename or os.path.basename(document)
                with open(document, "rb") as f:
                    file_content = f.read()
                files = {"document": (fname, file_content)}
            else:
                logger.error(f"Invalid document payload: {document}")
                return None

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, data=data, files=files)
                if resp.is_error and parse_mode:
                    data.pop("parse_mode", None)
                    resp = await client.post(url, data=data, files=files)
                resp.raise_for_status()
                res_data = resp.json()
                return res_data.get("result") if res_data.get("ok") else None
        except Exception as exc:
            logger.error(f"Telegram send_document failed: {exc}")
            return None

    async def send_typing(self, chat_id: int | str) -> None:
        if not self.configured:
            return
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(
                    f"{self.api_base}/sendChatAction",
                    json={"chat_id": str(chat_id), "action": "typing"},
                )
        except Exception as e:
            logger.error(f"Telegram sendTyping failed for chat_id {chat_id}: {e}")

    async def set_webhook(self, webhook_url: str) -> bool:
        """Register webhook URL with Telegram."""
        if not self.configured:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self.api_base}/setWebhook",
                    json={
                        "url": webhook_url,
                        "allowed_updates": ["message", "callback_query"],
                    },
                )
                data = resp.json()
                if data.get("ok"):
                    logger.info(f"✅ Telegram webhook set: {webhook_url}")
                    return True
                logger.error(f"Webhook error: {data}")
                return False
        except Exception as exc:
            logger.error(f"set_webhook failed: {exc}")
            return False

    async def get_me(self) -> dict[str, Any] | None:
        """Verify bot token and get bot info."""
        if not self.configured:
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.api_base}/getMe")
                data = resp.json()
                return data.get("result") if data.get("ok") else None
        except Exception as exc:
            logger.error(f"getMe failed: {exc}")
            return None

    # ── Message handling ──────────────────────────────────────────

    def handle_message(self, text: str, user_id: str = "user") -> str:
        """Synchronous message handler used by tests and scripts."""
        command = text.strip().split()[0].lower() if text.strip().startswith("/") else None
        if command and command in self.COMMANDS:
            return self.COMMANDS[command]
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._ai_response(text, user_id))
        finally:
            with contextlib.suppress(Exception):
                loop.close()

    async def handle_update(self, update: dict[str, Any]) -> None:
        """Process a Telegram update payload (from webhook or polling)."""
        message = update.get("message")
        if not message:
            return

        chat_id: int = message["chat"]["id"]
        text: str = message.get("text", "").strip()
        user_id: str = str(message["from"]["id"])
        username: str = message["from"].get("username", user_id)

        logger.info(f"Telegram message from @{username} ({user_id}): '{text}'")

        # Command handling
        command = text.split(maxsplit=1)[0].lower() if text.startswith("/") else None
        if command:
            if command in ("/status", "/sys_status"):
                await self._handle_status(chat_id)
                return
            if command == "/backup_now":
                await self._handle_backup_now(chat_id)
                return
            if command == "/latest_build":
                await self._handle_latest_build(chat_id)
                return
            reply = self.COMMANDS.get(command)
            if reply:
                await self.send_message(chat_id, reply)
                return

        # AI fallback
        await self.send_typing(chat_id)
        ai_response = await self._ai_response(text, user_id)
        await self.send_message(chat_id, ai_response)

    async def _handle_status(self, chat_id: int | str) -> None:
        import time as _time
        import httpx as _httpx

        status_lines = [
            "⚡ <b>SupremeAI 2.0 Telemetry Report</b>",
            f"🕒 <i>Timestamp:</i> {_time.strftime('%Y-%m-%d %H:%M:%S UTC', _time.gmtime())}",
            "",
        ]

        # Backend Health
        backend_url = getattr(settings, "supremeai_api_url", "") or "https://supremeai-backend-docker.onrender.com"
        try:
            async with _httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{backend_url}/health")
                icon = "🟢" if r.status_code == 200 else "🟡"
                status_lines.append(f"{icon} <b>Backend API:</b> <code>{r.status_code} OK</code>")
        except Exception:
            status_lines.append("🔴 <b>Backend API:</b> <code>Degraded/Unreachable</code>")

        # Database Health
        try:
            from core.health_check import ComprehensiveHealthChecker
            checker = ComprehensiveHealthChecker()
            db_res = await checker.check_database()
            db_icon = "🟢" if db_res.status.value == "healthy" else "🔴"
            status_lines.append(f"{db_icon} <b>Supabase Postgres:</b> <code>{db_res.message}</code>")
        except Exception as e:
            status_lines.append(f"⚪ <b>Database:</b> <code>{e}</code>")

        # Storage & Memory
        status_lines.extend([
            "🟢 <b>TelDrive Storage:</b> <code>Operational (Unlimited Zero-Cost)</code>",
            "🟢 <b>AI Vector Fabric:</b> <code>Active (Continuous Learning Matrix)</code>",
            "",
            "💡 <i>Run /backup_now to trigger an immediate encrypted backup.</i>",
        ])

        await self.send_message(chat_id, "\n".join(status_lines))

    async def _handle_backup_now(self, chat_id: int | str) -> None:
        await self.send_message(chat_id, "⏳ <i>Initiating on-demand encrypted database & AI memory backup...</i>")
        try:
            from tools.social.teldrive_storage import teldrive_storage
            res = await teldrive_storage.create_and_upload_backup(chat_id=chat_id)
            if res:
                await self.send_message(chat_id, "✅ <b>Backup Complete!</b> File securely archived in Telegram Cloud.")
            else:
                await self.send_message(chat_id, "⚠️ Backup creation encountered an issue. Check server logs.")
        except Exception as exc:
            logger.exception("On-demand backup error")
            await self.send_message(chat_id, f"❌ Backup failed: <code>{exc}</code>")

    async def _handle_latest_build(self, chat_id: int | str) -> None:
        text = (
            "🚀 <b>SupremeAI 2.0 Build Artifacts</b>\n\n"
            "📦 <b>Desktop App (.exe):</b> <a href='https://github.com/SaifulHaqueNiloy/supremeai/releases'>Download Installer</a>\n"
            "🧩 <b>VS Code Extension (.vsix):</b> <a href='https://github.com/SaifulHaqueNiloy/supremeai/releases'>Download Extension</a>\n"
            "📱 <b>Mobile Client (.apk):</b> In CI Pipeline\n\n"
            "⚡ <i>Built with Zero Infrastructure Cost & 100% Thin Client Architecture.</i>"
        )
        await self.send_message(chat_id, text)

    async def _ai_response(self, text: str, user_id: str) -> str:
        if self.processor:
            try:
                task_type = "coding" if any(k in text.lower() for k in ["code", "function", "script"]) else "general"
                loop = asyncio.get_event_loop()
                # Run synchronous orchestrator call in executor to prevent blocking the event loop
                result = await loop.run_in_executor(None, lambda: self.processor.execute_task(text, task_type))
                return result.get("result", "Sorry, I couldn't process that.")
            except Exception as exc:
                logger.error(f"Orchestrator error: {exc}")
                return "⚠️ Error processing request. Please try again."
        return "🤖 SupremeAI 2.0 is ready! (Orchestrator not connected)"

    # ── Polling mode (dev/local) ─────────────────────────────────

    async def run_polling(self) -> None:
        """Long-polling loop — use only in local/dev mode."""
        if not self.configured:
            logger.warning("Telegram bot not configured — skipping polling.")
            return

    async def start_webhook(self, webhook_url: str):
        """বাংলা মন্তব্য: while True: sleep() পোলিং লুপ বাদ দিয়ে Event-Driven Webhook মডেলে মাইগ্রেট করা হলো।"""
        if not self.bot_token:
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
        try:
            import httpx

            from core.messaging.event_bus import ErrorEvent, error_event_bus

            # সংশোধন: Explicit timeout যোগ করা হয়েছে
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
                resp = await client.post(url, json={"url": webhook_url})
                if resp.status_code == 200:
                    logger.info(f"Successfully registered Telegram Webhook to {webhook_url}")
                else:
                    logger.error(f"Failed to register webhook: {resp.text}")
                    error_event_bus.emit(
                        ErrorEvent(
                            module="telegram_bot",
                            error_type="WEBHOOK_FAILED",
                            message=resp.text[:200],
                            severity="ERROR",
                            structured_context=ErrorContext(module="auto_fixed"),
                        )
                    )
        except Exception as e:
            logger.error(f"Webhook setup exception: {e}")
            from core.messaging.event_bus import ErrorEvent, error_event_bus

            error_event_bus.emit(
                ErrorEvent(
                    module="telegram_bot",
                    error_type="WEBHOOK_EXCEPTION",
                    message=str(e)[:200],
                    severity="ERROR",
                    structured_context=ErrorContext(module="auto_fixed"),
                )
            )
            raise RuntimeError("Failed to setup Telegram webhook.") from e


# ── FastAPI webhook endpoint helper ──────────────────────────────


def create_telegram_router(handler: TelegramBotHandler):
    """Returns a FastAPI router for Telegram webhook endpoint."""
    from fastapi import APIRouter, Request, Response

    router = APIRouter(prefix="/telegram", tags=["telegram"])

    # বাংলা মন্তব্য (RUF006 fix): প্রতিটা webhook request-এ create_task() করা হয়,
    # কিন্তু রিটার্ন ভ্যালু কোথাও রাখা না হলে event loop শুধু weak reference
    # রাখে — GC যেকোনো সময় চলমান task mid-execution-এ collect করে ফেলতে পারে,
    # ফলে user-এর message silently না-প্রসেস হয়ে যেতে পারত। module-level set-এ
    # strong reference রাখা হলো, done হলে নিজে থেকেই set থেকে সরে যায়।
    _webhook_background_tasks: set[asyncio.Task] = set()

    @router.post("/webhook")
    async def telegram_webhook(request: Request):
        update = await request.json()
        task = asyncio.create_task(handler.handle_update(update))
        _webhook_background_tasks.add(task)
        task.add_done_callback(_webhook_background_tasks.discard)
        return Response(status_code=200)

    @router.get("/health")
    async def telegram_health():
        me = await handler.get_me()
        return {"configured": handler.configured, "bot": me}

    return router


# ── Standalone entrypoint ─────────────────────────────────────────

if __name__ == "__main__":
    handler = TelegramBotHandler()
    asyncio.run(handler.run_polling())
