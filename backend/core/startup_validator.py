from __future__ import annotations

from core.config import settings
from loguru import logger


class StartupValidator:
    """
    বাংলা মন্তব্য: সার্ভার স্টার্টআপের সময় প্রয়োজনীয় এনভায়রনমেন্ট ভ্যারিয়েবল এবং ডিরেক্টরি ভ্যালিডেশন করে।
    """

    _last_status: dict[str, bool | str | None] = {
        "validated": False,
        "success": False,
        "error": None,
    }

    @classmethod
    async def validate(cls) -> None:
        logger.info("🔍 Running startup validations...")
        try:
            # প্রয়োজনীয় সেটিংস যাচাই করা
            if not settings.app_name:
                raise ValueError("APP_NAME settings cannot be empty")

            logger.info("✅ Startup validations passed successfully.")
            cls._last_status = {"validated": True, "success": True, "error": None}
        except Exception as exc:
            logger.error(f"❌ Startup validation failed: {exc}")
            cls._last_status = {"validated": True, "success": False, "error": str(exc)}
            raise exc

    @classmethod
    def last_status(cls) -> dict:
        return cls._last_status
