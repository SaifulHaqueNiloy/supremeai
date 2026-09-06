"""
SSRF Protection facade / compatibility shim.
Redirects to `core.security.protection.ssrf_protection`.
"""

from core.security.protection.ssrf_protection import (
    SSRFProtection,
    SSRFValidationResult,
    get_ssrf_protection,
    is_safe_url,
    reset_ssrf_protection,
)

__all__ = [
    "SSRFProtection",
    "SSRFValidationResult",
    "get_ssrf_protection",
    "is_safe_url",
    "reset_ssrf_protection",
]
