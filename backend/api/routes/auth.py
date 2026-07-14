# ruff: noqa: BLE001, B904, E722
from __future__ import annotations

from datetime import UTC
from datetime import datetime
from datetime import timedelta

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


try:
    from jose import JWTError
    from jose import jwt
except ImportError:
    JWTError = Exception  # type: ignore[misc,assignment]
    jwt = None  # type: ignore[assignment]

from core.config import settings
from core.security.rbac import UserContext
from database.supabase_client import db


router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

SECRET_KEY = settings.jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    if jwt is None:
        raise RuntimeError("python-jose[cryptography] is required for token issuance")
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def optional_current_user(
    token: str | None = Depends(oauth2_scheme),
) -> UserContext | None:
    if not token or jwt is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub", "unknown")
        role = payload.get("role", "viewer")
        return UserContext(user_id=user_id, role=role)
    except Exception:  # noqa: BLE001
        return None


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


class MeResponse(BaseModel):
    user_id: str
    role: str
    scopes: tuple[str, ...] = ()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    if not db.client:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Supabase client is not initialized")

    try:
        res = db.client.auth.sign_in_with_password({"email": body.username, "password": body.password})
        if not res.user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user_id = res.user.id
        primary_role = "admin" if "admin" in body.username else "user"
        token_data = {
            "sub": user_id,
            "role": primary_role,
            "email": body.username,
            "method": "supabase_auth",
        }
        access_token = create_access_token(token_data)
        return TokenResponse(access_token=access_token, user_id=user_id, role=primary_role)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest):
    if not db.client:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Supabase client is not initialized")

    try:
        res = db.client.auth.sign_up({"email": body.username, "password": body.password})
        if not res.user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed")

        user_id = res.user.id
        primary_role = "admin" if "admin" in body.username else "user"
        token_data = {
            "sub": user_id,
            "role": primary_role,
            "email": body.username,
            "method": "supabase_auth",
        }
        access_token = create_access_token(token_data)
        return TokenResponse(access_token=access_token, user_id=user_id, role=primary_role)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=MeResponse)
async def me(current_user: UserContext | None = Depends(optional_current_user)):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return MeResponse(user_id=current_user.user_id, role=current_user.role, scopes=current_user.scopes)


@router.get("/verify")
async def verify_token(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    return {"valid": True, "user_id": user.get("sub"), "role": user.get("role"), "message": "Authentication successful"}
