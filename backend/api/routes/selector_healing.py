from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.session import get_db_session
from models.selector_healing_event import SelectorHealingEvent


router = APIRouter(prefix="/api/admin/selector-healing", tags=["Self-Healing Logs"])


class HealingEventOut(BaseModel):
    id: str
    ts: str
    action_id: int
    original_selector: str
    healed_selector: str
    confidence_score: int
    auto_applied: bool
    screenshot_before_base64: str = ""
    screenshot_after_base64: str = ""


class DecisionIn(BaseModel):
    approve: bool


@router.get("/")
async def get_healing_logs(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(SelectorHealingEvent))
    events = result.scalars().all()

    formatted = []
    for evt in events:
        formatted.append({
            "id": str(evt.id),
            "ts": "", # Add a timestamp field to model later
            "action_id": str(evt.action_id),
            "original_selector": evt.old_selector,
            "healed_selector": evt.new_selector,
            "confidence_score": float(evt.confidence_score),
            "auto_applied": evt.auto_applied,
            "screenshot_before_base64": evt.screenshot_before_url or "",
            "screenshot_after_base64": evt.screenshot_after_url or "",
        })
    return {"items": formatted}


@router.post("/{event_id}/decision")
async def make_healing_decision(event_id: str, payload: DecisionIn, session: AsyncSession = Depends(get_db_session)):
    import uuid
    try:
        eid = uuid.UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event UUID")

    result = await session.execute(select(SelectorHealingEvent).where(SelectorHealingEvent.id == eid))
    evt = result.scalars().first()
    if not evt:
        raise HTTPException(status_code=404, detail="not found")

    evt.auto_applied = payload.approve
    await session.commit()

    return {"status": "success", "event": {
        "id": str(evt.id),
        "ts": "",
        "action_id": str(evt.action_id),
        "original_selector": evt.old_selector,
        "healed_selector": evt.new_selector,
        "confidence_score": float(evt.confidence_score),
        "auto_applied": evt.auto_applied,
        "screenshot_before_base64": evt.screenshot_before_url or "",
        "screenshot_after_base64": evt.screenshot_after_url or "",
    }}
