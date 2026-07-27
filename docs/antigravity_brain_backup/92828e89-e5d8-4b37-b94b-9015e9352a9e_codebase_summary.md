# Codebase Summary - Split APIs & Device Fingerprinting

This document contains the complete and final codebase implementation of the split User/Admin APIs, Redis simulator state migration, JIT OTP router, and client-side device fingerprinting.

---

## 1. Backend Entrypoints and Core Settings

### `backend/main.py`
```python
# backend/main.py
"""SupremeAI 2.0 — FastAPI Application Entrypoint.

বাংলা মন্তব্য: মেইন অ্যাপ্লিকেশন এন্ট্রি পয়েন্ট যা প্রোডাকশনে SERVICE_ROLE অনুযায়ী লোড হয়।
"""

from __future__ import annotations

import os
import sys

import uvicorn
from loguru import logger

# বাংলা মন্তব্য: টেস্ট এনভায়রনমেন্টে সম্পূর্ণ অ্যাপ এবং প্রোডাকশনে রোল অনুযায়ী ইউজার/অ্যাডমিন এন্ট্রি পয়েন্ট লোড করা হচ্ছে
if "pytest" in sys.modules:
    from core.app import app
else:
    role = os.getenv("SERVICE_ROLE", "user").lower()
    if role == "admin":
        from core.app_admin import app
    else:
        from core.app_user import app
from core.config import settings
from core.logging_config import setup_logging

setup_logging()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"🚀 Starting SupremeAI 2.0 Core Services on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=settings.debug)
```

### `backend/core/config.py` (Selected additions)
```python
# Selected variables added/validated in backend/core/config.py
user_cors_origins: list[str] = []
admin_cors_origins: list[str] = []
enforce_anti_hacking: bool = False

@property
def discord_otp_webhook_url(self) -> SecretStr | None:
    return self._get_secret("DISCORD_OTP_WEBHOOK_URL")

@property
def resend_api_key(self) -> SecretStr | None:
    return self._get_secret("RESEND_API_KEY")

@property
def admin_notification_email(self) -> str | None:
    return self._get_secret("ADMIN_NOTIFICATION_EMAIL") or "security@supremeai.app"
```

### `backend/core/app.py`
```python
# backend/core/app.py
"""App shell extraction and configurations for backward compatibility."""
from fastapi import FastAPI
# ... (standard initializations)

def build_app_shell(title: str) -> FastAPI:
    fastapi_app = FastAPI(
        title=title,
        version="2.0.0",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        openapi_tags=tags_metadata,
        dependencies=docs_auth_dep,
    )
    # ... (middlewares, exception handlers registration)
    return fastapi_app

# Backward-compatible singleton
app = build_app_shell(title=f"{settings.app_name} (Production Ready)")
# ... (CORS middleware, register_all_routers, router_health_check)
```

### `backend/core/app_user.py`
```python
# backend/core/app_user.py
"""User Portal Entrypoint.

বাংলা মন্তব্য: ইউজার পোর্টালের জন্য নির্দিষ্ট করা বুটস্ট্র্যাপ ফাইল।
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.app import build_app_shell, router_health_check
from core.config import settings
from api.routers import include_user_routers

app = build_app_shell(title=f"{settings.app_name} (User API)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.user_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Tenant-ID", "X-API-Key", "X-Correlation-ID", "X-Device-Fingerprint"],
)

include_user_routers(app)
router_health_check(app)
```

### `backend/core/app_admin.py`
```python
# backend/core/app_admin.py
"""Admin Portal Entrypoint.

বাংলা মন্তব্য: এডমিন পোর্টালের জন্য নির্দিষ্ট করা বুটস্ট্র্যাপ ফাইল।
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.app import build_app_shell, router_health_check
from core.config import settings
from api.routers import include_admin_routers
from middleware.anti_hacking import AntiHackingContextMiddleware

app = build_app_shell(title=f"{settings.app_name} (Admin API)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.admin_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Tenant-ID", "X-API-Key", "X-Correlation-ID", "X-Device-Fingerprint"],
)

app.add_middleware(AntiHackingContextMiddleware)

include_admin_routers(app)
router_health_check(app)
```

---

## 2. API Routes and Router Registration

