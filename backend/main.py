"""SupremeAI 2.0 — Entry point. Handles ENV bootstrap, signal handling, and Uvicorn launch.

বাংলা: রুট এন্ট্রি পয়েন্ট। ENV সেটআপ, সিগন্যাল হ্যান্ডলিং এবং সার্ভার লঞ্চ।
"""
import os
import signal
import sys

if not os.getenv("ENV"):
    os.environ["ENV"] = os.getenv("SUPREMEAI_DEFAULT_ENV", "local")

import uvicorn
from loguru import logger

from core.app import app
from core.config import settings
from core.logging_config import setup_logging

setup_logging()


def _handle_sigterm(signum: int, frame: object) -> None:  # noqa: ANN401
    """SIGTERM/SIGINT handler — performs graceful shutdown."""
    logger.info("Received shutdown signal. Performing graceful shutdown...")
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_sigterm)
signal.signal(signal.SIGINT, _handle_sigterm)


def run_server() -> None:
    """Boot the Uvicorn server with config-driven settings.

    বাংলা: কনফিগ-ড্রিভেন সেটিংস দিয়ে Uvicorn সার্ভার বুট।
    """
    port = int(os.getenv("PORT", str(settings.port)))
    is_local = settings.env == "local"
    uvicorn_kwargs: dict = {
        "host": settings.host,
        "port": port,
        "log_level": os.getenv("UVICORN_LOG_LEVEL", "info"),
        "access_log": os.getenv("UVICORN_ACCESS_LOG", "true").lower() == "true",
        "timeout_keep_alive": int(os.getenv("UVICORN_KEEP_ALIVE_TIMEOUT", "30")),
    }
    if is_local:
        uvicorn_kwargs["reload"] = True
    else:
        uvicorn_kwargs["reload"] = False
        # বাংলা: UVICORN_WORKERS env var ব্যবহার করা হয়, GUNICORN_WORKERS deprecated
        workers = int(os.getenv("UVICORN_WORKERS", "4"))
        if workers > 1:
            uvicorn_kwargs["workers"] = workers

    try:
        # বাংলা: app-এর সরাসরি রেফারেন্স ব্যবহার, যাতে মডিউল রিলোডিং পরিবর্তনে ভাঙ্গবে না
        uvicorn.run(app, **uvicorn_kwargs)
    except RuntimeError as exc:
        logger.critical(f"Server failed to start (configuration error): {exc}")
        if settings.sentry_dsn:
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(exc)
            except Exception:
                pass
        sys.exit(1)
    except OSError as exc:
        logger.critical(f"Server failed to start (port/bind error on {settings.host}:{port}): {exc}")
        if settings.sentry_dsn:
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(exc)
            except Exception:
                pass
        sys.exit(1)


if __name__ == "__main__":
    run_server()
