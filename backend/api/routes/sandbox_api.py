"""
Sandbox API Routes
==================

Persistent cloud sandbox এর জন্য REST + SSE এন্ডপয়েন্ট।
Devin-এর মতো স্বায়ত্তশাসিত কোডিং ক্ষমতার জন্য এই রাউটগুলো ব্যবহৃত হয়।

Endpoints:
  POST /api/v1/sandbox/create   — নতুন persistent sandbox তৈরি
  POST /api/v1/sandbox/{id}/execute — কমান্ড রান করা
  GET  /api/v1/sandbox/{id}/logs     — লাইভ লগ স্ট্রিমিং (SSE)
  DELETE /api/v1/sandbox/{id}        — sandbox মুছে ফেলা
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.dependencies import get_current_user_token

# 🛡️ SECURITY FIX (CRITICAL): এই router-এর কোনো endpoint-এই আগে কোনো
# authentication ছিল না — POST /{sandbox_id}/execute সরাসরি manager-এর
# execute_in_session() কল করে sandbox-এ real শেল কমান্ড চালায় (স্টাব/ডামি
# না, প্রকৃত remote code execution)। কোনো auth ছাড়া যে কেউ /create দিয়ে
# একটা sandbox বানিয়ে /execute দিয়ে ইচ্ছামতো কমান্ড রান করতে পারত, /list
# দিয়ে সব sandbox দেখতে পারত এবং অন্যদের sandbox_id অনুমান করতে পারলে
# /{id}/execute বা /{id} DELETE দিয়ে সেগুলোও নিয়ন্ত্রণ/মুছে ফেলতে পারত।
# router-level auth যোগ করা হলো, বাকি sensitive router (tools_ops.py,
# admin.py ইত্যাদি) যে প্যাটার্ন ব্যবহার করে ঠিক সেভাবে।
router = APIRouter(prefix="/api/v1/sandbox", tags=["sandbox"], dependencies=[Depends(get_current_user_token)])

# বাংলা মন্তব্য: অ্যাপ্লিকেশন-স্কোপ স্যান্ডবক্স ম্যানেজার (singleton)।
_sandbox_manager: Any = None


def _get_manager():
    """PersistentSandbox ম্যানেজার লেজি-লোড করা হচ্ছে।"""
    global _sandbox_manager
    if _sandbox_manager is None:
        from core.orchestration.cloud_sandbox_orchestrator import PersistentSandbox

        _sandbox_manager = PersistentSandbox(provider="local")
    return _sandbox_manager


class CreateSandboxRequest(BaseModel):
    spec: dict[str, Any] | None = None
    provider: str = "local"


class ExecuteRequest(BaseModel):
    command: str
    timeout: int = 300


@router.post("/create")
async def create_sandbox(req: CreateSandboxRequest) -> dict[str, Any]:
    """নতুন persistent sandbox সেশন তৈরি করে।"""
    try:
        manager = _get_manager()
        session = await manager.create_with_volume(req.spec or {})
        return {
            "status": "success",
            "session_id": session.id,
            "volume_path": session.volume_path,
            "provider": session.provider,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{sandbox_id}/execute")
async def execute_command(sandbox_id: str, req: ExecuteRequest) -> dict[str, Any]:
    """স্যান্ডবক্স সেশনে একটি কমান্ড রান করে।"""
    manager = _get_manager()
    if sandbox_id not in manager._sessions:
        raise HTTPException(status_code=404, detail=f"Sandbox {sandbox_id} not found")
    result = await manager.execute_in_session(sandbox_id, req.command, timeout=req.timeout)
    return result


@router.get("/{sandbox_id}/logs")
async def stream_logs(sandbox_id: str, request: Request, command: str, timeout: int = 300):
    """লাইভ লগ স্ট্রিমিং (Server-Sent Events)।"""
    manager = _get_manager()
    if sandbox_id not in manager._sessions:
        raise HTTPException(status_code=404, detail=f"Sandbox {sandbox_id} not found")

    async def event_generator():
        # বাংলা মন্তব্য: ক্লায়েন্ট ডিসকানেক্ট করলে স্ট্রিম বন্ধ করা হচ্ছে।
        async for line in manager.stream_logs(sandbox_id, command, timeout=timeout):
            if await request.is_disconnected():
                break
            yield f"data: {line}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.delete("/{sandbox_id}")
async def destroy_sandbox(sandbox_id: str) -> dict[str, Any]:
    """স্যান্ডবক্স সেশন ও তার ভলিউম মুছে ফেলে।"""
    manager = _get_manager()
    success = await manager.destroy_sandbox(sandbox_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Sandbox {sandbox_id} not found or already destroyed",
        )
    return {"status": "success", "destroyed": sandbox_id}


@router.get("/list")
async def list_sandboxes() -> dict[str, Any]:
    """বর্তমানে থাকা সব স্যান্ডবক্স সেশনের তালিকা।"""
    manager = _get_manager()
    return {"status": "success", "sessions": manager.list_sessions()}
