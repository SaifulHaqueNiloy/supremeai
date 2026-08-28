import os

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.security.authentication.rbac import get_current_user_token as verify_token_dependency
from database.supabase_client import SupabaseDB

router = APIRouter(prefix="/keys", tags=["User Keys"])

# Simple encryption setup for demo/development purposes
# In production, use AWS KMS, HashiCorp Vault, or similar
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a temporary key if none provided (keys will be lost on restart)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
try:
    cipher_suite = Fernet(ENCRYPTION_KEY.encode())
except Exception:
    # Fallback to random if invalid key was provided in env
    cipher_suite = Fernet(Fernet.generate_key())


class KeyCreate(BaseModel):
    provider: str
    api_key: str


class KeyResponse(BaseModel):
    provider: str
    created_at: str


def encrypt_key(api_key: str) -> str:
    return cipher_suite.encrypt(api_key.encode()).decode()


def decrypt_key(encrypted_key: str) -> str:
    return cipher_suite.decrypt(encrypted_key.encode()).decode()


@router.post("/", response_model=KeyResponse)
async def create_or_update_key(key_data: KeyCreate, user: dict = Depends(verify_token_dependency)):
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    encrypted_key = encrypt_key(key_data.api_key)

    db = SupabaseDB()
    # Assuming upsert via Supabase RPC or direct table access
    # We will use direct table access here
    try:
        response = (
            await db.client.table("user_keys")
            .upsert(
                {"user_id": user_id, "provider": key_data.provider, "encrypted_key": encrypted_key},
                on_conflict="user_id,provider",
            )
            .execute()
        )

        data = response.data[0]
        return KeyResponse(provider=data["provider"], created_at=data["created_at"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[KeyResponse])
async def list_keys(user: dict = Depends(verify_token_dependency)):
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = SupabaseDB()
    try:
        response = (
            await db.client.table("user_keys")
            .select("provider, created_at")
            .eq("user_id", user_id)
            .execute()
        )
        return [
            KeyResponse(provider=row["provider"], created_at=row["created_at"])
            for row in response.data
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
