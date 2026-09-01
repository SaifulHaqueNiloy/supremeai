from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError as JWTError
from pydantic import BaseModel, EmailStr

from core.cache.redis_manager import redis_manager
from core.config import settings
from core.error_bus import with_error_bus
from core.logging_config import logger
from core.security import is_token_revoked, revoke_token
from core.security.authentication.rbac import UserContext
from database.supabase_client import db

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

ALGORITHM = "HS256"
# বাংলা: ২৪ ঘণ্টার টোকেন অনেক বেশি — অ্যাক্সেস টোকেন ১ ঘণ্টা, রিফ্রেশ টোকেন দীর্ঘ মেয়াদী।
ACCESS_TOKEN_EXPIRE_MINUTES = 60
# বাংলা: রিফ্রেশ টোকেন ৭ দিন — প্রোডাকশন স্ট্যান্ডার্ড।
REFRESH_TOKEN_EXPIRE_DAYS = 7

# বাংলা মন্তব্য (JWT-COOKIE-MIGRATION, ধাপ ১/২): টোকেন এখন থেকে httpOnly cookie
# হিসেবেও সেট হবে, যাতে ফ্রন্টএন্ড JS (localStorage) থেকে টোকেন সরিয়ে আনা যায়।
# ট্রানজিশন পিরিয়ডে response body-তেও টোকেন থাকছে (ব্রেকিং চেঞ্জ নয়) —
# ফ্রন্টএন্ড পুরোপুরি cookie-নির্ভর হয়ে গেলে body থেকে টোকেন সরানো যাবে।
ACCESS_COOKIE_NAME = "supreme_access_token"
REFRESH_COOKIE_NAME = "supreme_refresh_token"
CSRF_COOKIE_NAME = "supreme_csrf_token"


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str | None) -> None:
    """বাংলা: access/refresh টোকেন httpOnly cookie হিসেবে সেট করা হয়, প্লাস একটা
    non-httpOnly CSRF cookie (double-submit pattern) যাতে state-changing
    request-এ CSRF protection করা যায় — JS এই CSRF cookie পড়ে হেডারে পাঠাবে।
    """
    import secrets

    secure = settings.env == "production"
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    if refresh_token:
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh_token,
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/auth",
        )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=secrets.token_urlsafe(32),
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=False,
        secure=secure,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    for name, path in (
        (ACCESS_COOKIE_NAME, "/"),
        (REFRESH_COOKIE_NAME, "/auth"),
        (CSRF_COOKIE_NAME, "/"),
    ):
        response.delete_cookie(key=name, path=path)


async def _token_from_header_or_cookie(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
) -> str | None:
    """বাংলা: আগে Authorization header চেক করা হয় (backward-compat), না পেলে
    httpOnly cookie থেকে fallback করা হয়। এতে পুরনো (localStorage-based)
    এবং নতুন (cookie-based) দুই ধরনের ক্লায়েন্টই চলবে ট্রানজিশনের সময়।
    """
    if token:
        return token
    return request.cookies.get(ACCESS_COOKIE_NAME)


def _get_secret_key() -> str:
    return settings.jwt_secret


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    if jwt is None:
        raise RuntimeError("PyJWT is required for token issuance")
    to_encode = data.copy()
    # বাংলা: iat (issued-at) ও jti (token id) — রিভোকেশন ও অডিট ট্রেইলিং এর জন্য আবশ্যক।
    import uuid as _uuid

    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": to_encode.get("jti") or f"jti-{_uuid.uuid4().hex[:16]}",
            "type": "access",
        }
    )
    return jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """বাংলা: রিফ্রেশ টোকেন — অ্যাক্সেস টোকেন পুনঃপ্রদানের জন্য দীর্ঘ মেয়াদী।"""
    if jwt is None:
        raise RuntimeError("PyJWT is required for token issuance")
    import uuid as _uuid

    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": f"jti-{_uuid.uuid4().hex[:16]}",
            "type": "refresh",
        }
    )
    return jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)


