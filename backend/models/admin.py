"""
SupremeAI 2.0 — Admin Pydantic Models
বাংলা মন্তব্য: অ্যাডমিন অথেন্টিকেশন ও ম্যানেজমেন্ট রাউটগুলোর জন্য ইনপুট ভ্যালিডেশন স্কিমা
"""

from pydantic import BaseModel, Field


class AdminFirebaseLoginRequest(BaseModel):
    id_token: str = Field(..., description="Firebase ID token")
    trusted_device_token: str | None = Field(None, description="Optional 30-day trusted browser device token")


class AdminFirebaseTotpSetupRequest(BaseModel):
    id_token: str = Field(..., description="Firebase ID token")


class AdminFirebaseTotpVerifyRequest(BaseModel):
    id_token: str = Field(..., description="Firebase ID token")
    otp: str = Field(..., description="TOTP MFA OTP code")
    trust_device: bool = Field(False, description="Optionally trust this browser for 30 days to bypass OTP")


class AdminEasyLoginRequest(BaseModel):
    code: str = Field(..., description="Easy login authentication code")


class UserContext(BaseModel):
    user_id: str
    role: str = "viewer"
    roles: list[str] = Field(default_factory=list)
    tenant_id: str | None = Field(None, description="Multi-tenant isolation identifier")
    expires_at: str | None = None
    scopes: tuple[str, ...] | None = None