### `backend/api/routers.py`
```python
# backend/api/routers.py
# Identify admin paths
_admin_paths = {
    "api.routes.simulator_admin", "api.routes.site_actions", "api.routes.llm_gateway",
    "api.routes.browser", "api.routes.evolution", "api.routes.meta_ai",
    "api.routes.admin_dashboard", "api.routes.internal", "api.routes.admin",
    "api.routes.traffic_monitor", "api.routes.admin_librarian", "api.routes.tenant_admin",
    "api.routes.metrics", "api.routes.cloud_mesh"
}

# ADMIN_ROUTERS list
ADMIN_ROUTERS: list[tuple[str, str]] = [
    ("api.routes.health", "/api/v1"),
    ("api.routes.simulator_admin", ""),
    ("api.routes.site_actions", ""),
    ("api.routes.llm_gateway", ""),
    ("api.routes.browser", ""),
    ("api.routes.evolution", "/api/v1"),
    ("api.routes.meta_ai", "/api/v1"),
    ("api.routes.admin_dashboard", ""),
    ("api.routes.internal", ""),
    ("api.routes.admin", ""),
    ("api.routes.traffic_monitor", ""),
    ("api.routes.admin_librarian", "/api"),
    ("api.routes.tenant_admin", "/api"),
    ("api.routes.metrics", ""),
    ("api.routes.cloud_mesh", ""),
]

# USER_ROUTERS list
USER_ROUTERS: list[tuple[str, str]] = [
    r for r in (core_routers + optional_routers)
    if r[0] not in _admin_paths
]

def include_user_routers(app: FastAPI) -> None:
    for router_path, prefix in USER_ROUTERS:
        register_router(app, router_path, prefix=prefix, optional=True)
    if settings.encryption_key and settings.encryption_key.get_secret_value():
        register_router(app, "api.routes.byoc_api", "", optional=True)

def include_admin_routers(app: FastAPI) -> None:
    for router_path, prefix in ADMIN_ROUTERS:
        register_router(app, router_path, prefix=prefix, optional=True)
```

### `backend/api/routes/simulator.py` (Redis-backed state with fallbacks)
```python
# backend/api/routes/simulator.py
"""Simulator user API — device profile / install / session management.

 বাংলা মন্তব্য: সিমুলেটর ইউজার এপিআই যা আপস্ট্যাশ রেডিস ডেটাবেস ব্যবহার করে, কিন্তু টেস্ট এনভায়রনমেন্টে লোকাল মেমোরি ফলব্যাক ব্যবহার করে।
"""
from __future__ import annotations
import json
from datetime import UTC, datetime
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.cache.redis_manager import redis_manager

router = APIRouter(prefix="/api/simulator", tags=["simulator"])

_PROFILE_KEY = "simulator:profile:{user_id}"
_SESSION_KEY = "simulator:session:{user_id}"
_KNOWN_USERS_SET = "simulator:known_users"
_PROFILE_TTL = 30 * 86400

_IN_MEMORY_PROFILES: dict[str, Any] = {}
_IN_MEMORY_SESSIONS: dict[str, Any] = {}
_IN_MEMORY_KNOWN_USERS: set[str] = set()

def _use_redis() -> bool:
    try:
        if redis_manager is None or redis_manager.client is None:
            return False
        url = getattr(redis_manager, "url", "")
        if not url or "mock" in url.lower():
            return False
        return True
    except Exception:
        return False

async def get_or_create_profile(user_id: str) -> dict[str, Any]:
    if not _use_redis():
        if user_id not in _IN_MEMORY_PROFILES:
            _IN_MEMORY_PROFILES[user_id] = {
                "userId": user_id, "installQuota": 5, "activeInstalls": 0, "device": DEVICE_PROFILES[0], "installedApps": []
            }
            _IN_MEMORY_KNOWN_USERS.add(user_id)
        return _IN_MEMORY_PROFILES[user_id]
    
    redis_mgr = redis_manager
    raw = await redis_mgr.get_cache(_PROFILE_KEY.format(user_id=user_id))
    if raw:
        return json.loads(raw)
    
    profile = {
        "userId": user_id, "installQuota": 5, "activeInstalls": 0, "device": DEVICE_PROFILES[0], "installedApps": []
    }
    await _save_profile(user_id, profile)
    await redis_mgr.client.sadd(_KNOWN_USERS_SET, user_id)
    return profile

# ... (set_cache, get_cache wrapper details)
```

