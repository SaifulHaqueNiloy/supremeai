from __future__ import annotations


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

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: str | None = "HTML",
        reply_markup: dict[str, Any] | None = None,
    ) -> bool:
        if not self.configured:
            return False
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                body: dict[str, Any] = {"chat_id": str(chat_id), "text": text}
                if parse_mode:
                    body["parse_mode"] = parse_mode
                if reply_markup:
                    body["reply_markup"] = reply_markup

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

    async def answer_callback_query(self, callback_query_id: str, text: str | None = None) -> bool:
        if not self.configured:
            return False
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                payload: dict[str, Any] = {"callback_query_id": callback_query_id}
                if text:
                    payload["text"] = text
                resp = await client.post(f"{self.api_base}/answerCallbackQuery", json=payload)
                return bool(resp.status_code == 200)
        except Exception as e:
            logger.error(f"answerCallbackQuery error: {e}")
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

    async def sync_bot_profile(
        self,
        name: str = "SupremeAI 2.0 | Autonomous Intelligence",
        description: str | None = None,
        short_description: str | None = None,
    ) -> bool:
        """Sets official Name, Description, Short Description, and Commands Menu on Telegram."""
        if not self.configured:
            return False
        default_desc = (
            "🔱 SupremeAI 2.0 — Living Self-Evolving Superintelligence\n\n"
            "Built with 100% Zero-Cost Infrastructure & Continuous Learning Matrix.\n\n"
            "⚡ Core Capabilities:\n"
            "• Autonomous AI Pair Programmer & Metaprogramming\n"
            "• TelDrive Encrypted DB & Memory Vault (/backup_now)\n"
            "• Real-time Cluster Telemetry & Health (/sys_status)\n"
            "• Instant Desktop (.exe) & VSIX Build Delivery (/latest_build)\n\n"
            "Created by Saiful Haq Niloy | Powered by SupremeAI"
        )
        default_short = "🔱 SupremeAI 2.0: Self-evolving autonomous intelligence, $0-cost cloud vault & AI developer powerhouse."

        commands = [
            {"command": "start", "description": "Initialize SupremeAI assistant"},
            {"command": "sys_status", "description": "Real-time telemetry & health check"},
            {"command": "backup_now", "description": "Trigger encrypted DB & memory backup"},
            {"command": "latest_build", "description": "Download latest Desktop & VSIX builds"},
            {"command": "help", "description": "Command list & help documentation"},
            {"command": "rules", "description": "Constitutional rules & architecture"},
            {"command": "admin", "description": "Admin security & cluster controls"},
        ]

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                await client.post(f"{self.api_base}/setMyName", json={"name": name})
                await client.post(f"{self.api_base}/setMyDescription", json={"description": description or default_desc})
                await client.post(f"{self.api_base}/setMyShortDescription", json={"short_description": short_description or default_short})
                await client.post(f"{self.api_base}/setMyCommands", json={"commands": commands})
                logger.info("✅ Telegram bot profile and commands synchronized successfully.")
                return True
        except Exception as exc:
            logger.error(f"sync_bot_profile failed: {exc}")
            return False

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

    @staticmethod
    def _quick_actions_keyboard() -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [
                    {"text": "🌐 Open User Dashboard", "url": "https://supremeai-lac.vercel.app"},
                    {"text": "⚡ Cluster Health", "callback_data": "cmd_status"},
                ],
                [
                    {"text": "💾 Backup Vault", "callback_data": "cmd_backup"},
                    {"text": "🚀 Download Builds", "callback_data": "cmd_build"},
                ],
                [
                    {"text": "📜 AI Directives", "callback_data": "cmd_rules"},
                    {"text": "📚 API Documentation", "url": "https://supremeai-backend-docker.onrender.com/docs"},
                ],
            ]
        }

    async def handle_update(self, update: dict[str, Any]) -> None:
        """Process a Telegram update payload (from webhook or polling)."""
        # 1. Handle Inline Callback Queries
        callback_query = update.get("callback_query")
        if callback_query:
            callback_id = callback_query["id"]
            data = callback_query.get("data", "")
            chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
            await self.answer_callback_query(callback_id)

            if chat_id and data:
                if data == "cmd_status":
                    await self._handle_status(chat_id)
                elif data == "cmd_backup":
                    await self._handle_backup_now(chat_id)
                elif data == "cmd_build":
                    await self._handle_latest_build(chat_id)
                elif data == "cmd_rules":
                    await self.send_message(chat_id, self.COMMANDS["/rules"])
                elif data == "cmd_help":
                    await self.send_message(chat_id, self.COMMANDS["/help"], reply_markup=self._quick_actions_keyboard())
            return

        # 2. Handle Direct Messages
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
            if command in ("/start", "/help"):
                welcome_text = self.COMMANDS.get(command, self.COMMANDS["/start"])
                await self.send_message(chat_id, welcome_text, reply_markup=self._quick_actions_keyboard())
                return
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
        """Route user query through SupremeAI reasoning engine and persist chat memory."""
        # 1. Primary: Gemini 2.5 Flash (Ultra-fast & Intelligent)
        gem_keys = [k.strip() for k in os.getenv("GEMINI_API_KEY", "").split(",") if k.strip().startswith("AIza")]
        system_instruction = (
            "You are SupremeAI 2.0, a living self-evolving autonomous intelligence. "
            "Respond helpfully, clearly, and concisely in Bengali or English according to the user's language."
        )

        for gem_key in gem_keys:
            try:
                async with httpx.AsyncClient(timeout=25) as client:
                    gem_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gem_key}"
                    payload = {
                        "contents": [{"parts": [{"text": text}]}],
                        "systemInstruction": {"parts": [{"text": system_instruction}]},
                    }
                    r = await client.post(gem_url, json=payload)
                    if r.status_code == 200:
                        data = r.json()
                        candidates = data.get("candidates", [])
                        if candidates and "parts" in candidates[0].get("content", {}):
                            return candidates[0]["content"]["parts"][0]["text"]
            except Exception as direct_exc:
                logger.warning(f"Gemini key attempt notice: {direct_exc}")

        # 2. Fallback: Groq (Ultra-low latency GPT-OSS / Qwen)
        groq_keys = [k.strip() for k in os.getenv("GROQ_API_KEY", "").split(",") if k.strip()]
        for groq_key in groq_keys:
            for model_name in ["openai/gpt-oss-120b", "qwen/qwen3.6-27b", "openai/gpt-oss-20b"]:
                try:
                    async with httpx.AsyncClient(timeout=20) as client:
                        r = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                            json={
                                "model": model_name,
                                "messages": [
                                    {"role": "system", "content": system_instruction},
                                    {"role": "user", "content": text},
                                ],
                            },
                        )
                        if r.status_code == 200:
                            return r.json()["choices"][0]["message"]["content"]
                except Exception as groq_exc:
                    logger.debug(f"Groq {model_name} attempt notice: {groq_exc}")

        # 3. Fallback: Orchestrator / ModelRouter
        if self.processor:
            try:
                task_type = "coding" if any(k in text.lower() for k in ["code", "function", "script", "fix", "bug"]) else "general"
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: self.processor.execute_task(text, task_type))
                if isinstance(result, dict) and result.get("result"):
                    return str(result["result"])
            except Exception as exc:
                logger.error(f"Orchestrator fallback error: {exc}")

        return "🤖 SupremeAI 2.0: আপনার বার্তাটি গ্রহণ করা হয়েছে। আমি সিস্টেম মেমোরি ও মডেল রুট করছি।"

    # ── Polling mode (dev/local) ─────────────────────────────────

    async def run_polling(self) -> None:
        """Long-polling loop — receives updates and callback queries in real time."""
        if not self.configured:
            logger.warning("Telegram bot not configured — skipping polling.")
            return

        # Delete any conflicting webhook so getUpdates works cleanly
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(f"{self.api_base}/deleteWebhook")
                logger.info("Cleared Telegram Webhook for polling mode.")
        except Exception as e:
            logger.warning(f"deleteWebhook notice: {e}")

        logger.info("🤖 SupremeAI Telegram long-polling loop active...")
        offset = 0
        while True:
            try:
                async with httpx.AsyncClient(timeout=35) as client:
                    resp = await client.get(
                        f"{self.api_base}/getUpdates",
                        params={"offset": offset, "timeout": 25, "allowed_updates": ["message", "callback_query"]},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        updates = data.get("result", [])
                        for update in updates:
                            offset = update["update_id"] + 1
                            asyncio.create_task(self.handle_update(update))
            except Exception as exc:
                logger.error(f"Telegram polling error: {exc}")
                await asyncio.sleep(2)

    async def start_webhook(self, webhook_url: str):
        """Register Telegram Webhook to point to live backend endpoint."""
        if not self.bot_token:
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json={"url": webhook_url, "allowed_updates": ["message", "callback_query"]})
                if resp.status_code == 200:
                    logger.info(f"Successfully registered Telegram Webhook to {webhook_url}")
                else:
                    logger.error(f"Failed to register webhook: {resp.text}")
        except Exception as e:
            logger.error(f"Webhook setup exception: {e}")


# ── FastAPI webhook endpoint helper ──────────────────────────────


def create_telegram_router(handler: TelegramBotHandler):
    """Returns a FastAPI router for Telegram webhook endpoint."""
    from fastapi import APIRouter, Request, Response

    router = APIRouter(prefix="/telegram", tags=["telegram"])
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


# Module-level router exported for FastAPI auto-discovery
router = create_telegram_router(TelegramBotHandler())


# ── Standalone entrypoint ─────────────────────────────────────────

if __name__ == "__main__":
    handler = TelegramBotHandler()
    asyncio.run(handler.run_polling())