@with_error_bus("optional_current_user")
async def optional_current_user(
    token: str | None = Depends(_token_from_header_or_cookie),
) -> UserContext | None:
    if not token or jwt is None:
        return None
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        # বাংলা: type=access ছাড়া অন্য টোকেন (যেমন refresh) ব্যবহার রোধ।
        if payload.get("type") != "access":
            return None
        # বাংলা মন্তব্য (ROOT-CAUSE FIX, /logout ফিচারের অংশ): logout করা
        # (blacklist-এ থাকা) টোকেন যেন আর valid না ধরা হয়, নাহলে logout-এর
        # পরেও পুরনো access_token দিয়ে /me কাজ করতে থাকবে।
        jti = payload.get("jti")
        if jti and await is_token_revoked(jti):
            return None
        # বাংলা মন্তব্য: JWT ডিকোড সফল হলে UserContext তৈরি করে return করা হচ্ছে।
        user_id = payload.get("sub", "unknown")
        role = payload.get("role", "viewer")
        return UserContext(
            user_id=user_id,
            role=role,
            email=payload.get("email") if isinstance(payload.get("email"), str) else None,
        )
    except (JWTError, ValueError):
        logger.debug("JWT decode failed in optional_current_user", exc_info=True)
        return None


class LoginRequest(BaseModel):
    username: EmailStr
    password: str


class RegisterRequest(BaseModel):
    username: EmailStr
    password: str
    name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    user_id: str
    role: str


class MeResponse(BaseModel):
    user_id: str
    role: str
    scopes: tuple[str, ...] = ()
    email: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, response: Response):
    if not db.client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase client is not initialized",
        )

    # বাংলা: supabase-py এর auth.sign_in_with_password সিঙ্ক্রোনাস — সরাসরি কল করলে
    # event loop ব্লক হয়ে যায়। asyncio.to_thread দিয়ে thread pool-এ পাঠাচ্ছি।
    try:
        res = await asyncio.to_thread(
            db.client.auth.sign_in_with_password,
            {"email": body.username, "password": body.password},
        )
        if not res.user:
            # বাংলা: auth ফেইলিওরে generic message — internal detail লিক করছি না।
            logger.warning(f"Login failed for email={body.username!r}: no user returned")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        user_id = res.user.id
        # বাংলা: ইমেইলটি settings.admin_emails তালিকায় আছে কি না তা দেখে রোল অ্যাসাইন করা হচ্ছে (ঝুঁকিপূর্ণ "admin" in username চেক প্রতিস্থাপিত)।
        is_admin = body.username and any(
            body.username.lower() == admin_email.lower() for admin_email in settings.admin_emails
        )
        primary_role = "admin" if is_admin else "user"
        token_data = {
            "sub": user_id,
            "role": primary_role,
            "email": body.username,
            "method": "supabase_auth",
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # বাংলা মন্তব্য: Phase 2 — Hybrid Fingerprint Login। হেডারটি ঐচ্ছিক, তাই না থাকলেও
        # লগইন স্বাভাবিকভাবে চলবে (ব্রেকিং চেঞ্জ নয়); থাকলে ডিভাইসটি known-devices সেটে যোগ হয়
        # যা AntiHackingContextMiddleware admin scope-এ তৃতীয় সিগন্যাল হিসেবে ব্যবহার করে।
        fingerprint = request.headers.get("x-device-fingerprint")
        if fingerprint and redis_manager and redis_manager.client:
            try:
                await redis_manager.client.sadd(f"device:known:{user_id}", fingerprint)
            except Exception as exc:
                logger.warning(f"Failed to register device fingerprint for {user_id}: {exc}")

        _set_auth_cookies(response, access_token, refresh_token)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
            role=primary_role,
        )
    except HTTPException:
        # বাংলা: নিজে রেইজ করা HTTPException পুনরায় রেইজ করি — বাকি সব exception 500।
        raise
    except Exception as e:
        # বাংলা: অন্য কোনো exception (network, DB, Supabase internal) — ক্লায়েন্টকে
        # generic বার্তা দেখাচ্ছি, কিন্তু server-side এ পূর্ণ stack লগ করছি।
        logger.exception(f"Unexpected login error for email={body.username!r}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login service temporarily unavailable. Please try again.",
        ) from e


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, response: Response):
    if not db.client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase client is not initialized",
        )

    try:
        # বাংলা: sign_up ও সিঙ্ক্রোনাস — to_thread দিয়ে wrap করা হলো।
        res = await asyncio.to_thread(
            db.client.auth.sign_up,
            {"email": body.username, "password": body.password},
        )
        if not res.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed"
            )

        # বাংলা মন্তব্য: যদি ইমেইল ভেরিফিকেশন অন থাকে, তাহলে res.session None হবে। সেক্ষেত্রে ফেক টোকেন না দিয়ে ইউজারকে ভেরিফাই করতে বলব।
        if res.session is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Email confirmation required"
            )

        user_id = res.user.id
        # বাংলা মন্তব্য: ইমেইলটি settings.admin_emails তালিকায় আছে কি না তা দেখে রোল অ্যাসাইন করা হচ্ছে (ঝুঁকিপূর্ণ "admin" in username চেক প্রতিস্থাপিত)।
        is_admin = body.username and any(
            body.username.lower() == admin_email.lower() for admin_email in settings.admin_emails
        )
        primary_role = "admin" if is_admin else "user"
        token_data = {
            "sub": user_id,
            "role": primary_role,
            "email": body.username,
            "method": "supabase_auth",
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        _set_auth_cookies(response, access_token, refresh_token)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
            role=primary_role,
        )
    except HTTPException:
        raise
    except Exception as e:
        # বাংলা: registration-এর ক্ষেত্রেও internal error লিক করছি না।
        logger.exception(f"Unexpected registration error for email={body.username!r}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration service temporarily unavailable. Please try again.",
        ) from e


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    body: RefreshRequest, request: Request | None = None, response: Response | None = None
):
    """বাংলা: রিফ্রেশ টোকেন দিয়ে নতুন অ্যাক্সেস টোকেন প্রদান।

    type=refresh চেক করে access token রিফ্রেশে ব্যবহার রোধ করা হয় — token confusion প্রতিরোধ।
    """
    if jwt is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="JWT service unavailable"
        )
    refresh_token_value = body.refresh_token or (
        request.cookies.get(REFRESH_COOKIE_NAME) if request else None
    )
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing"
        )
    try:
        payload = jwt.decode(refresh_token_value, _get_secret_key(), algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not a refresh token"
        )

    token_data = {
        "sub": payload.get("sub", "unknown"),
        "role": payload.get("role", "viewer"),
        "email": payload.get("email"),
        "method": payload.get("method", "supabase_auth"),
    }
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)
    if response is not None:
        _set_auth_cookies(response, new_access, new_refresh)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user_id=str(token_data["sub"]),
        role=str(token_data["role"]),
    )


