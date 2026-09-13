"""Crown Jewel mock endpoints + the legacy in-memory task-step executor.

Split out of the former single-module api/routes/browser.py verbatim.
NOTE: ``execute_step`` (POST /tasks/{id}/step) appears here because it sits
between the Crown-Jewel routes and the session-store routes in the original
file — keeping it in this module preserves the exact route registration
order. It reads TASKS (in-place only) from ``_tasks``.
"""

import hashlib
from typing import Any

from fastapi import HTTPException, Response

from api.routes.browser import router
from api.routes.browser._tasks import TASKS

# --- Crown Jewel Endpoints ---


@router.post("/browse-session")
def browse_session(body: dict[str, Any]):
    raw_url = str(body.get("url") or "")
    session_hash = hashlib.sha256(raw_url.encode("utf-8")).hexdigest()[:16]
    return {"success": True, "session_id": f"sess_{session_hash}"}


@router.post("/ai-action")
def ai_action(body: dict[str, Any]):
    action = body.get("action")
    return {
        "success": True,
        "action": action,
        "response": f"AI successfully processed {action}",
        "summary": "This is a mock summary for " + str(body.get("url")),
        "analysis": "This is a mock analysis.",
        "links": [],
        "issues": [],
        "criticalIssues": [],
    }


@router.post("/security-scan")
def security_scan(body: dict[str, Any]):
    return {"success": True, "score": 100, "issues": []}


@router.post("/screenshot")
def capture_screenshot(body: dict[str, Any]):
    # Returns the mock screenshot already in /surf/screenshot
    mock_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    import base64

    return Response(content=base64.b64decode(mock_png_base64), media_type="image/png")


# -----------------------------


@router.post("/tasks/{id}/step")
def execute_step(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    # Simulate a step execution
    return {
        "success": True,
        "action": "navigated to dashboard",
        "details": "Autonomous step succeeded",
    }
