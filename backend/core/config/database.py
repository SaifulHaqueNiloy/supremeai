"""
Database Configuration for SupremeAI 2.0
=========================================

বাংলা: ডাটাবেজ কানেকশন এবং পুল সম্পর্কিত কনফিগারেশন মডিউল।
"""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from core.config.constants import DatabaseConstants


class DatabaseConfig(BaseSettings):
    """Database connection and pool configuration.

    বাংলা: ডাটাবেজ কানেকশন পুলের সব প্যারামিটার — env-driven, zero-hardcode.
    """

    model_config = {"extra": "ignore"}

    # Connection URL
    supabase_database_url: str = Field(default="", description="Supabase PostgreSQL connection URL")

    # Pool configuration
    pool_size: int = Field(
        default=DatabaseConstants.USER_POOL_SIZE,
        description="Database connection pool size",
    )
    max_overflow: int = Field(
        default=DatabaseConstants.USER_POOL_OVERFLOW,
        description="Maximum overflow connections",
    )
    pool_timeout: int = Field(
        default=DatabaseConstants.POOL_TIMEOUT,
        description="Pool timeout in seconds",
    )
    pool_recycle: int = Field(
        default=DatabaseConstants.POOL_RECYCLE,
        description="Pool recycle interval in seconds",
    )
    pool_pre_ping: bool = Field(default=True, description="Verify connection before use")

    @field_validator("supabase_database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """বাংলা: ডাটাবেজ URL যাচাই — শুধুমাত্র পরিচিত প্রোটোকল অনুমোদিত।"""
        if v and not v.startswith(("postgresql", "postgres", "sqlite", "mysql")):
            raise ValueError(f"Database URL must start with a valid protocol, got: {v[:20]}...")
        return v

    @property
    def is_configured(self) -> bool:
        """বাংলা: ডাটাবেজ কনফিগার করা আছে কিনা চেক করে।"""
        return bool(self.supabase_database_url)


# Singleton instance
database_config = DatabaseConfig()
