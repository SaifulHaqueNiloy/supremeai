# backend/api/dependencies.py
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from loguru import logger

from core.evolution.fitness_engine import FitnessEngine
from core.security import verify_token
from core.tenant_db import TenantAwareFirestore

# শেয়ার্ড ইউটিলিটি — টেস্ট এনভায়রনমেন্ট চেক কেন্দ্রীভূত
from utils.environment import is_test_environment


_fitness_engine = FitnessEngine()


def get_fitness_engine() -> FitnessEngine:
    return _fitness_engine


def get_current_user_token(request: Request) -> dict:
    # 1. Check context injected by AuthMiddleware
    user = getattr(request.state, "user", None)
    if user:
        return user

    # 2. Test Environment fallback
    if is_test_environment():
        return {"sub": "admin@supremeai.com", "role": "admin"}

    # 3. Fallback check
    raise HTTPException(status_code=401, detail="Unauthorized")


def get_tenant_db(
    payload: dict = Depends(get_current_user_token),
) -> TenantAwareFirestore:
    """
    Dependency Injection: Extracts tenant_id (user email/uid) from JWT
    and returns a hard-isolated Firestore client.
    """
    tenant_id = payload.get("sub")
    if not tenant_id:
        logger.error("Token payload missing 'sub' (tenant_id) claim.")
        raise HTTPException(status_code=401, detail="Invalid token structure.")

    # রিটার্ন করছে আইসোলেটেড ডিবি ক্লায়েন্ট
    return TenantAwareFirestore(tenant_id=tenant_id)
