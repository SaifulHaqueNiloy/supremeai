from fastapi import APIRouter, Depends, HTTPException, WebSocket
from loguru import logger

router = APIRouter(prefix="/ws/command-center", tags=["Command Center WS"])

@router.get("/health")
async def ws_health():
    return {"status": "ok"}
