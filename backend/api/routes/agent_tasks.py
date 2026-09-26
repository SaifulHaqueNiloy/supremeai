import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.dependencies import get_current_user_token
from brain.agent_departments import AgentDepartment
from brain.autonomous_agent import AutonomousAgent
from brain.langgraph_agent import SupremeOrchestrator
from brain.model_router import ModelRouter
from core.generation_monitor import GenerationMonitor
from core.logging_config import logger
from core.security.authentication.rbac import RoleBasedAccessControl
from core.zero_cost_architecture.swarm_orchestrator_integration import ZeroCostSwarmOrchestrator

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
orchestrator = SupremeOrchestrator()
autonomous_agent = AutonomousAgent()
agent_department = AgentDepartment(model_router)
rbac = RoleBasedAccessControl()
monitor = GenerationMonitor()


class AgentExecuteRequest(BaseModel):
    task: str
    task_type: str = "general"
    role: str | None = None
    department: str | None = None
    autonomous: bool = False
    user_context: dict[str, Any] | None = None


class SwarmExecuteRequest(BaseModel):
    task: str
    session_id: str | None = None
    user_id: str = "default_user"


class AgentExecuteResponse(BaseModel):
    success: bool
    output: str | None = None
    role: str | None = None
    provider: str | None = None
    cost: float | None = None
    errors: list | None = None


def _user_context(request: Request) -> dict[str, Any]:
    return {
        "ip": request.client.host if request.client else None,
        "source": request.headers.get("X-Source"),
    }


def _correlation_id(request: Request) -> str:
    """Issue #685: the id assigned by SupremeContext/RequestContext middleware."""
    return getattr(request.state, "correlation_id", "") or ""


@agent_router.post("/execute", response_model=AgentExecuteResponse)
async def execute_agent(request: Request, body: AgentExecuteRequest):
    correlation_id = _correlation_id(request)
    # Issue #685 (Domain 15): high-traffic router correlation logging.
    logger.info(
        "[agents.execute] task_type=%s department=%s autonomous=%s correlation_id=%s",
        body.task_type,
        body.department,
        body.autonomous,
        correlation_id,
    )
    _user_context(request)
    if body.autonomous:
        run = autonomous_agent.run(body.task, body.task_type)
        monitor.track_agent_call(prompt=body.task, provider="autonomous")
        return AgentExecuteResponse(
            success=run.get("run", {}).get("success", False),
            output=run.get("run", {}).get("output"),
            role="autonomous",
            cost=0.0,
            errors=run.get("run", {}).get("errors") or [],
        )

    if body.department:
        result = agent_department.execute(body.department, body.task, body.task_type)
        monitor.track_agent_call(prompt=body.task, provider=result.get("provider", "unknown"))
        return AgentExecuteResponse(
            success=result.get("success", False),
            output=result.get("output"),
            role=result.get("role"),
            provider=result.get("provider"),
            cost=result.get("cost"),
            errors=[result.get("error")] if result.get("error") else [],
        )

    result = orchestrator.execute_task(body.task, body.task_type)
    monitor.track_agent_call(prompt=body.task, provider=result.get("provider", "unknown"))
    return AgentExecuteResponse(
        success=result.get("success", False),
        output=result.get("result"),
        role="orchestrator",
        provider=result.get("provider"),
        cost=result.get("cost"),
        errors=[result.get("result")] if not result.get("success") else [],
    )


@agent_router.get("/roles")
async def list_agent_roles():
    return {"roles": agent_department.list_roles()}


@agent_router.get("/monitor/latency")
async def agent_latency_summary():
    summary = monitor.latency_summary()
    return JSONResponse(content=summary)


@agent_router.post("/swarm/execute")
async def execute_swarm(request: Request, body: SwarmExecuteRequest):
    """
    Executes the multi-agent swarm logic (Architecture -> Code -> QA)
    and returns the final workspace state.
    """
    session_id = body.session_id or str(uuid.uuid4())
    # Issue #685 (Domain 15): high-traffic router correlation logging.
    logger.info(
        "[agents.swarm_execute] session_id=%s correlation_id=%s",
        session_id,
        _correlation_id(request),
    )
    # AUDIT-FIX (P0): আগে ZeroCostSwarmOrchestrator-কে ভুল কনস্ট্রাক্টর আর্গুমেন্ট
    # (user_id/session_id/task_prompt) দিয়ে call করা হতো — কিন্তু আসল সিগনেচার শুধু
    # (config: ZeroCostConfig | None = None)। এছাড়া .execute(max_retries=2) মেথড
    # নেই; সঠিক মেথড .execute_task(prompt, user_id, priority, timeout)।
    # workspace.generated_code/architecture_design-ও SharedWorkspace-এ নেই —
    # সঠিক ফিল্ড: work_product (dict) ও execution_logs (list)।
    swarm_orchestrator = ZeroCostSwarmOrchestrator()
    execution_result = await swarm_orchestrator.execute_task(
        prompt=body.task,
        user_id=body.user_id or f"session:{session_id}",
    )
    workspace = execution_result.workspace

    return {
        "status": execution_result.status,  # "success" | "degraded" | "error"
        "session_id": session_id,
        "task_id": execution_result.task_id,
        "results": {
            "passed_qa": workspace.test_results.get("passed", False),
            "feedback": workspace.test_results.get("feedback", ""),
            "work_product": workspace.work_product,
            "execution_logs": workspace.execution_logs,
            "errors": [*workspace.errors, *(execution_result.errors or [])],
        },
        # বোনাস: প্রতি রেসপন্ন্সে orchestrator-এর স্বাস্থ্য ও metrics দেখাচ্ছে —
        # ক্লায়েন্ট বুঝতে পারবে circuit breaker ট্রিপ করেছে কিনা।
        "orchestrator_status": swarm_orchestrator.get_status(),
    }
