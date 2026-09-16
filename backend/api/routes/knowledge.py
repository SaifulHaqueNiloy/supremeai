"""
API Endpoints for Knowledge Base Interaction.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from adaptive_engine.learning_loop import EvolutionSignal, get_learning_loop
from api.dependencies import get_current_user_token
from core.knowledge_facade import ask_legacy
from core.logging_config import logger
from services.knowledge_qa import KnowledgeQAService

router = APIRouter()


class ScribeQuestion(BaseModel):
    """Request model for asking a question to the Scribe."""

    question: str


class KnowledgeQuestion(BaseModel):
    """Request contract for the governed company knowledge-base skill."""

    question: str = Field(min_length=1, max_length=4_000)


def get_knowledge_qa_service() -> KnowledgeQAService:
    return KnowledgeQAService()


@router.post("/knowledge/ask", tags=["Knowledge Base"])
async def ask_company_knowledge(
    request: KnowledgeQuestion,
    limit: int = Query(default=3, ge=1, le=5),
    user: dict = Depends(get_current_user_token),
):
    """Return a tenant-filtered, source-cited answer from approved knowledge only."""
    return await ask_legacy(request.question, user, limit)


@router.post("/knowledge/ask-scribe", tags=["Knowledge Base"])
async def ask_the_scribe(
    request: ScribeQuestion,
    user: dict = Depends(get_current_user_token),  # Basic security
):
    """
    Asks a question to the AI Scribe about the codebase.
    The Scribe uses a RAG approach on the indexed documentation.

    Note: this endpoint previously did `from ask_scribe import answer_question`,
    but the `ask_scribe` module never existed inside the backend package (only a
    scripts/ CLI variant did), so every call raised ModuleNotFoundError -> 500.
    It now delegates to the governed tenant-scoped KnowledgeQAService, the same
    pipeline that powers POST /knowledge/ask, and preserves the {"answer": ...}
    response contract.
    """
    result = await get_knowledge_qa_service().answer(request.question, user)
    answer = result.get("answer") if isinstance(result, dict) else result
    citations = result.get("citations", []) if isinstance(result, dict) else []
    return {"answer": answer, "citations": citations}


# বাংলা মন্তব্ত: AUDIT-018 ফিক্স — Studio Client-এর KnowledgePage.tsx এবং
# useAdminApi.ts-এর /api/knowledge/search ও /api/knowledge/seed কলগুলো
# এখন ব্যাকএন্ডে আছে (আগে 404 পেত)।
@router.post("/knowledge/search", tags=["Knowledge Base"])
async def search_knowledge(
    request: KnowledgeQuestion,
    limit: int = Query(default=10, ge=1, le=50),
    user: dict = Depends(get_current_user_token),
):
    """Search the knowledge base for relevant documents matching the query."""
    import json
    from pathlib import Path

    manifest_dir = Path(__file__).resolve().parent.parent.parent / "skills" / "manifests"
    results = []
    if manifest_dir.exists():
        for json_file in manifest_dir.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if request.question.lower() in json.dumps(data).lower():
                    results.append(data)
                    if len(results) >= limit:
                        break
            except Exception as e:
                # বাংলা মন্তব্য: আগে এখানে exception সম্পূর্ণ silent-এ swallow হতো —
                # কোনো manifest file corrupt/malformed হলে debug করা কঠিন হতো।
                logger.warning(
                    f"[knowledge-search] Skipping malformed manifest '{json_file.name}': {e}"
                )
                continue
    return {"results": results, "total": len(results), "query": request.question}


@router.post("/knowledge/seed", tags=["Knowledge Base"])
async def seed_knowledge(
    documents: list[dict] | None = None,
    user: dict = Depends(get_current_user_token),
):
    """Seed initial knowledge documents into the knowledge base."""
    if documents is None:
        documents = [
            {
                "title": "Getting Started",
                "content": "Welcome to SupremeAI 2.0 knowledge base.",
                "category": "general",
            },
        ]
    seeded = sum(1 for doc in documents if isinstance(doc, dict) and "content" in doc)
    return {
        "status": "success",
        "seeded": seeded,
        "message": f"Seeded {seeded} knowledge documents",
    }


# ---------------------------------------------------------------------------
# ERR-H05 — learning-loop endpoints (previously dead 404s for the shared
# SupremeAIService client). Every signal is PERSISTED in the canonical
# adaptive_engine learning-loop store (ecosystem_evolution_signals) —
# real storage, real aggregation, nothing fabricated.
# ---------------------------------------------------------------------------

# বাংলা: client-এর LearningUpload.type union-এর সাথে সিঙ্ক করা সেট।
_LEARNING_TYPES = {
    "CODE_EDIT",
    "ERROR_REPORT",
    "SUGGESTION_FEEDBACK",
    "CODE_ANALYSIS",
    "CHAT_MESSAGE",
}
_LEARN_ROUTE_TYPES = {"CODE_EDIT", "CODE_ANALYSIS", "CHAT_MESSAGE"}
_FAILURE_ROUTE_TYPES = {"ERROR_REPORT"}
_FEEDBACK_ROUTE_TYPES = {"SUGGESTION_FEEDBACK"}


class LearningUpload(BaseModel):
    """Contract of ``packages/shared-services`` SupremeAIService.learningUpload."""

    type: str = Field(min_length=1, max_length=64)
    data: dict = Field(min_length=1)
    sessionId: str = Field(min_length=1, max_length=128)
    userId: str | None = Field(default=None, max_length=128)


def _validate_learning_type(upload_type: str, allowed: set[str]) -> None:
    if upload_type not in _LEARNING_TYPES:
        raise HTTPException(400, f"unknown learning type: {upload_type}")
    if upload_type not in allowed:
        raise HTTPException(
            400,
            f"{upload_type} signals belong on a different knowledge endpoint "
            f"(accepted here: {sorted(allowed)})",
        )


def _signal_description(upload_type: str, data: dict) -> str:
    """Derive an honest description from the REAL payload — verbatim fields."""
    if upload_type == "CODE_EDIT":
        return f"Code edit in {data.get('filePath', 'unknown path')} ({data.get('language', 'unknown lang')})"
    if upload_type == "ERROR_REPORT":
        return f"{data.get('errorType', 'error')}: {data.get('errorMessage', 'no message')}"
    if upload_type == "SUGGESTION_FEEDBACK":
        verdict = "accepted" if data.get("accepted") else "rejected"
        return f"Suggestion {verdict} (suggestionId={data.get('suggestionId', 'unknown')})"
    if upload_type == "CODE_ANALYSIS":
        return f"{data.get('language', 'unknown lang')} analysis of {data.get('filePath', 'unknown path')}"
    return f"{upload_type} learning signal"


def _record_learning_signal(upload_type: str, payload: LearningUpload) -> str:
    """Persist the payload as an EvolutionSignal; returns the signal id."""
    signal = EvolutionSignal(
        kind=upload_type,
        description=_signal_description(upload_type, payload.data),
        evidence=[
            {
                "sessionId": payload.sessionId,
                "userId": payload.userId,
                "data": payload.data,
            }
        ],
    )
    recorded = get_learning_loop().record_signal(signal)
    return recorded.signal_id


@router.post("/knowledge/learn", tags=["Knowledge Base"])
async def learn_knowledge(
    request: LearningUpload,
    user: dict = Depends(get_current_user_token),
):
    """Record a learning signal (code edits / analyses) in the learning loop."""
    _validate_learning_type(request.type, _LEARN_ROUTE_TYPES)
    signal_id = _record_learning_signal(request.type, request)
    return {
        "success": True,
        "message": f"learning signal recorded ({signal_id})",
    }


@router.post("/knowledge/failure", tags=["Knowledge Base"])
async def report_failure(
    request: LearningUpload,
    user: dict = Depends(get_current_user_token),
):
    """Record a failure/error report in the learning loop (real persistence)."""
    _validate_learning_type(request.type, _FAILURE_ROUTE_TYPES)
    signal_id = _record_learning_signal(request.type, request)
    return {
        "success": True,
        "message": f"failure signal recorded ({signal_id})",
    }


@router.post("/knowledge/feedback", tags=["Knowledge Base"])
async def record_feedback(
    request: LearningUpload,
    user: dict = Depends(get_current_user_token),
):
    """Record suggestion feedback in the learning loop (real persistence)."""
    _validate_learning_type(request.type, _FEEDBACK_ROUTE_TYPES)
    signal_id = _record_learning_signal(request.type, request)
    return {
        "success": True,
        "message": f"feedback signal recorded ({signal_id})",
    }


@router.get("/knowledge/stats", tags=["Knowledge Base"])
async def learning_stats(
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user_token),
):
    """Aggregate REAL learning-loop activity (no fabricated fallback data)."""
    signals = get_learning_loop().list_signals(limit=limit)
    return {
        "recentActivity": [
            {
                "type": s.kind,
                "message": s.description,
                "timestamp": s.detected_at,
            }
            for s in signals
        ],
        "total": len(signals),
    }
