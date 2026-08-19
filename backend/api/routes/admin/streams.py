"""Admin → SSE Streams (logs & events) + WebSocket endpoint."""
import asyncio
import json
import os

from fastapi import APIRouter, Query, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.websockets import WebSocketDisconnect
from loguru import logger

from core.utils.time_utils import utc_now

# Imported lazily when needed to avoid circular imports
router = APIRouter()


@router.get("/logs/stream")
def logs_stream():
    async def log_generator():
        log_file = "logs/supremeai.log"
        if not os.path.exists(log_file):
            log_file = "logs/app.log"

        if os.path.exists(log_file):
            try:
                with open(log_file) as f:
                    lines = f.readlines()[-30:]
                    for line in lines:
                        yield f"data: {line.strip()}\n\n"
            except Exception as e:
                yield f"data: Error reading logs: {e}\n\n"

        file_obj = None
        try:
            if os.path.exists(log_file):
                file_obj = open(log_file)
                file_obj.seek(0, os.SEEK_END)

            while True:
                if file_obj:
                    line = file_obj.readline()
                    if line:
                        yield f"data: {line.strip()}\n\n"
                    else:
                        await asyncio.sleep(0.5)
                else:
                    if os.path.exists(log_file):
                        file_obj = open(log_file)
                        file_obj.seek(0, os.SEEK_END)
                    await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            logger.info("Log stream client disconnected")
            raise
        finally:
            if file_obj:
                try:
                    file_obj.close()
                except Exception as exc:
                    logger.exception(f"Failed to close log stream file: {exc}")

    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/events/stream")
def events_stream():
    """SSE stream for real-time dashboard events — mirrors the /admin-api/events HTTP endpoint."""
    events_log_path = "data/dashboard_events.jsonl"
    if not os.path.exists(events_log_path):
        events_log_path = "/app/data/dashboard_events.jsonl"

    async def event_generator():
        if os.path.exists(events_log_path):
            try:
                with open(events_log_path, encoding="utf-8") as f:
                    lines = f.readlines()[-10:]
                    for line in lines:
                        line = line.strip()
                        if line:
                            try:
                                json.loads(line)
                                yield f"data: {line}\n\n"
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                yield f"data: Error reading events: {e}\n\n"

        file_obj = None
        try:
            if os.path.exists(events_log_path):
                file_obj = open(events_log_path, encoding="utf-8")
                file_obj.seek(0, os.SEEK_END)

            while True:
                if file_obj:
                    line = file_obj.readline()
                    if line:
                        line = line.strip()
                        if line:
                            try:
                                json.loads(line)
                                yield f"data: {line}\n\n"
                            except json.JSONDecodeError:
                                await asyncio.sleep(0.1)
                    else:
                        await asyncio.sleep(1.0)
                else:
                    if os.path.exists(events_log_path):
                        file_obj = open(events_log_path, encoding="utf-8")
                        file_obj.seek(0, os.SEEK_END)
                    await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            logger.info("Event stream client disconnected")
            raise
        finally:
            if file_obj:
                try:
                    file_obj.close()
                except Exception as exc:
                    logger.exception(f"Failed to close event stream file: {exc}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/events")
async def get_events(limit: int = Query(50, ge=1, le=200)):
    # বাংলা মন্তব্য: রিয়েল-টাইম সিস্টেম ইভেন্টগুলো JSONL ফাইল থেকে রিটার্ন করার এন্ডপয়েন্ট
    events_log_path = "data/dashboard_events.jsonl"
    if not os.path.exists(events_log_path):
        events_log_path = "/app/data/dashboard_events.jsonl"

    if not os.path.exists(events_log_path):
        return []

    try:
        with open(events_log_path, encoding="utf-8") as f:
            lines = f.readlines()

        events = []
        for line in reversed(lines):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning(f"Skipping malformed event log line: {line.strip()}")

        return events[:limit]
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Error reading events log: {e}")
        raise HTTPException(status_code=500, detail="Could not read event logs.") from e


@router.websocket("/ws")
async def admin_websocket(websocket: WebSocket):
    # Import here to avoid circular dependencies with system module
    from api.routes.admin.system import get_metrics, get_health_map
    from api.routes.admin.providers import get_providers

    await websocket.accept()
    try:
        while True:
            try:
                metrics = get_metrics()
                providers_status = {p["id"]: p["status"] for p in get_providers()}
                health = await get_health_map()
                await websocket.send_json(
                    {
                        "type": "dashboard_update",
                        "data": {
                            "metrics": metrics,
                            "providers": providers_status,
                            "health": health,
                            "timestamp": utc_now().isoformat(),
                        },
                    }
                )
            except Exception as exc:
                logger.debug(f"WS send error: {exc}")
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info("Admin WebSocket client disconnected")
    except Exception as exc:
        logger.error(f"Admin WebSocket error: {exc}")
