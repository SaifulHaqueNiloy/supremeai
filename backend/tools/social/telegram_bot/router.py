"""FastAPI webhook router for the Telegram bot (verbatim split artifact
of the former single-module telegram_bot.py).

Holds the import-time side effect from the original file —
``router = create_telegram_router(TelegramBotHandler())`` — re-exported
by the package so FastAPI auto-discovery (api/routers.py registry,
``importlib.import_module('tools.social.telegram_bot')`` → ``.router``)
keeps working unchanged.
"""

from __future__ import annotations

import asyncio

from .handler import TelegramBotHandler

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
