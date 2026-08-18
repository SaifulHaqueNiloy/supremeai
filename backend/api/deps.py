# backend/api/deps.py
"""Enhanced dependency injection with standardized error handling.

Canonical successor of ``api/dependencies.py``. Re-exports the full dependency
surface (JWT guards, tenant extraction, idempotency) so routes may import from
either path during migration, and provides the async ``get_current_user_token``
with ErrorEventBus integration.

বাংলা: ``dependencies.py``-র পুরো পাবলিক সারফেস এখানে re-export করা হয় যাতে
মাইগ্রেশন পিরিয়ডে দুটো import path-ই কাজ করে। আগে দুটি মডিউলেই আলাদা
``FitnessEngine()`` singleton তৈরি হতো — এখন শুধু একটি (এখান থেকে re-export)।
"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from api.dependencies import (
    get_current_admin,
    get_current_tenant,
    get_fitness_engine,
    get_tenant_db,
    verify_autonomous_agent_token,
    verify_idempotency,
)
from api.errors import raise_unauthorized
from core.error_bus import with_error_bus
from utils.environment import is_test_environment


@with_error_bus(component_name="AuthDependency")
async def get_current_user_token(request: Request) -> dict[str, Any]:
    """Async user-token extractor (ErrorEventBus-integrated).

    বাংলা: AuthMiddleware-ইনজেক্ট করা ``request.state.user`` আগে চেক করা হয়;
    না থাকলে test-environment fallback, নাহলে 401। (``dependencies.py``-র sync
    ভার্সনের জায়গায় — FastAPI async dependency-ই preferred।)
    """
    user = getattr(request.state, "user", None)
    if user:
        return user

    if is_test_environment():
        return {"sub": "admin@supremeai.com", "role": "admin"}

    raise_unauthorized("Missing or invalid authentication token.")
    return None  # type: ignore


__all__ = [
    "get_current_admin",
    "get_current_tenant",
    "get_current_user_token",
    "get_fitness_engine",
    "get_tenant_db",
    "verify_autonomous_agent_token",
    "verify_idempotency",
]

