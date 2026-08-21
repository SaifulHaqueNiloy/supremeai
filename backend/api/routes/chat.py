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

    # Cache miss - generate response from AI model with memory context
    logger.info("❌ CACHE MISS: Generating new response from AI model with memory recall")
    try:
        # Retrieve long-term memory facts for tenant/user context
        memory_ctx = ""
        try:
            from memory.long_term_memory import LongTermMemory
            ltm = LongTermMemory(session_id=session_id or "default")
            mem_facts = ltm.build_context()
            if mem_facts and mem_facts != "No memory available.":
                memory_ctx = f"[Relevant Memory Context:\n{mem_facts}]\n\n"
        except Exception as mem_err:
            logger.debug(f"Memory retrieval bypassed: {mem_err}")

        enriched_prompt = f"{memory_ctx}{payload.prompt}" if memory_ctx else payload.prompt
        # বাংলা মন্তব্য: সরাসরি গুগল নেটিভ ক্লায়েন্ট কল না করে ইউনিভার্সাল llm_gateway ব্যবহার করে এপিআই কল করা হচ্ছে
        response = await llm_gateway.acompletion(prompt=enriched_prompt, task_type="chat", stream=False)
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
async def stream_chat(payload: ChatPayload, db=Depends(get_tenant_db)):
    """High-Concurrency Async SSE Streamer.

    বাংলা: SSE-এর জন্য ক্রিটিক্যাল হেডার যোগ করা হলো (Cache-Control: no-cache,
    X-Accel-Buffering: no) যাতে nginx/CDN/proxy স্ট্রিম বাফার না করে। ক্লায়েন্ট
    ডিসকানেক্ট হলে generator বন্ধ হবে।
    """
    logger.info(f"🌊 SSE Stream Initiated for tenant: {db.tenant_id}")

    async def async_generator():
        try:
            # বাংলা: ইউনিভার্সাল llm_gateway ব্যবহার করে স্ট্রিমিং সম্পন্ন করা হচ্ছে
            response_stream = await llm_gateway.acompletion(prompt=payload.prompt, task_type="chat", stream=True)

            async for chunk in response_stream:
                if chunk:
                    # SSE (Server-Sent Events) স্ট্যান্ডার্ড ফরম্যাট
                    yield f"data: {chunk}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream broken: {e!s}")
            yield f"data: [ERROR] {e!s}\n\n"

    # বাংলা: SSE হেডার — proxy/CDN বাফারিং রোধে ক্রিটিক্যাল।
    return StreamingResponse(
        async_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # nginx বাফারিং রোধে
            "Content-Encoding": "identity",  # কম্প্রেশন বন্ধ — SSE-এর জন্য প্রয়োজন
        },
    )
