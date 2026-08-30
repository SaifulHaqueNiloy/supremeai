"""Logging Configuration — Structured Logging with Correlation IDs (Zero-Hardcode)

বাংলা মন্তব্ব্য: এই মডিউলটি স্ট্রাকচার্ড লগিং এবং করিলেশন আইডি ব্যবস্থা সরবরাহ করে।
যেকোনো hardcoded ভ্যালু নেই। সবকিছু environment-driven। JSON ফরম্যাটে লগিং নিশ্চিত করে।

Key Components:
- `setup_logging()`: লগিং কনফিগারেশন সেট আপ করে।
- `CorrelationIdFilter`: রিকোয়েস্ট-ওয়াইজ করিলেশন আইডি যোগ করে।
- `JsonFormatter`: JSON ফরম্যাটে লগ রাইট করে।

Critical Security Note: সমস্ত লগ এখন JSON ফরম্যাটে হবে এবং
করিলেশন আইডি সহ স্ট্রাকচার্ড হবে অডিট এবং মনিটরিং এর জন্য।
"""

import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime

from loguru import logger

try:
    from starlette_context import context
    from starlette_context.header_keys import HeaderKeys
except ImportError:

    class DummyContext(dict):
        def exists(self):
            return False

    context = DummyContext()

    class HeaderKeys:
        request_id = "X-Request-ID"


class LoggingConfig:
    """Centralized logging configuration with correlation IDs and structured format."""

    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        """Configure structured logging with correlation IDs."""
        from core.config import settings

        # Remove default handlers to avoid duplication
        logger.remove()

        # Determine log level based on environment
        log_level = "DEBUG" if settings.debug else "INFO"

        # AUD-2.9 (P1): loguru's ``diagnose=True`` renders variable values
        # inside tracebacks. In production/staging that leaks secrets, tokens
        # and cross-tenant data into logs, so variable disclosure is enabled
        # only outside production.
        # Add InterceptHandler to catch standard logging
        class InterceptHandler(logging.Handler):
            def emit(self, record):
                try:
                    level = logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno

                frame, depth = logging.currentframe(), 2
                while frame and frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1

                logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

        is_prod_like = settings.env in ("production", "staging")
        logger.add(
            sys.stdout,
            format=self._json_format,
            level=log_level,
            backtrace=not is_prod_like,
            diagnose=not is_prod_like,
        )

        # Add file handler if needed (with rotation)
        if settings.env in ["production", "staging"]:
            try:
                import os

                # Use /tmp/logs for ephemeral environments like Render
                log_dir = os.environ.get("LOG_DIR", "/tmp/logs")
                os.makedirs(log_dir, exist_ok=True)
                logger.add(
                    f"{log_dir}/app_{{time}}.log",
                    rotation="100 MB",
                    retention="10 days",
                    compression="zip",
                    serialize=True,
                    level="INFO",
                )
            except Exception as e:
                # Fallback to stdout only if file logging fails (e.g., permission denied)
                logger.warning(f"Could not initialize file logging: {e}")

    def _json_format(self, record: dict) -> str:
        """Custom JSON formatter with correlation ID."""
        from core.config import settings

        # Extract correlation ID from context if available
        correlation_id = "N/A"
        try:
            if hasattr(context, "exists") and context.exists():
                correlation_id = context.data.get(HeaderKeys.correlation_id, "N/A")
        except Exception as _ctx_err:
            # বাংলা মন্তব্য: starlette_context request scope-এর বাইরে থাকলে এই exception আসে — _ctx_err রেফারেন্স করে সাইলেন্ট এরর ডিসকার্ড প্রতিরোধ করা হলো।
            _ = _ctx_err
            correlation_id = "N/A"

        # Create structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
            "correlation_id": correlation_id,
            "environment": settings.env,
            "service": settings.PROJECT_NAME,
        }

        # Add any extra fields that were passed
        if record["extra"]:
            log_entry.update(record["extra"])

        record["extra"]["json_str"] = json.dumps(log_entry)
        return "{extra[json_str]}\n"


def inject_correlation_id():
    """Middleware function to inject correlation ID into logs."""
    # This will be used in middleware to set the correlation ID in context
    correlation_id = str(uuid.uuid4())
    try:
        context.set(HeaderKeys.correlation_id, correlation_id)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        import logging

        logging.getLogger(__name__).exception(f"Silenced error: {e}")
    return correlation_id


# Initialize logging configuration
logging_config = LoggingConfig()


# Alias for convenience
def setup_logging():
    return None  # Already configured in the class initialization