@router.get("/me", response_model=MeResponse)
async def me(current_user: UserContext | None = Depends(optional_current_user)):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    # বাংলা মন্তব্য: scopes যদি None হয় তবে MeResponse ভ্যালিডেশন পাস করানোর জন্য খালি টুপল পাস করা হচ্ছে।
    scopes_val = current_user.scopes if current_user.scopes is not None else ()
    return MeResponse(
        user_id=current_user.user_id,
        role=current_user.role,
        scopes=scopes_val,
        email=current_user.email,
    )


@router.post("/logout")
async def logout(
    response: Response,
    token: str | None = Depends(_token_from_header_or_cookie),
):
    """বাংলা মন্তব্য (নতুন এন্ডপয়েন্ট): আগে /logout রুটটাই ছিল না (তাই 404
    আসত)। JWT stateless বলে সত্যিকারের "invalidate" সম্ভব না, কিন্তু ইতিমধ্যেই
    কোডবেসে থাকা Redis-ব্যাকড blacklist (core/security/revoke_token,
    is_token_revoked -- admin_auth.py-তে যেভাবে ব্যবহৃত হয়) পুনঃব্যবহার করে
    টোকেনের jti ব্ল্যাকলিস্ট করে দেওয়া হচ্ছে। এরপর optional_current_user
    (উপরে) revoke-চেক করে, তাই এই টোকেন দিয়ে /me আর কাজ করবে না।

    বাংলা (JWT-COOKIE-MIGRATION): auth cookie থাকলে সেগুলোও ক্লিয়ার করা হচ্ছে।
    """
    _clear_auth_cookies(response)
    if not token or jwt is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from None

    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti:
        await revoke_token(jti, exp=int(exp) if isinstance(exp, (int, float)) else None)
    return {"status": "logged_out"}


@router.get("/verify")
async def verify_token(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    return {
        "valid": True,
        "user_id": user.get("sub"),
        "role": user.get("role"),
        "message": "Authentication successful",
    }
