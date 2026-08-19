from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from api.dependencies import get_tenant_db
from core.cache.multi_layer_cache import multi_layer_cache
from core.llm.llm_gateway import llm_gateway

router = APIRouter(prefix="/api/chat", tags=["AI-Orchestration"])


class ChatPayload(BaseModel):
    prompt: str
    model_name: str = "gemini-2.5-pro"


# ⚡ ১. Fully Async Standard Completion with Multi-Layer Caching
@router.post("/get_completion")
async def get_completion(request: Request, payload: ChatPayload, db=Depends(get_tenant_db)):
    """Non-blocking Async LLM Completion with 5-Layer Caching"""
    logger.info(f"⚡ Async API Hit: Generating completion for tenant: {db.tenant_id}")

    # Extract session ID from headers for session-based caching
    session_id = request.headers.get("X-Session-ID")

    # Check multi-layer cache first
    cached_result = await multi_layer_cache.get(
        prompt=payload.prompt, model_name=payload.model_name, session_id=session_id
    )

    if cached_result:
        logger.info(f"🚀 CACHE HIT: {cached_result['source']}")
        return {
            "success": True,
            "response": cached_result["response"],
            "cached": True,
            "cache_source": cached_result["source"],
            "latency_ms": cached_result.get("latency_ms", 0),
        }

    # Cache miss - generate response from AI model
    logger.info("❌ CACHE MISS: Generating new response from AI model")
    try:
        # বাংলা মন্তব্য: সরাসরি গুগল নেটিভ ক্লায়েন্ট কল না করে ইউনিভার্সাল llm_gateway ব্যবহার করে এপিআই কল করা হচ্ছে
        response = await llm_gateway.acompletion(prompt=payload.prompt, task_type="chat", stream=False)
        response_text = response.get("text", "") if isinstance(response, dict) else str(response)

        # Store response in multi-layer cache for future requests
        await multi_layer_cache.set(
            prompt=payload.prompt,
            response=response_text,
            model_name=payload.model_name,
            session_id=session_id,
        )

        return {
            "success": True,
            "response": response_text,
            "cached": False,
            "cache_source": "L5_AI_MODEL",
        }
    except Exception as e:
        logger.error(f"Async LLM Error: {e!s}")
        raise HTTPException(status_code=500, detail="AI Gateway Timeout.") from e


# ⚡ ২. Fully Async Streaming Generator
@router.post("/stream_chat")
@router.post("/stream")
async def stream_chat(payload: ChatPayload, db=Depends(get_tenant_db)):
    """High-Concurrency Async SSE Streamer.

    বাংলা মন্তব্য: ক্লায়েন্টরা /api/chat/stream_chat এবং /api/chat/stream — দুটিই কল করে,
    তাই উভয় পাথেই স্ট্রিমিং সাপোর্ট করা হলো (alias)।
    """
    logger.info(f"🌊 SSE Stream Initiated for tenant: {db.tenant_id}")

    async def async_generator():
        try:
            # বাংলা মন্তব্য: ইউনিভার্সাল llm_gateway ব্যবহার করে স্ট্রিমিং সম্পন্ন করা হচ্ছে
            response_stream = await llm_gateway.acompletion(prompt=payload.prompt, task_type="chat", stream=True)

            async for chunk in response_stream:
                if chunk:
                    # SSE (Server-Sent Events) স্ট্যান্ডার্ড ফরম্যাট
                    yield f"data: {chunk}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream broken: {e!s}")
            yield f"data: [ERROR] {e!s}\n\n"

    # ইভেন্ট লুপ ব্লক না করে স্ট্রিমিং রেসপন্স থ্রো করা
    return StreamingResponse(async_generator(), media_type="text/event-stream")


# ⚡ ২.৫. Non-streaming message endpoint (used by VS Code extension primary path)
@router.post("/message")
async def chat_message(payload: ChatPayload, db=Depends(get_tenant_db)):
    """Single-shot chat completion (mirrors /get_completion response shape)."""
    try:
        response = await llm_gateway.acompletion(prompt=payload.prompt, task_type="chat", stream=False)
        response_text = response.get("text", "") if isinstance(response, dict) else str(response)
        return {"success": True, "response": response_text, "cached": False}
    except Exception as e:
        logger.error(f"Chat message error: {e!s}")
        raise HTTPException(status_code=500, detail="AI Gateway Timeout.") from e

# ⚡ ৩. Session Intelligence: Get Session DNA
@router.get("/session-dna")
async def get_session_dna(request: Request, db=Depends(get_tenant_db)):
    """Fetch summarized context of the last active session to provide Continuous Thread experience."""
    session_id = request.headers.get("X-Session-ID") or "default_session"
    tenant_id = db.tenant_id
    logger.info(f"🧬 Fetching Session DNA for session: {session_id}, tenant: {tenant_id}")
    
    try:
        # In a full implementation, we'd fetch the latest conversation thread from memory
        # Here we mock it for the frontend to build the UI
        dna = {
            "session_id": session_id,
            "last_active": "2 hours ago",
            "summary": "Discussed system architecture, Redis caching layer, and optimized the backend routing logic. You asked about improving test coverage for the cost guard module.",
            "topics": ["Architecture", "Redis", "Testing"],
            "memories_count": 4,
            "context_nodes": ["cost_guard", "cache_layer"]
        }
        
        return {"success": True, "dna": dna}
    except Exception as e:
        logger.error(f"Error fetching session DNA: {e}")
        return {"success": False, "dna": None, "error": str(e)}
