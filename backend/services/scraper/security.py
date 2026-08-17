"""
Minimal SSRF protection for the standalone scraper service.
Self-contained — does NOT import from backend/core/security to avoid
pulling in DB/Redis/asyncpg dependencies.
"""

from ipaddress import ip_address
from urllib.parse import urlparse

_BLOCKED_SCHEMES = {"file", "ftp", "gopher", "dict", "ldap", "javascript", "data"}
_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
_PRIVATE_PREFIXES = ("10.", "172.16.", "192.168.", "169.254.", "100.64.", "fc", "fe80:")


def _is_private_ip(hostname: str) -> bool:
    try:
        ip = ip_address(hostname)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def is_safe_url(url: str) -> bool:
    """Validate URL to prevent SSRF attacks in the standalone scraper service."""
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"} or scheme in _BLOCKED_SCHEMES:
            return False

        hostname = parsed.hostname or ""
        if not hostname:
            return False

        if hostname.lower() in _BLOCKED_HOSTS:
            return False

        if _is_private_ip(hostname):
            return False

        for prefix in _PRIVATE_PREFIXES:
            if hostname.lower().startswith(prefix):
                return False

        return True
    except Exception:
        return False
