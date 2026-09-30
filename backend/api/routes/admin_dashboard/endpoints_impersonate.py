"""Impersonation endpoints
(POST /admin-api/users/impersonate/{username}, POST /admin-api/impersonate)."""

# বাংলা মন্তব্য: #2515 ফিক্স — impersonation token-এর lifecycle আগে অসীম ছিল: কোনো
# exp/iat/jti ছিল না, ফলে টোকেন কখনো মেয়াদ শেষ হতো না এবং revocation registry-ও
# কাজ করত না (revocation jti-ভিত্তিক)। এখন সব impersonation token canonical
# `auth.create_access_token` দিয়ে মিন্ট হয় — exp/iat/jti/type স্বয়ংক্রিয়ভাবে যুক্ত,
# সংক্ষিপ্ত dedicated TTL-সহ (৩০ মিনিট)। এছাড়া /impersonate একটি অজানা user-এর জন্যও
# টোকেন মিন্ট করত — এখন 404 (fail-closed)।

from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException

from api.routes.admin_auth import require_admin_token
from api.routes.admin_dashboard import load_users, router
from api.routes.admin_dashboard._models import ImpersonateRequest
from api.routes.auth import create_access_token

# বাংলা মন্তব্য: impersonation হলো high-privilege অস্থায়ী অধিকার — সাধারণ access token
# থেকে ছোট TTL রাখা নীতিগতভাবে জরুরি (leak-এর ঝুঁকি সীমিত রাখতে)।
_IMPERSONATION_TTL = timedelta(minutes=30)


def _mint_impersonation_token(
    *, uid: str, role: str, impersonator: str
) -> str:
    """বাংলা: impersonation token — canonical auth pipeline (exp/iat/jti সহ) দিয়ে।"""
    now = datetime.now(UTC)
    return create_access_token(
        {
            "uid": uid,
            "role": role,
            "impersonator": impersonator,
            "impersonation": True,
            # বাংলা মন্তব্য: type কে আলাদা করে 'impersonation' রাখা হলো যাতে ভবিষ্যতে
            # auth middleware চাইলে impersonation scope আলাদাভাবে শনাক্ত করতে পারে।
            "type": "impersonation",
        },
        expires_delta=_IMPERSONATION_TTL,
    )


@router.post("/users/impersonate/{username}")
async def impersonate_user(username: str, current_admin: dict = Depends(require_admin_token)):
    users = load_users()
    target = next((u for u in users if u["username"] == username), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    impersonation_token = _mint_impersonation_token(
        uid=target["username"],
        role=target["role"],
        impersonator=current_admin.get("uid", "admin"),
    )
    return {
        "status": "success",
        "impersonation_token": impersonation_token,
        "user": target,
    }


@router.post("/impersonate")
async def impersonate_by_payload(
    payload: ImpersonateRequest, current_admin: dict = Depends(require_admin_token)
):
    """Impersonate user via JSON payload for CommandCenter."""
    users = load_users()
    target = next(
        (
            u
            for u in users
            if u["username"] == payload.user_id or str(u.get("id")) == payload.user_id
        ),
        None,
    )
    # বাংলা মন্তব্য: #2515 — অজানা user-এর জন্য টোকেন মিন্ট বন্ধ; শুধু বিদ্যমান user-ই
    # impersonate-যোগ্য (fail-closed, উপরের endpoint-এর সঙ্গে একই নীতি)।
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    token = _mint_impersonation_token(
        uid=target["username"],
        role=target.get("role", "user"),
        impersonator=current_admin.get("uid", "admin"),
    )
    return {"token": token, "user": target}
