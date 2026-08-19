"""LLM Gateway admin endpoints (Super-Admin Studio dashboard).

বাংলা মন্তব্য: ফ্রন্টএন্ডের LlmGatewayPage সরাসরি /api/admin/llm/* কল করে, কিন্তু ব্যাকএন্ডে
এই পাথগুলোর কোনো এন্ডপয়েন্ট ছিল না (শুধু /llm-gateway/* ছিল) — ফলে পেজ সবসময় 404 পেত।
এই মডিউলটি গেটওয়ের বাস্তব স্টেট (fallback chain, circuit breaker, routing policy) থেকে
প্রভাইডার/রাউটার ডেটা বিল্ড করে এবং ওভাররাইড + রুল ইন-মেমরি স্টোর করে (admin restart-এ reset)।
"""

from fastapi import APIRouter, Depends

from api.dependencies import get_current_user_token
from core.llm.llm_gateway import get_llm_gateway
from core.resilience.circuit_breaker_manager import get_circuit_breaker_manager

router = APIRouter(prefix="/api/admin/llm", tags=["llm-gateway-admin"])

# বাংলা মন্তব্য: ওভাররাইড ও রুল ইন-মেমরি — single-tenant admin tool-এর জন্য যথেষ্ট।
# পারসিস্টেন্স দরকার হলে ভবিষ্যতে ai_memory-এ সেভ করা যাবে।
_active_override: dict | None = None
_system_rules: dict = {}


def _parse_provider_model(entry: str) -> tuple[str, str]:
    if "/" in entry:
        provider, model = entry.split("/", 1)
        return provider, model
    return "default", entry


@router.get("/providers")
async def list_providers(current_user: dict = Depends(get_current_user_token)):
    """Build Provider[] from the gateway fallback chain."""
    gateway = get_llm_gateway()
    routing_policy = getattr(gateway, "routing_policy", {}) or {}
    fallback_chain: list[str] = routing_policy.get("fallback_chain", [])

    cb_manager = get_circuit_breaker_manager()
    cb_states = cb_manager.get_all_states() if cb_manager else {}

    providers: list[dict] = []
    seen: set[str] = set()
    for entry in fallback_chain:
        provider, model = _parse_provider_model(entry)
        if provider in seen:
            # Append model to existing provider
            for p in providers:
                if p["id"] == provider:
                    if model not in p["models"]:
                        p["models"].append(model)
                    break
            continue
        seen.add(provider)
        # Derive a rough health/latency signal from circuit breaker states
        status = "healthy"
        latency_ms = 0
        for cb_name, cb_state in (cb_states or {}).items():
            if isinstance(cb_state, dict) and provider in str(cb_name):
                state_val = cb_state.get("state", "closed")
                if state_val != "closed":
                    status = "degraded"
        providers.append(
            {
                "id": provider,
                "name": provider,
                "status": status,
                "latency_ms": latency_ms,
                "models": [model] if model else [],
                "mode": "fallback",
            }
        )

    return providers


@router.get("/router")
async def get_router(current_user: dict = Depends(get_current_user_token)):
    """Build ModelRouter from the routing policy + active override."""
    gateway = get_llm_gateway()
    routing_policy = getattr(gateway, "routing_policy", {}) or {}
    fallback_chain: list[str] = routing_policy.get("fallback_chain", [])

    provider_order: list[str] = []
    for entry in fallback_chain:
        provider, _ = _parse_provider_model(entry)
        if provider not in provider_order:
            provider_order.append(provider)

    return {
        "current_override": _active_override,
        "provider_order": provider_order,
        "cost_quality_preference": routing_policy.get("cost_quality_preference", 0.5),
    }


@router.post("/router/override")
async def set_router_override(payload: dict, current_user: dict = Depends(get_current_user_token)):
    """Set a live routing override (in-memory)."""
    global _active_override
    _active_override = {
        "provider": payload.get("provider"),
        "model": payload.get("model"),
        "remaining_requests": payload.get("remaining_requests", 100),
    }
    return {"status": "ok", "override": _active_override}


@router.get("/rules")
async def get_rules(current_user: dict = Depends(get_current_user_token)):
    """Return current system rules."""
    return _system_rules


@router.post("/rules")
async def save_rules(payload: dict, current_user: dict = Depends(get_current_user_token)):
    """Persist system rules (in-memory)."""
    global _system_rules
    rules = payload.get("rules", payload) if isinstance(payload, dict) else {}
    _system_rules = rules if isinstance(rules, dict) else {}
    return {"status": "ok", "rules": _system_rules}


__all__ = ["router"]
