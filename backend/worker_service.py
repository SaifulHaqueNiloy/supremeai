"""SupremeAI worker HTTP wrapper — makes the Celery worker viable on Render's free tier.

Render free web services MUST bind $PORT and answer HTTP or they are spun down
forever (and never receive Celery tasks). This module serves a minimal FastAPI
control/health surface and (best-effort) supervises a Celery worker subprocess
so a single free web service can act as both the HTTP endpoint and the queue
consumer. All Celery/Redis wiring is wrapped in try/except: the HTTP service
ALWAYS starts, even if Celery or Redis is unavailable (status becomes degraded).

Run with:  python worker_service.py   (backend/ as working dir)
"""

from __future__ import annotations

import asyncio
import atexit
import contextlib
import importlib.util
import os
import signal
import subprocess
import sys
from collections.abc import Callable
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

PORT = int(os.getenv("PORT", "8080"))
ROLE = os.getenv("SUPREMEAI_SERVICE_ROLE", "worker")
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="SupremeAI Worker", docs_url=None, redoc_url=None, openapi_url=None)
_state: dict[str, Any] = {"celery_proc": None, "degraded": False, "detail": ""}


def _celery_importable() -> bool:
    return importlib.util.find_spec("celery") is not None


def _redis_url() -> str | None:
    """Redis URL from env, falling back to core.config (lazy — that import can raise)."""
    if os.getenv("REDIS_URL"):
        return os.environ["REDIS_URL"]
    try:
        from core.config import settings

        return getattr(settings, "redis_url", None)
    except Exception:
        return None


def _spawn_celery() -> None:
    """Best-effort Celery subprocess spawn. Never raises."""
    try:
        if ROLE != "worker" or not _celery_importable() or not _redis_url():
            return
        _state["celery_proc"] = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "celery",
                "-A",
                "workers.celery_app",
                "worker",
                "--loglevel=INFO",
                "-c",
                "2",
            ],
            cwd=BACKEND_DIR,
            env=os.environ.copy(),
        )
        print(f"[worker_service] celery spawned pid={_state['celery_proc'].pid}", flush=True)
    except Exception as exc:  # HTTP service must survive celery/redis failures
        _state.update(degraded=True, detail=f"celery spawn failed: {exc}")


def _terminate_celery() -> None:
    proc: subprocess.Popen[bytes] | None = _state.get("celery_proc")
    if proc is None:
        return
    with contextlib.suppress(Exception):
        proc.terminate()
        proc.wait(timeout=10)


def _queue_call(op: str, *args: Any, **kwargs: Any) -> Any:
    """Run an async core.queue.task_queue_enhanced API in a fresh event loop.

    Runs inside a worker thread (via asyncio.to_thread) so asyncio.run is legal.
    Import is lazy: that module raises at import time when redis_url is missing
    (task_queue_enhanced.py ~line 583) — module top level here must never raise.
    """
    from core.queue import task_queue_enhanced as tq

    async def _inner() -> Any:
        result: Callable[..., Any] = getattr(tq, op)(*args, **kwargs)
        return await result

    return asyncio.run(_inner())


def _drain_once() -> dict[str, Any]:
    """Submit a no-op heartbeat through TaskQueue and await its result (e2e proof)."""
    from core.queue.task_queue_enhanced import get_task_queue

    async def _inner() -> dict[str, Any]:
        async def heartbeat() -> str:
            return "heartbeat-ok"

        queue = get_task_queue()
        task_id = await queue.submit_task(heartbeat, task_name="worker_heartbeat", timeout=30)
        result = await queue.get_result(task_id, timeout=30)
        return {"task_id": task_id, "status": result.status, "result": result.result}

    return asyncio.run(_inner())


@app.get("/")
async def root() -> dict[str, Any]:
    return {"service": "supremeai-worker", "status": "ok", "role": ROLE}


@app.get("/health")
@app.get("/api/v1/health/live")
async def health() -> dict[str, str]:
    return {"status": "ok"}


class TaskSubmission(BaseModel):
    goal: str = Field(min_length=1, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)


async def _process_task(payload: dict[str, Any]) -> dict[str, Any]:
    # The worker contract is intentionally capability-neutral. Domain executors can
    # consume this payload later without changing the frontend lifecycle contract.
    return {"message": "Task accepted by worker", "goal": payload["goal"], "metadata": payload.get("metadata", {})}


@app.post("/tasks")
async def submit_task(request: TaskSubmission) -> JSONResponse:
    try:
        from core.queue.task_queue_enhanced import get_task_queue

        queue = get_task_queue()
        task_id = await queue.submit_task(_process_task, request.model_dump(), task_name="supremeai_task")
        return JSONResponse({"task_id": task_id, "status": "pending"}, status_code=202)
    except Exception as exc:
        _state.update(degraded=True, detail=f"task submit failed: {exc}")
        return JSONResponse({"status": "degraded", "detail": str(exc)[:200]}, status_code=503)


@app.get("/tasks/{task_id}")
async def task_status(task_id: str) -> JSONResponse:
    try:
        from core.queue.task_queue_enhanced import get_task_queue

        status = await get_task_queue().get_status(task_id)
        if status == "unknown":
            raise HTTPException(status_code=404, detail="Task not found")
        return JSONResponse({"task_id": task_id, "status": status})
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@app.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str) -> JSONResponse:
    try:
        from core.queue.task_queue_enhanced import get_task_queue

        cancelled = await get_task_queue().cancel_task(task_id)
        if not cancelled:
            raise HTTPException(status_code=409, detail="Task cannot be cancelled")
        return JSONResponse({"task_id": task_id, "status": "cancelled"})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@app.get("/tasks/stats")
async def tasks_stats() -> JSONResponse:
    try:
        stats = await asyncio.wait_for(
            asyncio.to_thread(_queue_call, "get_queue_stats"), timeout=10.0
        )
        return JSONResponse({"status": "ok", "stats": stats})
    except Exception as exc:
        _state.update(degraded=True, detail=f"queue stats failed: {exc}")
        return JSONResponse({"status": "degraded", "detail": str(exc)[:200]}, status_code=503)


@app.post("/tasks/drain")
async def tasks_drain() -> JSONResponse:
    try:
        proof = await asyncio.wait_for(asyncio.to_thread(_drain_once), timeout=45.0)
        return JSONResponse({"status": "ok", "queue": "asyncio", **proof})
    except Exception as exc:
        _state.update(degraded=True, detail=f"drain failed: {exc}")
        return JSONResponse({"status": "degraded", "detail": str(exc)[:200]}, status_code=503)


@app.get("/worker/status")
async def worker_status() -> dict[str, Any]:
    proc: subprocess.Popen[bytes] | None = _state.get("celery_proc")
    return {
        "service": "supremeai-worker",
        "role": ROLE,
        "celery_spawned": proc is not None,
        "celery_pid": proc.pid if proc else None,
        "celery_alive": bool(proc and proc.poll() is None),
        "redis_configured": _redis_url() is not None,
        "degraded": bool(_state["degraded"]),
        "detail": _state["detail"],
    }


# ── Celery subprocess lifecycle (atexit is the reliable path; uvicorn replaces
#    our signal handlers when it installs its own, but both are registered) ────
atexit.register(_terminate_celery)
for _sig in (signal.SIGTERM, signal.SIGINT):
    with contextlib.suppress(ValueError, OSError):  # non-main thread / unsupported
        signal.signal(_sig, lambda *_: (_terminate_celery(), sys.exit(0)))

_spawn_celery()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