### `backend/api/routes/simulator_admin.py`
```python
# backend/api/routes/simulator_admin.py
"""Simulator admin API — device profile / install / session management admin endpoints.

বাংলা মন্তব্য: সিমুলেটর অ্যাডমিন এপিআই যা সিমুলেটর ব্যবহারের স্ট্যাটিস্টিকস ও কোটা ম্যানেজ করে।
"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from api.routes.admin import get_current_admin
from api.routes.simulator import (
    _redis, _use_redis, _KNOWN_USERS_SET, _IN_MEMORY_KNOWN_USERS, get_or_create_profile, _save_profile
)

router = APIRouter(prefix="/api/simulator", tags=["simulator-admin"])

@router.get("/admin/usage")
async def get_all_usage(admin_user: dict = Depends(get_current_admin)):
    if not _use_redis():
        user_ids = list(_IN_MEMORY_KNOWN_USERS)
    else:
        redis_mgr = _redis()
        user_ids = await redis_mgr.client.smembers(_KNOWN_USERS_SET)

    deployments = []
    for user_id in user_ids:
        profile = await get_or_create_profile(user_id)
        for app in profile["installedApps"]:
            deployments.append({
                "appId": app["appId"],
                "deviceType": profile["device"]["type"],
                "previewUrl": app["previewUrl"],
                "status": app["status"],
                "deployedAt": app["installedAt"],
            })
    return {"totalDeployments": len(deployments), "deployments": deployments}

@router.post("/admin/set-quota/{userId}")
async def admin_set_quota(userId: str, quota: int, admin_user: dict = Depends(get_current_admin)):
    profile = await get_or_create_profile(userId)
    profile["installQuota"] = max(1, min(20, quota))
    await _save_profile(userId, profile)
    return profile
```

### `backend/api/routes/admin.py` (Selected endpoint added)
```python
# backend/api/routes/admin.py
class VerifyOtpRequest(BaseModel):
    code: str

@router.post("/verify-otp")
async def verify_otp(payload: VerifyOtpRequest, admin_user: dict = Depends(get_current_admin)):
    """Validate a JIT OTP issued by AntiHackingContextMiddleware and promote the
    pending (mismatched) context to trusted, so the admin isn't re-challenged
    on their next request from this IP/fingerprint.

    বাংলা: অ্যাডমিন OTP সাবমিট করলে এখানে ভ্যালিডেট হয় এবং সফল হলে Redis-এ
    ট্রাস্টেড কনটেক্সট (last_context) আপডেট হয়ে যায়।
    """
    admin_id = admin_user.get("sub", "unknown_admin")

    if not redis_manager or not redis_manager.client:
        raise HTTPException(status_code=503, detail="Security store unavailable")

    pending_key = f"security:otp_pending:{admin_id}"
    raw_pending = await redis_manager.get_cache(pending_key)
    if not raw_pending:
        raise HTTPException(status_code=400, detail="No pending verification for this admin, or it has expired")

    pending = json.loads(raw_pending)

    if not secrets.compare_digest(str(pending["code"]), str(payload.code)):
        logger.warning(f"❌ Failed OTP verification attempt for admin {admin_id}")
        raise HTTPException(status_code=401, detail="Invalid code")

    await redis_manager.set_cache(
        f"security:last_context:{admin_id}",
        json.dumps(pending["signal"]),
        ex_seconds=86400,
    )
    await redis_manager.client.delete(pending_key)

    logger.info(f"✅ Admin {admin_id} passed OTP verification — context promoted to trusted")
    return {"status": "verified"}
```

### `backend/api/routes/auth.py` (Selected additions)
```python
# backend/api/routes/auth.py (Login modification)
@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    # ... (authenticate user via Supabase)
    access_token = create_access_token(token_data)

    # বাংলা মন্তব্য: Phase 2 — Hybrid Fingerprint Login। হেডারটি ঐচ্ছিক, তাই না থাকলেও
    # লগইন স্বাভাবিকভাবে চলবে (ব্রেকিং চেঞ্জ নয়); থাকলে ডিভাইসটি known-devices সেটে যোগ হয়
    # যা AntiHackingContextMiddleware admin scope-এ তৃতীয় সিগন্যাল হিসেবে ব্যবহার করে।
    fingerprint = request.headers.get("x-device-fingerprint")
    if fingerprint and redis_manager and redis_manager.client:
        try:
            await redis_manager.client.sadd(f"device:known:{user_id}", fingerprint)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to register device fingerprint for {user_id}: {exc}")

    return TokenResponse(access_token=access_token, user_id=user_id, role=primary_role)
```

---

## 3. Middleware and Security

### `backend/middleware/anti_hacking.py`
```python
# backend/middleware/anti_hacking.py
"""Anti-Hacking Agent — context-aware checks + JIT OTP routing (Admin API only).

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
                    from loguru import logger
                    logger.warning(f"🔓 [ALERT-ONLY] Context mismatch for admin {admin_id}: {signal} vs last {last}")

                await redis_manager.set_cache(key, json.dumps(signal), ex_seconds=_CONTEXT_TTL)

        return await call_next(request)
```

