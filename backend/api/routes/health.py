"""Health check endpoints for SupremeAI.

বাংলা: স্বাস্থ্য পরীক্ষা এন্ডপয়েন্ট।
render.yaml-এ healthCheckPath: /api/v1/health সেট করা আছে।
তাই GET /api/v1/health অবশ্যই 200 রিটার্ন করতে হবে।
"""
import time

from fastapi import APIRouter
from pydantic import BaseModel

from core.services import registry


router = APIRouter()


# বাংলা মন্তব্য: Render health check-এর জন্য এই endpoint অপরিহার্য।
# render.yaml-এ healthCheckPath: /api/v1/health নির্ধারিত।
# এটি prefix="/api/v1" সহ register করা হয়, তাই path="/health" যথেষ্ট।
@router.get("/health")
async def health_check():
    """Primary health check endpoint — used by Render, Kubernetes, and uptime monitors."""
    return {
        "status": "ok",
        "service": "supremeai-backend",
        "version": "2.0",
        "timestamp": int(time.time()),
    }


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
