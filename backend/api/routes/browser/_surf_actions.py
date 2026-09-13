"""Legacy mock surf action endpoints (navigate/click/fill/type/activity feed).

Split out of the former single-module api/routes/browser.py verbatim.
Uses the shared in-place-mutated state singletons from ``_state``.
"""

from datetime import UTC, datetime

from fastapi import Depends
from pydantic import BaseModel

from api.deps import get_current_user_token
from api.routes.browser import router
from api.routes.browser._state import BROWSER_STATUS, RECENT_ACTIVITIES


class NavigateRequest(BaseModel):
    url: str


class ClickRequest(BaseModel):
    selector: str


class FillRequest(BaseModel):
    selector: str
    value: str


class ClickAtRequest(BaseModel):
    x: int
    y: int


class KeyRequest(BaseModel):
    key: str


@router.get("/surf/screenshot")
def get_screenshot():
    # Return a mock transparent 1x1 PNG or read browser screenshot if initialized
    mock_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    return {"screenshot": mock_png}


@router.post("/surf/navigate")
def navigate(req: NavigateRequest):
    BROWSER_STATUS["currentUrl"] = req.url
    RECENT_ACTIVITIES.append(
        {
            "url": req.url,
            "action": "navigate",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    return {"success": True}


@router.post("/surf/click")
def click(req: ClickRequest):
    RECENT_ACTIVITIES.append(
        {
            "url": str(BROWSER_STATUS["currentUrl"]),
            "action": f"click {req.selector}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    return {"success": True}


@router.post("/surf/fill")
def fill(req: FillRequest):
    RECENT_ACTIVITIES.append(
        {
            "url": str(BROWSER_STATUS["currentUrl"]),
            "action": f"fill {req.selector} with {req.value}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    return {"success": True}


@router.post("/surf/click-at")
def click_at(req: ClickAtRequest):
    RECENT_ACTIVITIES.append(
        {
            "url": str(BROWSER_STATUS["currentUrl"]),
            "action": f"click at {req.x}, {req.y}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    return {"success": True}


@router.post("/surf/type-key")
def type_key(req: KeyRequest):
    RECENT_ACTIVITIES.append(
        {
            "url": str(BROWSER_STATUS["currentUrl"]),
            "action": f"type key {req.key}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    return {"success": True}


@router.get("/surf/accessibility")
def get_accessibility_tree():
    return {"role": "WebArea", "name": "SupremeAI Console", "children": []}


@router.post("/simulate-activity")
def simulate_activity(body: dict[str, str]):
    activity = {
        "url": body.get("url", "http://example.com"),
        "action": body.get("action", "surf"),
        "title": body.get("title", "Page Title"),
        "reasoning": body.get("reasoning", "Exploring content"),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    RECENT_ACTIVITIES.append(activity)
    return activity
