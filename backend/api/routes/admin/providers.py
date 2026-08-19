"""Admin → AI Providers & Model Router endpoints."""
from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from core.config import settings

router = APIRouter()


class RouterOverrideRequest(BaseModel):
    provider: str
    model: str
    remaining_requests: int


@router.get("/providers")
def get_providers():
    providers = []
    all_known = [
        (
            "openrouter",
            "OpenRouter",
            settings.openrouter_api_key,
            ["gpt-4o", "claude-3.5-sonnet", "llama-3.1-70b"],
        ),
        (
            "gemini",
            "Google Gemini",
            settings.gemini_api_key,
            ["gemini-2.0-flash", "gemini-2.5-pro"],
        ),
        ("groq", "Groq", settings.groq_api_key, ["llama-3.1-8b", "mixtral-8x7b"]),
        (
            "deepseek",
            "DeepSeek",
            settings.deepseek_api_key,
            ["deepseek-chat", "deepseek-reasoner"],
        ),
    ]
    for p_id, p_name, has_key, models in all_known:
        if has_key:
            providers.append(
                {
                    "id": p_id,
                    "name": p_name,
                    "status": "healthy",
                    "latency_ms": 120,
                    "latency_history": [115, 118, 120, 122, 119, 121, 120],
                    "api_key_valid": True,
                    "rate_limit_remaining": 90,
                    "rate_limit_max": 100,
                    "models": models,
                    "mode": "active",
                }
            )
    if not providers:
        providers.append(
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "status": "healthy",
                "latency_ms": 45,
                "latency_history": [40, 42, 45, 48, 44, 46, 45],
                "api_key_valid": True,
                "rate_limit_remaining": 100,
                "rate_limit_max": 100,
                "models": ["llama3", "mistral"],
                "mode": "active",
            }
        )
    return providers


@router.get("/model-router")
def get_model_router():
    return {
        "current_override": None,
        "override_remaining_requests": 0,
        "ab_test_active": False,
        "ab_test_split": 50,
        "provider_order": ["openrouter", "gemini", "groq", "deepseek"],
        "cost_quality_preference": 0.7,
    }


@router.post("/model-router/override")
def set_router_override(payload: RouterOverrideRequest):
    logger.info(f"Router override set: {payload.provider}/{payload.model} for {payload.remaining_requests} requests")
    return {
        "status": "success",
        "override": {
            "provider": payload.provider,
            "model": payload.model,
            "remaining": payload.remaining_requests,
        },
    }
