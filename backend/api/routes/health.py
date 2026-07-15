"""Health check endpoints for SupremeAI.

বাংলা: স্বাস্থ্য পরীক্ষা এন্ডপয়েন্ট।
"""
from fastapi import APIRouter
from pydantic import BaseModel

from core.services import registry


router = APIRouter()


class HealthRequest(BaseModel):
    """Request model for agent health check."""
    agent_ids: list[str]


@router.post("/health/agents")
async def get_agents_health(request: HealthRequest):
    """Get health status for multiple agents."""
    # বাংলা: ServiceRegistry-এ get() মেথড ব্যবহার, get_service() নেই
    try:
        redis_mgr = await registry.get("redis_manager")
    except KeyError:
        return {"error": "Observability layer is offline."}

    # MGET কল করা হচ্ছে
    health_data = await redis_mgr.get_agents_health(request.agent_ids)
    return health_data
