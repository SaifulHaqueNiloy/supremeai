"""Anti-Hacking Agent — context-aware checks + JIT OTP routing (Admin API only).

Alert-only by default (ENFORCE_ANTI_HACKING=false): logs + notifies on context
mismatch but never blocks. Flip the env var to enforce once false-positive
rate from VPNs/CGNAT/mobile-switching has been observed and is acceptable.

বাংলা মন্তব্য: অ্যাডমিন সিকিউরিটি ওটিপি মিডলওয়্যার। এটি ইউজারের আইপি ও কান্ট্রি ভেরিফিকেশন চেক করে।
"""

from __future__ import annotations

import json
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings
from core.otp_router import send_otp
from core.cache.redis_manager import redis_manager

_CONTEXT_KEY_PREFIX = "security:last_context:"
_CONTEXT_TTL = 86400


class AntiHackingContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        signal = {
            "ip": request.headers.get("x-forwarded-for", "").split(",")[0].strip(),
            "country": request.headers.get("cf-ipcountry", "unknown"),
            "ua": request.headers.get("user-agent", "unknown"),
        }
        request.state.security_signal = signal

        admin_id = getattr(getattr(request.state, "user", None), "get", lambda *_: None)("sub")
        if admin_id:
            if redis_manager and redis_manager.client:
                key = f"{_CONTEXT_KEY_PREFIX}{admin_id}"
                raw_last = await redis_manager.get_cache(key)
                last = json.loads(raw_last) if raw_last else None
                mismatch = last and (last.get("ip") != signal["ip"] or last.get("country") != signal["country"])

                if mismatch:
                    code = f"{secrets.randbelow(900000) + 100000}"
                    await send_otp(admin_id, code, signal)
                    request.state.security_otp_pending = True

                    if settings.enforce_anti_hacking:
                        return JSONResponse(
                            status_code=403,
                            content={
                                "error": "context_mismatch",
                                "detail": "OTP verification required — check your configured channel."
                            },
                        )
                    # alert-only: log and continue
                    from loguru import logger
                    logger.warning(f"🔓 [ALERT-ONLY] Context mismatch for admin {admin_id}: {signal} vs last {last}")

                await redis_manager.set_cache(key, json.dumps(signal), ex_seconds=_CONTEXT_TTL)

        return await call_next(request)
