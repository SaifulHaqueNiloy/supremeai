"""Admin-only intelligence insights and maintenance proposals."""

from fastapi import APIRouter, Depends

from api.dependencies import get_current_admin
from core.intelligence.precognitive_risk import precognitive_risk
from core.intelligence.synaptic_memory import synaptic_memory

a_router = APIRouter(
    prefix="/admin-api/intelligence",
    tags=["intelligence-insights"],
    dependencies=[Depends(get_current_admin)],
)


@a_router.get("/insights")
def insights() -> dict:
    return {
        "memory": synaptic_memory.insights(),
        "governance": {"proposal_only": True, "automatic_deletion": False},
        "risk": {"noise_budget": precognitive_risk.noise_budget},
    }


@a_router.post("/risk-proposals")
def risk_proposal(task: str, failure_rate: float = 0.0, irreversible: bool = False) -> dict:
    return precognitive_risk.propose(task, failure_rate=failure_rate, irreversible=irreversible).to_dict()


@a_router.post("/memory/consolidate")
async def consolidate_memory() -> dict:
    return synaptic_memory.consolidate().__dict__


router = a_router
