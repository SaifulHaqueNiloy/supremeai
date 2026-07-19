#!/usr/bin/env python3
"""
admin/__init__.py
=================
SupremeAI 2.0 — Admin Package Initialization

বাংলা মন্তব্য: অ্যাডমিন কন্ট্রোল প্যানেল, গড মোড, RBAC, এবং
অডিট লগিং মডিউলগুলোর প্যাকেজ ইনিশিয়ালাইজেশন।
"""

from __future__ import annotations

from admin.god import AdminGodLayer
from admin.god import GodModeAuditLog
from admin.god import GodModeContext

__all__ = [
    "AdminGodLayer",
    "GodModeAuditLog",
    "GodModeContext",
]

# Admin package metadata
__admin_version__ = "2.0.0"


def get_admin_capabilities() -> list[str]:
    """List all admin capabilities available in this package."""
    return [
        "god_mode_session",
        "role_based_access_control",
        "constitutional_enforcement",
        "immutable_audit_logging",
        "prompt_constraint_injection",
        "admin_auth_verification",
    ]
