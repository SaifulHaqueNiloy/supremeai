from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

router = APIRouter(prefix="/admin-api/commandcenter", tags=["Command Center"])

@router.get("/health")
async def command_health():
    return {"status": "ok"}

@router.get("/metrics")
async def command_metrics():
    return {}

@router.get("/events")
async def command_events():
    return []
