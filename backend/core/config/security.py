"""
Security Configuration for SupremeAI 2.0
=========================================

বাংলা: JWT, OTP, এনক্রিপশন এবং অন্যান্য সিকিউরিটি কনফিগারেশন মডিউল।
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings

from core.config.constants import SecurityConstants


class SecurityConfig(BaseSettings):
    """Security-related configuration.

    বাংলা: JWT, OTP, এনক্রিপশন — সব সিকিউরিটি কনফিগারেশন এখানে।
    """

    model_config = {"extra": "ignore"}

    # ── JWT Configuration ──────────────────────────────────────────────
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expire_minutes: int = Field(
        default=SecurityConstants.JWT_EXPIRE_MINUTES,
        description="JWT token expiration in minutes",
    )

    # ── OTP Configuration ──────────────────────────────────────────────
    otp_length: int = Field(
        default=SecurityConstants.OTP_LENGTH,
        description="OTP character length",
    )
    otp_expiration: int = Field(
        default=SecurityConstants.OTP_EXPIRATION,
        description="OTP expiration in seconds",
    )
    otp_cooldown_seconds: int = Field(
        default=60,
        description="Minimum seconds between OTP requests per admin",
    )

    # ── Password Policy ─────────────────────────────────────────────────
    password_min_length: int = Field(
        default=SecurityConstants.PASSWORD_MIN_LENGTH,
        description="Minimum password length",
    )
    max_login_attempts: int = Field(
        default=SecurityConstants.MAX_LOGIN_ATTEMPTS,
        description="Maximum failed login attempts before lockout",
    )
    account_lockout_duration: int = Field(
        default=SecurityConstants.ACCOUNT_LOCKOUT_DURATION,
        description="Account lockout duration in seconds",
    )

    # ── Circuit Breaker ─────────────────────────────────────────────────
    circuit_breaker_failure_threshold: int = Field(
        default=3,
        description="Failures before circuit opens",
    )
    circuit_breaker_cooldown_period: int = Field(
        default=60,
        description="Seconds before circuit retry",
    )

    # ── Security Context ────────────────────────────────────────────────
    security_context_ttl: int = Field(
        default=86400,
        description="Security context TTL in seconds",
    )
    security_caution_log_ttl: int = Field(
        default=86400,
        description="Caution log TTL in seconds",
    )
    admin_emails: list[str] = Field(
        default_factory=list,
        description="List of admin email addresses",
    )

    # ── API Security ────────────────────────────────────────────────────
    allow_test_auth_bypass: bool = Field(
        default=False,
        description="Allow test authentication bypass (CI only)",
    )
    allow_test_origin_bypass: bool = Field(
        default=False,
        description="Allow test origin bypass (CI only)",
    )
    enforce_anti_hacking: bool = Field(
        default=False,
        description="Enforce anti-hacking measures",
    )
    docs_auth_enabled: bool = Field(default=True, description="Enable docs authentication")
    docs_username: str = Field(default="admin", description="Docs basic auth username")
    docs_password: SecretStr = Field(
        default=SecretStr(""),
        description="Docs basic auth password (env: SUPREMEAI_DOCS_PASSWORD)",
    )

    # ── Rate Limiting ───────────────────────────────────────────────────
    gemini_rpm_limit: int = Field(default=9, description="Gemini requests per minute")
    gemini_tpm_limit: int = Field(default=240_000, description="Gemini tokens per minute")
    gemini_rpd_limit: int = Field(default=475, description="Gemini requests per day")
    groq_rpm_limit: int = Field(default=28, description="GROQ requests per minute")
    groq_tpm_limit: int = Field(default=28_500, description="GROQ tokens per minute")
    groq_rpd_limit: int = Field(default=13_680, description="GROQ requests per day")
    openrouter_rpm_limit: int = Field(default=19, description="OpenRouter requests per minute")
    openrouter_rpd_limit: int = Field(default=45, description="OpenRouter requests per day")
    cloudflare_rpd_limit: int = Field(default=9_000, description="Cloudflare requests per day")
    nvidia_rpm_limit: int = Field(default=38, description="NVIDIA requests per minute")
    nvidia_tpm_limit: int = Field(default=38_000, description="NVIDIA tokens per minute")
    huggingface_rpm_limit: int = Field(default=18, description="HuggingFace requests per minute")
    huggingface_rpd_limit: int = Field(default=950, description="HuggingFace requests per day")

    @field_validator("admin_emails", mode="before")
    @classmethod
    def parse_admin_emails(cls, v: Any) -> list[str]:
        """Parse comma-separated admin emails."""
        if isinstance(v, str):
            return [email.strip() for email in v.split(",") if email.strip()]
        return v or []

    @property
    def jwt_secret(self) -> str:
        """Get JWT secret with caching — production requires explicit secret."""
        if hasattr(self, "_jwt_secret_cache") and self._jwt_secret_cache:
            return self._jwt_secret_cache

        env = os.getenv("ENV", "local")

        # Production: Must be explicitly set
        if env == "production":
            secret = os.getenv("SUPREMEAI_JWT_SECRET") or ""
            if not secret or len(secret) < 64:
                raise RuntimeError("Production JWT secret must be set and >= 64 bytes")
            self._jwt_secret_cache = secret
            return secret

        # Development: Try file, then generate
        local_file = ".secrets/jwt_secret.key"
        file_path = Path(local_file)

        if file_path.exists():
            try:
                secret = file_path.read_text().strip()
                if len(secret) >= 32:
                    self._jwt_secret_cache = secret
                    return secret
            except OSError:
                pass

        # Generate new secret
        new_secret = secrets.token_hex(64)
        self._jwt_secret_cache = new_secret
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(new_secret)
        except OSError:
            logger.warning("Could not persist JWT secret — using in-memory only")

        return new_secret


# Singleton instance
security_config = SecurityConfig()
