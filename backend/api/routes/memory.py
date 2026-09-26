from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.dependencies import get_current_user_token, get_tenant_db
from memory.checkpoint_resume import CheckpointResume
from memory.sliding_window import SlidingWindowConfig, SlidingWindowMemory

router = APIRouter(
    prefix="/api/memory",
    tags=["memory"],
    dependencies=[Depends(get_current_user_token)],
)


# Model for message persistence
class MessageCreate(BaseModel):
    conversation_id: str | None = None
    message: dict


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


_checkpoint: CheckpointResume | None = None
_window: SlidingWindowMemory | None = None


def _checkpoint_prefix(user: dict) -> str:
    """Owner prefix for checkpoint keys (AUD-5.1 tenant binding)."""
    sub = user.get("sub") or "anonymous"
    safe = str(sub).replace(":", "_").replace("/", "_")
    return f"u:{safe}:"


def _owned_checkpoint_key(user: dict, task_id: str) -> str:
    return f"{_checkpoint_prefix(user)}{task_id}"


def get_checkpoint() -> CheckpointResume:
    global _checkpoint
    if _checkpoint is None:
        _checkpoint = CheckpointResume()
    return _checkpoint


def get_window() -> SlidingWindowMemory:
    global _window
    if _window is None:
        _window = SlidingWindowMemory()
    return _window


