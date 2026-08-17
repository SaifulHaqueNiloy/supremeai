from fastapi import APIRouter
from pydantic import BaseModel

from utils.branding import MODEL_DISPLAY, PROVIDER_DISPLAY

router = APIRouter(
    prefix="/config/public",
    tags=["public_config"],
)


class PublicConfigResponse(BaseModel):
    adminEmail: str  # -- camelCase required to match frontend JSON API contract
    maxConcurrency: int  # -- camelCase required to match frontend JSON API contract
    features: dict[str, bool]


@router.get("", response_model=PublicConfigResponse)
async def get_public_config():
    # In a real database-driven app, fetch these from DB or environment securely.
    # We return safe defaults here.
    return PublicConfigResponse(
        adminEmail="admin@supremeai.dev",
        maxConcurrency=3,
        features={"selfHealing": True, "costGuard": True},
    )


@router.get("/branding")
async def get_public_branding():
    """Return the canonical SupremeAI model/provider branding maps.

    Public (no auth) so the customer dashboard can brand model names without
    an admin token. The frontend uses this as the single source of truth,
    falling back to its local copy when offline.
    """
    return {
        "models": {k: v["label"] for k, v in MODEL_DISPLAY.items()},
        "providers": PROVIDER_DISPLAY,
    }