### `backend/core/otp_router.py`
```python
# backend/core/otp_router.py
"""JIT OTP channel router — Human-in-the-loop delivery for Anti-Hacking Agent.

বাংলা মন্তব্য: অ্যাডমিন অথেনটিকেশনের জন্য ওটিপি সুইচিং রাউটার। ডিসকর্ড ওয়েবহুক এবং রিসেন্ড ইমেল সার্ভিস ব্যবহার করে।
"""
from __future__ import annotations
import httpx
from loguru import logger
from core.config import settings
from core.cache.redis_manager import redis_manager

CHANNEL_DISCORD = "discord"
CHANNEL_EMAIL = "email"
CHANNEL_TELEGRAM = "telegram"
CHANNEL_WHATSAPP = "whatsapp"

_REDIS_KEY_PREFIX = "otp:channel:"

async def get_active_channel(admin_id: str) -> str:
    if redis_manager and redis_manager.client:
        override = await redis_manager.get_cache(f"{_REDIS_KEY_PREFIX}{admin_id}")
        if override:
            return override
    return CHANNEL_DISCORD

# ... (send_otp implementation logic details)
```

---

## 4. Frontend Integration

### `apps/studio-client/src/utils/deviceFingerprint.ts`
```typescript
// apps/studio-client/src/utils/deviceFingerprint.ts
// বাংলা মন্তব্য: কোনো এক্সটার্নাল সার্ভিস ছাড়াই (Zero-Cost) ব্রাউজার/হার্ডওয়্যার সিগন্যাল থেকে
// একটি স্থিতিশীল SHA-256 হ্যাশ তৈরি করা হয়। একই ডিভাইস/ব্রাউজারে বারবার একই ভ্যালু আসে,
// তাই backend-এর AntiHackingContextMiddleware এটাকে IP/country-এর পাশে তৃতীয় সিগন্যাল হিসেবে ব্যবহার করতে পারে।

let cachedFingerprint: string | null = null;
let inFlight: Promise<string> | null = null;

async function computeFingerprint(): Promise<string> {
  const nav = navigator as Navigator & { deviceMemory?: number };
  const raw = [
    navigator.userAgent,
    navigator.language,
    `${screen.colorDepth}`,
    `${screen.width}x${screen.height}`,
    Intl.DateTimeFormat().resolvedOptions().timeZone,
    `${navigator.hardwareConcurrency ?? 'na'}`,
    `${nav.deviceMemory ?? 'na'}`,
    navigator.platform ?? 'na',
  ].join('|');

  try {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw));
    return Array.from(new Uint8Array(buf))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
  } catch (e) {
    console.error('🚨 [FINGERPRINT_HASH_FAILED]: Failed to compute SHA-256 device fingerprint', e);
    return 'fallback_fingerprint';
  }
}

export const getDeviceFingerprint = async (): Promise<string> => {
  if (cachedFingerprint) return cachedFingerprint;
  if (!inFlight) {
    inFlight = computeFingerprint().then((fp) => {
      cachedFingerprint = fp;
      return fp;
    });
  }
  return inFlight;
};

export const primeDeviceFingerprint = (): void => {
  if (typeof window !== 'undefined') {
    void getDeviceFingerprint();
  }
};
```

### `apps/studio-client/src/services/apiClient.ts`
```typescript
// apps/studio-client/src/services/apiClient.ts
// Centralized API Client for SupremeAI 2.0
// বাংলা মন্তব্য: এটি অ্যাপ্লিকেশনের সেন্ট্রাল এপিআই ক্লায়েন্ট যা হেডার, টোকেন এবং সিকিউর রেট লিমিট (429) / ভ্যালিডেশন এরর ইন্টারসেপ্ট করে।

import { getApiBaseUrl, switchActiveBackend } from '../utils/api';
import { getDeviceFingerprint } from '../utils/deviceFingerprint';
import PQueue from 'p-queue';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export const requestQueue = new PQueue({ concurrency: 3 });

let cachedToken: string | null = null;

export const getAuthHeaders = async (): Promise<Record<string, string>> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (cachedToken === null) {
    cachedToken = localStorage.getItem('supremeai_auth_token') || '';
  }

  if (cachedToken) {
    headers['Authorization'] = `Bearer ${cachedToken}`;
  }

  // 🔐 Phase 2: Hybrid Fingerprint Login — AntiHackingContextMiddleware ব্যবহার করে
  // IP/country-এর পাশাপাশি তৃতীয় কনটেক্সট সিগন্যাল হিসেবে
  try {
    headers['X-Device-Fingerprint'] = await getDeviceFingerprint();
  } catch {
    // বাংলা: WebCrypto অনুপস্থিত থাকলে (পুরনো ব্রাউজার) নীরবে বাদ দেওয়া হচ্ছে — request ব্লক হবে না
  }

  return headers;
};

// ... (apiClient wrapper wrappers with async await headers)
```
