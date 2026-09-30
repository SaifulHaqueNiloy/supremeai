"""OpenAI-Compatible Web AI Session Reverse Proxy Router (askalf + auth2api + g4f inspired).

বাংলা সারসংক্ষেপ:
------------------
SupremeAI-এর জিরো-কস্ট সেশন পুলকে স্ট্যান্ডার্ড OpenAI API (/v1/chat/completions)-এ
এক্সপোজ করার FastAPI রাউটার।
এর ফলে যে কোনো বাইরের টুল (Cursor, Cline, Aider, Claude Code, বা আমাদের নিজস্ব এজেন্ট)
একে স্ট্যান্ডার্ড OpenAI এন্ডপয়েন্ট হিসেবে ব্যবহার করতে পারে।
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from core.logging_config import logger
from core.web_ai_session_bridge import (
    WebAISessionError,
    global_session_pool,
)

router = APIRouter(prefix="/v1", tags=["web-ai-proxy"])


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="auto-zero-cost", description="কাঙ্ক্ষিত মডেল বা সার্ভিস")
    messages: list[ChatMessage] = Field(..., min_length=1)
    temperature: float | None = 0.7
    stream: bool = False


class AccountRegisterRequest(BaseModel):
    service: Literal["claude", "chatgpt", "v0"]
    token: str
    account_id: str | None = None


def _resolve_service_from_model(model_name: str) -> tuple[str, tuple[str, ...]]:
    """বাংলা মন্তব্য: মডেলের নাম থেকে প্রায়োরিটি সার্ভিস ও ফলব্যাক চেইন নির্ধারণ করা।"""
    m = model_name.lower().strip()
    if "claude" in m:
        return "claude", ("claude", "chatgpt", "v0")
    if "gpt" in m or "chatgpt" in m or "openai" in m:
        return "chatgpt", ("chatgpt", "claude", "v0")
    if "v0" in m:
        return "v0", ("v0", "claude", "chatgpt")
    # ডিফল্ট অটো চেইন
    return "claude", ("claude", "chatgpt", "v0")


@router.post("/chat/completions")
async def chat_completions(payload: ChatCompletionRequest):
    """
    বাংলা সারসংক্ষেপ:
    ------------------
    স্ট্যান্ডার্ড OpenAI /v1/chat/completions এন্ডপয়েন্ট।
    মাল্টি-অ্যাকাউন্ট রোটেশন এবং ক্রস-প্রোভাইডার ক্যাস্কেড সহ ইনফারেন্স চালায়।
    """
    preferred_service, fallback_chain = _resolve_service_from_model(payload.model)

    # সিস্টেম প্রম্পট ও ইউজার প্রম্পট আলাদা করা
    system_prompts: list[str] = []
    user_prompts: list[str] = []

    for msg in payload.messages:
        if msg.role == "system":
            system_prompts.append(msg.content)
        elif msg.role in ("user", "assistant"):
            user_prompts.append(f"{msg.role.upper()}: {msg.content}")

    system_text = "\n".join(system_prompts) if system_prompts else None
    prompt_text = "\n".join(user_prompts)

    if not prompt_text:
        raise HTTPException(status_code=400, detail="No prompt or user messages provided.")

    try:
        # বাংলা মন্তব্য: গ্লোবাল পুল দিয়ে ক্যাস্কেড এক্সিকিউশন
        response = await global_session_pool.complete_with_cascade(
            prompt=prompt_text,
            system_prompt=system_text,
            preferred_service=preferred_service,
            fallback_chain=fallback_chain,
            model=payload.model,
        )
        return response
    except WebAISessionError as exc:
        logger.error(f"[WebAIProxy] All cascade providers failed: {exc}")
        raise HTTPException(status_code=502, detail=f"Web AI Session Proxy failure: {exc}")
    except Exception as exc:
        logger.error(f"[WebAIProxy] Unexpected error in chat completion: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/models")
async def list_models():
    """বাংলা মন্তব্য: উপলব্ধ মডেলগুলোর তালিকা (OpenAI /v1/models সামঞ্জস্যপূর্ণ)।"""
    available_models = [
        {"id": "claude-3-7-sonnet-web", "object": "model", "owned_by": "supremeai-session-pool"},
        {"id": "gpt-4o-web", "object": "model", "owned_by": "supremeai-session-pool"},
        {"id": "v0-web", "object": "model", "owned_by": "supremeai-session-pool"},
        {"id": "auto-zero-cost", "object": "model", "owned_by": "supremeai-session-pool"},
    ]
    return {"object": "list", "data": available_models}


@router.get("/pool/status")
async def pool_status():
    """বাংলা মন্তব্য: মাল্টি-অ্যাকাউন্ট পুলের বর্তমান স্বাস্থ্য ও সক্রিয় অ্যাকাউন্ট সংখ্যা।"""
    return global_session_pool.get_pool_status()


@router.post("/pool/accounts")
async def register_pool_account(body: AccountRegisterRequest):
    """বাংলা মন্তব্য: পুলে ডায়নামিকালি নতুন অ্যাকাউন্ট/টোকেন ইনজেক্ট করা।"""
    acc = global_session_pool.register_account(
        service=body.service,
        token=body.token,
        account_id=body.account_id,
    )
    return {
        "status": "success",
        "service": acc.service,
        "account_id": acc.account_id,
        "is_active": acc.is_active,
    }


class ParallelTaskItem(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    prompt: str
    service: Literal["claude", "chatgpt", "v0", "auto"] = "auto"
    model: str | None = None
    system_prompt: str | None = None


class ParallelTasksRequest(BaseModel):
    tasks: list[ParallelTaskItem] = Field(..., min_length=1, max_length=20)
    concurrency_limit: int = Field(default=5, ge=1, le=20)


@router.post("/tasks/parallel")
async def parallel_chat_completions(payload: ParallelTasksRequest):
    """
    বাংলা সারসংক্ষেপ:
    ------------------
    একই সাথে একাধিক সেশনে ভিন্ন ভিন্ন AI-কে ভিন্ন ভিন্ন কাজের দায়িত্ব সমান্তরালে (Parallel) সম্পাদন।
    যেমন:
      - Task 1: Claude (Frontend Design)
      - Task 2: ChatGPT (Backend API & Database)
      - Task 3: v0 (React UI Components)
    """
    task_dicts = [t.model_dump() for t in payload.tasks]
    try:
        results = await global_session_pool.execute_parallel_tasks(
            tasks=task_dicts,
            concurrency_limit=payload.concurrency_limit,
        )
        return results
    except Exception as exc:
        logger.error(f"[WebAIProxy] Parallel execution error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


__all__ = ["router"]
