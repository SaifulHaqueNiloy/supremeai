"""Firestore-style in-app session store endpoints (VaultPage sync API).

Split out of the former single-module api/routes/browser.py verbatim.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel

from api.routes.browser import router

# ──────────────────────────────────────────────
# বাংলা মন্তব্য: সেশন স্টোর — Firestore-ভিত্তিক সেশন সিঙ্ক (VaultPage-এর মত ব্যাকএন্ড API কল)
# ──────────────────────────────────────────────
SESSIONS: dict[str, dict[str, Any]] = {}


class SessionMessageIn(BaseModel):
    id: int
    sender: str
    text: str
    timestamp: str


class SessionIn(BaseModel):
    id: str
    title: str
    status: str = "running"
    created_at: str = ""
    updated_at: str = ""
    messages: list[SessionMessageIn] = []


@router.get("/sessions")
def list_sessions():
    """বাংলা মন্তব্য: সব সেশন তালিকা রিটার্ন করে"""
    return {"sessions": list(SESSIONS.values())}


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    """বাংলা মন্তব্য: নির্দিষ্ট সেশন রিটার্ন করে"""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    return SESSIONS[session_id]


@router.post("/sessions")
def create_session(session: SessionIn):
    """বাংলা মন্তব্য: নতুন সেশন তৈরি করে"""
    now = datetime.now(UTC).isoformat()
    data = session.model_dump()
    if not data.get("created_at"):
        data["created_at"] = now
    if not data.get("updated_at"):
        data["updated_at"] = now
    SESSIONS[session.id] = data
    return {"success": True, "session": data}


@router.put("/sessions/{session_id}")
def update_session(session_id: str, session: SessionIn):
    """বাংলা মন্তব্য: বিদ্যমান সেশন আপডেট করে"""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    data = session.model_dump()
    data["updated_at"] = datetime.now(UTC).isoformat()
    SESSIONS[session_id] = data
    return {"success": True, "session": data}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """বাংলা মন্তব্য: সেশন মুছে ফেলে"""
    SESSIONS.pop(session_id, None)
    return {"success": True}
