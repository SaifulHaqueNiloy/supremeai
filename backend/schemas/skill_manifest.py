from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class SkillStatus(str, Enum):
    STAGING = "staging"
    QUARANTINE = "quarantine"
    APPROVED = "approved"
    EPHEMERAL = "ephemeral"
    REJECTED = "rejected"
    DEPRECATED_PENDING = "deprecation_pending"

class SkillPermissions(BaseModel):
    allow_network: bool = Field(default=False, description="স্কিলটি ইন্টারনেট অ্যাক্সেস করতে পারবে কিনা")
    allowed_domains: List[str] = Field(default_factory=list, description="নেটওয়ার্ক ট্রাস্টেড ওরিজিন ডোমেইন লিস্ট")
    allow_filesystem_write: bool = Field(default=False, description="লোকাল ফাইলে রাইট করার অনুমতি")
    required_env_vars: List[str] = Field(default_factory=list, description="কাজ করার জন্য প্রয়োজনীয় পরিবেশ ভ্যারিয়েবল")

class SkillManifest(BaseModel):
    skill_id: str = Field(..., description="ইউনিক স্কিল আইডেন্টিফায়ার (slug)")
    name: str = Field(..., description="স্কিলের মানব-পাঠ্য নাম")
    description: str = Field(..., description="FastAPI বা এজেন্ট রাউটার যার মাধ্যমে ম্যাচিং করবে")
    version: str = Field(default="1.0.0")
    source_url: HttpUrl = Field(..., description="ভেরিফায়েড MCP বা গিটহাব রিপোজিটরি উৎস")
    checksum: str = Field(..., description="SHA-256 কোড ইন্টিগ্রিটি হ্যাশ")
    status: SkillStatus = Field(default=SkillStatus.STAGING)
    permissions: SkillPermissions = Field(default_factory=SkillPermissions)

    # ইউজেস এবং মেটাডেটা ট্র্যাকিং
    usage_count: int = Field(default=0)
    failure_count: int = Field(default=0)
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
