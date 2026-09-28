import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.dependencies import get_current_user_token
from brain.agent_departments import AgentDepartment
from brain.model_router import ModelRouter
from core.generation_monitor import GenerationMonitor
from core.logging_config import logger

agent_router = APIRouter(
    prefix="/api/v1/agents",
    tags=["agents"],
    dependencies=[Depends(get_current_user_token)],
)

# FIX (AUDIT-WIRE-1): রেজিস্ট্রির register_router() সবসময় module-এর 'router'
# attribute খোঁজে — এই ফাইল শুধু 'agent_router' এক্সপোর্ট করত বলে ALL_ROUTERS-এ
# যোগ করলেও এটি silently no-op হত। ক্যানোনিকাল alias যোগ করা হলো।
router = agent_router

model_router = ModelRouter()
agent_department = AgentDepartment(model_router)
monitor = GenerationMonitor()


def _correlation_id(request: Request) -> str:
    """Issue #685: the id assigned by SupremeContext/RequestContext middleware."""
    return getattr(request.state, "correlation_id", "") or ""


@agent_router.get("/roles")
async def list_agent_roles():
    return {"roles": agent_department.list_roles()}


@agent_router.get("/monitor/latency")
async def agent_latency_summary():
    summary = monitor.latency_summary()
    return JSONResponse(content=summary)