class CheckpointSaveRequest(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    step_index: int = Field(..., ge=0)
    state: dict[str, Any] = Field(default_factory=dict)


class CheckpointResponse(BaseModel):
    task_id: str
    step_index: int
    state: dict[str, Any]
    resumed: bool


class ChunkRequest(BaseModel):
    text: str
    session_id: str = "default"
    max_tokens: int = 4000
    overlap_ratio: float = 0.15


class ChunkResponse(BaseModel):
    session_id: str
    windows: list[dict[str, Any]]


class ContextRequest(BaseModel):
    documents: list[str] = Field(default_factory=list)
    query: str = ""
    session_id: str = "default"
    budget: int | None = None


class ContextResponse(BaseModel):
    session_id: str
    context: str


@router.post("/checkpoint", response_model=CheckpointResponse)
def save_checkpoint(payload: CheckpointSaveRequest, user: dict = Depends(get_current_user_token)):
    store = get_checkpoint()
    # AUD-5.1 (IDOR fix): checkpoints were globally keyed by task_id with no owner
    # binding — any authenticated user could read/clear another user's checkpoint.
    # Namespace the stored key by the authenticated user.
    owned_key = _owned_checkpoint_key(user, payload.task_id)
    ok = store.save(owned_key, payload.step_index, payload.state)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to save checkpoint")
    return CheckpointResponse(
        task_id=payload.task_id,
        step_index=payload.step_index,
        state=payload.state,
        resumed=False,
    )


@router.get("/checkpoint/{task_id}", response_model=CheckpointResponse | None)
def load_checkpoint(task_id: str, user: dict = Depends(get_current_user_token)):
    store = get_checkpoint()
    result = store.load(_owned_checkpoint_key(user, task_id))
    if result is None:
        return None
    result = dict(result)
    result["task_id"] = task_id
    return CheckpointResponse(**result)


@router.get("/checkpoints", response_model=list[dict[str, Any]])
def list_checkpoints(user: dict = Depends(get_current_user_token)):
    store = get_checkpoint()
    prefix = _checkpoint_prefix(user)
    scoped = []
    for cp in store.list_all():
        cp_id = str(cp.get("task_id", ""))
        if cp_id.startswith(prefix):
            scoped.append({**cp, "task_id": cp_id[len(prefix) :]})
    return scoped


@router.delete("/checkpoint/{task_id}")
def clear_checkpoint(task_id: str, user: dict = Depends(get_current_user_token)):
    store = get_checkpoint()
    ok = store.clear(_owned_checkpoint_key(user, task_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return {"status": "ok", "task_id": task_id}


@router.post("/chunk", response_model=ChunkResponse)
def chunk_text(payload: ChunkRequest):
    config = SlidingWindowConfig(max_tokens=payload.max_tokens, overlap_ratio=payload.overlap_ratio)
    memory = SlidingWindowMemory(config=config)
    windows = memory.chunk(payload.text, session_id=payload.session_id)
    return ChunkResponse(session_id=payload.session_id, windows=windows)


@router.post("/context", response_model=ContextResponse)
def build_context(payload: ContextRequest):
    config = SlidingWindowConfig()
    memory = SlidingWindowMemory(config=config)
    budget = payload.budget or config.max_tokens
    context = memory.build_context(payload.documents, payload.query, payload.session_id, budget)
    return ContextResponse(session_id=payload.session_id, context=context)


@router.get("/recall", response_model=list[dict[str, Any]])
def recall_memory(session_id: str = "default", limit: int = 20):
    memory = get_window()
    return memory.recall(session_id, limit=limit)


@router.delete("/recall")
def clear_memory(session_id: str = "default"):
    memory = get_window()
    ok = memory.clear(session_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to clear memory")
    return {"status": "ok", "session_id": session_id}


# ---------------------------------------------------------------------------
# Vector Memory (Eternal Brain) API Schemas & Endpoints
# ---------------------------------------------------------------------------


class VectorRecallRequest(BaseModel):
    task_description: str = Field(
        ..., min_length=1, description="Task or prompt to recall context for"
    )
    limit: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class VectorSaveRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    task_type: str = Field(default="general")
    agent_type: str = Field(default="main")
    metadata: dict[str, Any] | None = None


class SessionSaveRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    messages: list[dict[str, Any]] = Field(..., min_length=1)
    task_type: str = Field(default="general")


@router.post("/recall")
async def vector_recall(req: VectorRecallRequest, user: dict = Depends(get_current_user_token)):
    """Semantic-search the Eternal Brain for relevant past memories (owner-scoped)."""
    from services.memory_service import recall_memories

    memories = await recall_memories(
        task_description=req.task_description,
        limit=req.limit,
        threshold=req.threshold,
        user_id=user.get("sub"),  # AUD-5.1: no cross-tenant recall
    )
    return {"success": True, "memories": memories, "count": len(memories)}


@router.post("/save")
async def vector_save(req: VectorSaveRequest, user: dict = Depends(get_current_user_token)):
    """Store a vector memory entry into Supabase/pgvector or cascade fallback."""
    from services.memory_service import save_memory

    result = await save_memory(
        session_id=req.session_id,
        summary=req.summary,
        task_type=req.task_type,
        agent_type=req.agent_type,
        metadata=req.metadata,
        user_id=user.get("sub"),  # AUD-5.1: bind memory to owner
    )
    return result


@router.post("/session")
async def save_session(req: SessionSaveRequest, user: dict = Depends(get_current_user_token)):
    """Summarize a full chat session via LLM, then save as vector memory."""
    from services.memory_service import summarize_and_save_session

    result = await summarize_and_save_session(
        session_id=req.session_id,
        messages=req.messages,
        task_type=req.task_type,
        user_id=user.get("sub"),
    )
    return result


@router.post("/conversations/messages")
async def save_message(req: MessageCreate, db=Depends(get_tenant_db)):
    """
    Save a chat message to conversation history.
    Creates conversation if doesn't exist.
    """
    from core.config import settings
    from core.logging_config import logger

    conversation_id = req.conversation_id or f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    try:
        # Issue #1472 fix: this endpoint previously called Mongo-style APIs
        # (db.conversations.find_one/insert_one/update_one) on the
        # TenantAwareFirestore dependency — AttributeError -> 500 on every
        # call. Rewrite with the Firestore document API the dependency
        # actually provides; the sync google-cloud-firestore calls run in a
        # worker thread so the event loop is never blocked.
        col = db.conversations  # tenant-scoped: tenants/<uid>/conversations
        doc_ref = col.document(conversation_id)
        snap = await asyncio.to_thread(doc_ref.get)
        existing = snap.to_dict() if getattr(snap, "exists", False) else None

        now = datetime.utcnow()
        message_doc = {**req.message, "saved_at": now}

        if existing:
            messages = list(existing.get("messages") or [])
            messages.append(message_doc)
            doc = {
                "_id": conversation_id,
                "title": existing.get("title") or "chat conversation",
                "created_at": existing.get("created_at") or now,
                "updated_at": now,
                "messages": messages,
                "tags": list(existing.get("tags") or []),
            }
        else:
            doc = {
                "_id": conversation_id,
                "title": req.message.get("metadata", {}).get("source", "chat") + " conversation",
                "created_at": now,
                "updated_at": now,
                "messages": [message_doc],
                "tags": [],
            }

        await asyncio.to_thread(doc_ref.set, doc)

        # If RAG is enabled, also index for retrieval
        if (
            hasattr(settings, "RAG_ENABLED")
            and settings.RAG_ENABLED
            and req.message.get("role") == "user"
        ):
            try:
                from services.memory_service import save_memory

                await save_memory(
                    session_id=conversation_id,
                    summary=req.message["content"],
                    task_type="chat",
                    metadata={"timestamp": req.message.get("timestamp", time.time())},
                )
            except Exception as e:
                logger.warning(f"RAG indexing failed for message: {e}")

        return {
            "success": True,
            "conversation_id": conversation_id,
            "message_id": req.message.get("id"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/conversations")
async def list_conversations(request: Request, db=Depends(get_tenant_db)):
    """Get all conversations for authenticated user."""
    from core.logging_config import logger

    try:
        # Issue #1472 fix: Mongo-style find().sort().to_list() on the
        # Firestore-backed dependency always 500'd. Use the Firestore query
        # API (tenant-scoped), offloaded to a worker thread.
        snaps = await asyncio.to_thread(
            lambda: list(
                db.conversations.order_by("updated_at", direction="DESCENDING").limit(50).stream()
            )
        )

        # Format for frontend
        result = []
        for snap in snaps:
            conv = snap.to_dict() or {}
            conv_id = conv.get("_id") or snap.id
            messages = conv.get("messages") or []
            result.append(
                {
                    "id": conv_id,
                    "title": conv.get("title", "Untitled"),
                    "messages": messages[-10:],  # Last 10 messages
                    "createdAt": conv.get("created_at"),
                    "updatedAt": conv.get("updated_at"),
                    "messageCount": len(messages),
                    "tags": conv.get("tags", []),
                }
            )

        return result

    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
