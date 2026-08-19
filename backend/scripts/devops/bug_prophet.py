"""Bug Prophet — zero-cost anomaly detection background agent.

বাংলা মন্তব্য:
`core/startup/agents.py`-এর `bug-prophet-anomaly-detector` agent হিসেবে চলে। Render/লগ
সোর্স থেকে এরর-লগ জোগাড় করে naive RCA করে লগ/অ্যালার্ট দেয়। API-key না থাকলে
শান্তভাবে skip করে — কোনো কনফিগারেশন ছাড়াই অ্যাপ চালানো যায় (Zero Breakage নীতি)।

Entry point: `run_anomaly_detector_loop` (async, infinite loop)
  — AgentSupervisor-এর `coro_factory` কন্ট্রাক্ট অনুযায়ী।
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

try:
    from loguru import logger
except ImportError:  # loguru না থাকলে stdlib logger-এ ফলব্যাক
    import logging

    logger = logging.getLogger(__name__)  # type: ignore[assignment]


# ─── Config ──────────────────────────────────────────────────────────────────
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID")  # e.g. srv-cxxx
SUPREMEAI_API_KEY = os.getenv("SUPREMEAI_API_KEY")  # optional: internal alert API
INTERNAL_API_URL = os.getenv("INTERNAL_API_URL", "http://localhost:8000")
DEFAULT_INTERVAL = int(os.getenv("BUG_PROPHET_INTERVAL", "300"))  # 5 min


# ─── Fetch / analyze / alert ─────────────────────────────────────────────────
async def _fetch_error_logs() -> list[str]:
    """Render API থেকে সাম্প্রতিক error-logs আনে (async; httpx না থাকলে skip)।"""
    if not RENDER_API_KEY or not RENDER_SERVICE_ID:
        logger.warning("RENDER_API_KEY / RENDER_SERVICE_ID missing. BugProphet log-fetch skipped.")
        return []

    try:
        import httpx
    except ImportError:
        logger.warning("httpx not installed. BugProphet log-fetch skipped.")
        return []

    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/logs"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params={"limit": 100})
            response.raise_for_status()
            logs = response.json()
        return [
            str(log.get("log", ""))
            for log in logs
            if "error" in str(log.get("log", "")).lower() or "exception" in str(log.get("log", "")).lower()
        ]
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to fetch Render logs: {exc}")
        return []


def _analyze(logs: list[str]) -> str:
    """Naive Root-Cause Analysis — ভারী LLM কল ছাড়াই দ্রুত প্রিডিকশন।"""
    if not logs:
        return "No errors found."

    log_text = "\n".join(logs[-10:])  # শেষ ১০টি এরর
    if "Connection refused" in log_text:
        return "Root Cause Analysis: Database connection refused. Check Supabase pooler."
    if "Timeout" in log_text or "timed out" in log_text.lower():
        return "Root Cause Analysis: Endpoint timeout. Possible infinite loop or slow query."
    if "MemoryError" in log_text or "OutOfMemory" in log_text:
        return "Root Cause Analysis: Out-of-memory. Check worker RAM limits."
    return f"Root Cause Analysis: Anomalies detected. Requires manual inspection.\nPreview:\n{log_text[:200]}"


async def _alert(analysis: str) -> None:
    """Internal Admin Dashboard-এ অ্যালার্ট পাঠায় (API-key না থাকলে skip)।"""
    if not SUPREMEAI_API_KEY:
        logger.warning("SUPREMEAI_API_KEY not configured. Internal alert skipped.")
        return
    try:
        import httpx
    except ImportError:
        return

    payload = {"level": "error", "message": f"🚨 **Bug Prophet Report**\n\n{analysis}"}
    headers = {"x-api-key": SUPREMEAI_API_KEY, "Content-Type": "application/json"}
    url = f"{INTERNAL_API_URL.rstrip('/')}/api/v1/admin/alerts"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        logger.info("Sent BugProphet analysis to Internal Admin Dashboard.")
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to send internal alert: {exc}")


async def _anomaly_cycle() -> None:
    """একটি সম্পূর্ণ detect → analyze → alert cycle।"""
    error_logs = await _fetch_error_logs()
    if not error_logs:
        logger.info("BugProphet: system healthy (no error logs found).")
        return
    logger.info(f"BugProphet: found {len(error_logs)} error log entries.")
    analysis = _analyze(error_logs)
    logger.warning(analysis)
    await _alert(analysis)


# ─── Main loop (AgentSupervisor contract) ────────────────────────────────────
async def run_anomaly_detector_loop(interval_seconds: int | None = None) -> None:
    """Infinite anomaly-detection loop — AgentSupervisor `coro_factory` হিসেবে চলে।

    প্রতি interval-এ `_anomaly_cycle` চালায়। কোনো cycle ব্যর্থ হলে লুপ থামে না;
    error লগ করে পরের cycle-এ চলে (supervisor-কে false-restart এড়াতে)।
    """
    interval = interval_seconds or DEFAULT_INTERVAL
    logger.info(f"🚨 BugProphet Anomaly Detector started (interval={interval}s).")
    while True:
        try:
            await _anomaly_cycle()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error(f"BugProphet cycle failed: {exc}")
        await asyncio.sleep(interval)


if __name__ == "__main__":  # pragmatic CLI: `python scripts/devops/bug_prophet.py`
    asyncio.run(run_anomaly_detector_loop(interval_seconds=60))


__all__ = ["run_anomaly_detector_loop", "_analyze", "_fetch_error_logs", "_alert"]
