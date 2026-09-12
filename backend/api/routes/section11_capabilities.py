"""Section 11 capability primitives: citations, structured output and memory policy."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from core.llm.structured_output_router import StructuredOutputRouter, StructuredOutputError
from tools.knowledge.citation_store import citation_store

router = APIRouter(prefix="/api/v1/capabilities", tags=["section-11-capabilities"])
_structured = StructuredOutputRouter()


class CitationRequest(BaseModel):
    claim_id: str = Field(min_length=1, max_length=200)
    url: str
    title: str = ""
    excerpt: str = ""
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class StructuredOutputRequest(BaseModel):
    raw: str = Field(min_length=1, max_length=200_000)


@router.post("/citations")
def add_citation(payload: CitationRequest, x_tenant_id: str = Header(...)) -> dict:
    try:
        citation = citation_store.add(tenant_id=x_tenant_id, **payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"citation": citation.__dict__}


@router.get("/citations/{claim_id}")
def get_citations(claim_id: str, x_tenant_id: str = Header(...)) -> dict:
    return {"claim_id": claim_id, "citations": citation_store.for_claim(tenant_id=x_tenant_id, claim_id=claim_id)}


@router.post("/structured-output")
def parse_structured_output(payload: StructuredOutputRequest) -> dict:
    try:
        value = _structured.parse(payload.raw, lambda item: item)
    except StructuredOutputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"valid": True, "value": value}
