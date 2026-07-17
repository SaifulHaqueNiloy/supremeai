"""Health check endpoints for SupremeAI.

বাংলা: স্বাস্থ্য পরীক্ষা এন্ডপয়েন্ট।
render.yaml-এ healthCheckPath: /api/v1/health সেট করা আছে।
তাই GET /api/v1/health অবশ্যই 200 রিটার্ন করতে হবে।
"""
import time

from fastapi import APIRouter
from pydantic import BaseModel

from core.services import registry, redis_manager


router = APIRouter()


from fastapi import Request, Response

# বাংলা মন্তব্য: Render health check-এর জন্য এই endpoint অপরিহার্য।
# render.yaml-এ healthCheckPath: /api/v1/health নির্ধারিত।
# এটি prefix="/api/v1" সহ register করা হয়, তাই path="/health" যথেষ্ট।
@router.get("/health")
async def health_check(request: Request, response: Response):
    """Primary health check endpoint — checks actual database, redis and config health."""
    subsystems = getattr(request.app.state, "subsystem_status", {}).copy()

    # ── DB Health Check ──
    db_pool = getattr(request.app.state, "db_pool", None)
    if db_pool is not None:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            subsystems["db"] = "up"
        except Exception:  # noqa: BLE001
            subsystems["db"] = "down"
    elif subsystems.get("db") != "down":
        subsystems["db"] = "sqlite"

    # ── Redis Health Check ──
    if subsystems.get("redis") == "up":
        try:
            await redis_manager.client.ping()
        except Exception:  # noqa: BLE001
            subsystems["redis"] = "down"

    has_critical_failure = any(
        subsystems.get(k) == "down" for k in ["db", "redis"]
    )

    if has_critical_failure:
        response.status_code = 503
        return {
            "status": "degraded",
            "service": "supremeai-backend",
            "version": "2.0",
            "timestamp": int(time.time()),
            "subsystems": subsystems,
        }

    return {
        "status": "ok",
        "service": "supremeai-backend",
        "version": "2.0",
        "timestamp": int(time.time()),
        "subsystems": subsystems,
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
