"""Anti-Hacking Agent — context-aware checks + JIT OTP routing (Admin API only).

Alert-only by default (ENFORCE_ANTI_HACKING=false): logs + notifies on context
mismatch but never blocks. Flip the env var to enforce once false-positive
rate from VPNs/CGNAT/mobile-switching has been observed and is acceptable.

বাংলা মন্তব্য: অ্যাডমিন সিকিউরিটি ওটিপি মিডলওয়্যার। এটি ইউজারের আইপি, কান্ট্রি ও ডিভাইস ফিঙ্গারপ্রিন্ট ভেরিফিকেশন চেক করে।
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
            "fingerprint": request.headers.get("x-device-fingerprint", "unknown"),
        }
        request.state.security_signal = signal

        admin_id = getattr(getattr(request.state, "user", None), "get", lambda *_: None)("sub")
        if admin_id:
            if redis_manager and redis_manager.client:
                key = f"{_CONTEXT_KEY_PREFIX}{admin_id}"
                raw_last = await redis_manager.get_cache(key)
                last = json.loads(raw_last) if raw_last else None

                mismatch = False
                if last:
                    ip_country_mismatch = (last.get("ip") != signal["ip"] or last.get("country") != signal["country"])
                    last_fp = last.get("fingerprint")
                    if last_fp and last_fp != "unknown":
                        # বাংলা মন্তব্য: ফিঙ্গারপ্রিন্ট মিললে আইপি পরিবর্তন হলেও ওটিপি লাগবে না (ভিপিএন/মোবাইল নেটওয়ার্কের জন্য)
                        mismatch = ip_country_mismatch and (last_fp != signal["fingerprint"])
                    else:
                        mismatch = ip_country_mismatch

                if mismatch:
                    code = f"{secrets.randbelow(900000) + 100000}"
                    await send_otp(admin_id, code, signal)
                    request.state.security_otp_pending = True

                    # বাংলা মন্তব্য: ওটিপি কোড ৫ মিনিটের জন্য Redis-এ রাখা হচ্ছে যাচাইয়ের জন্য
                    await redis_manager.set_cache(
                        f"security:otp_pending:{admin_id}",
                        json.dumps({"code": code, "signal": signal}),
                        ex_seconds=300,
                    )

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
