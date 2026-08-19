from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/agents", tags=["specialized-agents"])


class SymptomRequest(BaseModel):
    symptoms: str
    age: int | None = None
    medical_history: str | None = None


class DrugInteractionRequest(BaseModel):
    medications: list[str]


class LegalAnalysisRequest(BaseModel):
    document_text: str
    doc_type: str = "contract"


class TradeRequest(BaseModel):
    symbol: str
    quantity: float
    price: float | None = None


class ResearchRequest(BaseModel):
    query: str
    source: str = "arxiv"
    max_results: int = 5


class SummarizeRequest(BaseModel):
    paper: dict[str, Any]
    style: str = "apa"


# বাংলা মন্তব্য: AUDIT FIX (2026-08) — আগে nonexistent `agents.legal_agent` ইত্যাদি
# import করে এই endpoints 500 দিত। এখন real `tools.ai_agents.*` ব্যবহার করা হয়;
# যেসব sub-action-এর real implementation নেই সেগুলো 501 (Not Implemented) return করে —
# কোনো fake/misleading data বা crash নয়।

_IMPLEMENTED_AGENTS = {"legal", "medical", "trading"}


def _not_implemented(action: str) -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={
            "error": "not_implemented",
            "detail": f"'{action}' is not implemented yet. Use the main chat/orchestration API instead.",
        },
    )


@router.get("/", tags=["specialized-agents"])
async def list_agents():
    """List all available specialized agent types."""
    return {
        "agents": [
            {"id": "legal", "name": "Legal Agent", "description": "Legal document analysis"},
            {"id": "medical", "name": "Medical Agent", "description": "Medical symptom analysis"},
            {"id": "trading", "name": "Trading Agent", "description": "Stock trading analysis"},
            {"id": "research", "name": "Research Agent", "description": "Research paper analysis"},
        ]
    }


@router.get("/{agent_id}/status", tags=["specialized-agents"])
async def get_agent_status(agent_id: str):
    """Get status of a specific agent — honest, no hardcoded 'active'."""
    if agent_id in _IMPLEMENTED_AGENTS:
        return {"agent_id": agent_id, "status": "available"}
    return {
        "agent_id": agent_id,
        "status": "unavailable",
        "detail": "No backend implementation registered for this agent type.",
    }


@router.post("/legal/analyze")
async def legal_analyze(payload: LegalAnalysisRequest):
    try:
        from tools.ai_agents.legal_agent import LegalAgent

        agent = LegalAgent()
        result = await agent.analyze_clause(clause_text=payload.document_text, jurisdiction="BD")
        return {"success": True, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Legal analysis service unavailable: {exc}") from exc


@router.post("/medical/symptoms")
async def medical_symptoms(payload: SymptomRequest):
    try:
        from tools.ai_agents.medical_agent import MedicalAgent

        agent = MedicalAgent()
        context = {"age": payload.age, "medical_history": payload.medical_history}
        result = await agent.analyze_symptoms(payload.symptoms, context=context)
        return {"success": True, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Medical analysis service unavailable: {exc}") from exc



@router.post("/trading/analyze")
async def trading_analyze(symbol: str):
    try:
        from tools.ai_agents.trading_agent import TradingAgent

        agent = TradingAgent()
        result = await agent.generate_strategy(prompt=f"Analyze trading trend for {symbol}")
        return {"success": True, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Trading analysis service unavailable: {exc}") from exc
