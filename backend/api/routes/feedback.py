from __future__ import annotations

import asyncio
import json
import sqlite3
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.degraded_mode import sqlite_fallback_allowed
from core.feedback_loop import FeedbackLoop
from core.logging_config import logger


def _get_db_path() -> Path:
    base = Path("data")
    try:
        base.mkdir(parents=True, exist_ok=True)
        return base / "feedback.db"
    except PermissionError:
        fallback = Path(tempfile.gettempdir()) / "data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback / "feedback.db"


DB_PATH = _get_db_path()
_feedback_loop = FeedbackLoop()


def _ensure_db() -> None:
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        import logging

        logging.getLogger(__name__).exception(f"Silenced error: {e}")
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """)
        conn.commit()
    finally:
        conn.close()


def _persist_feedback(event_type: str, payload: dict[str, Any]) -> None:
    # P0 (Task 9-c2): only the SQLite persistence is gated. The in-memory
    # FeedbackLoop above keeps the route fully functional; when the SQLite
    # fallback is refused in production we skip persistence loudly (CRITICAL
    # logged once by core.degraded_mode) instead of crashing the route.
    if not sqlite_fallback_allowed("feedback_events"):
        logger.warning(
            "[P0] feedback event NOT persisted: SQLite fallback refused in "
            "production (in-memory handling only). Set SUPABASE_ALLOW_DB_DEGRADATION=true "
            "to accept the ephemeral fallback."
        )
        return
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.execute(
            "INSERT INTO feedback_events (event_type, payload, created_at) VALUES (?, ?, ?)",
            (event_type, json.dumps(payload), time.time()),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.error(f"feedback persist failed: {exc}")


@asynccontextmanager
async def feedback_lifespan(router: APIRouter):
    # P0: skip SQLite schema creation entirely when the fallback is refused —
    # the route keeps working with in-memory handling only.
    if sqlite_fallback_allowed("feedback_events"):
        _ensure_db()
    yield


from api.dependencies import get_current_user_token

router = APIRouter(
    prefix="/api/feedback",
    tags=["feedback"],
    lifespan=feedback_lifespan,
    dependencies=[Depends(get_current_user_token)],
)


class FeedbackEvent(BaseModel):
    event_type: str
    payload: dict[str, Any] | None = None


class FeedbackResponse(BaseModel):
    success: bool
    event_id: int | None = None


@router.post("/ingest", response_model=FeedbackResponse)
async def ingest(event: FeedbackEvent) -> FeedbackResponse:
    try:
        payload = event.payload or {}
        handled = _feedback_loop.handle_feedback({"type": event.event_type, **payload})
        if handled.get("stored"):
            _persist_feedback(event.event_type, payload)
            return FeedbackResponse(success=True)
        raise HTTPException(
            status_code=400, detail=handled.get("reason", "Unsupported feedback type")
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"feedback ingest failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
