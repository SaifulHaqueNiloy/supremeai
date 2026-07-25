import re
from urllib.parse import urlparse
from typing import Any
import httpx
from loguru import logger
from core.config import settings


def _validate_endpoint_url(url: str) -> bool:
    """
    Validate endpoint URL to prevent SSRF attacks.

    Args:
        url: URL to validate

    Returns:
        bool: True if URL is safe, False otherwise
    """
    try:
        parsed = urlparse(url)

        # Block dangerous schemes
        if parsed.scheme in {"file", "gopher", "ftp", "tftp", "ldap", "ldaps", "sftp", "jar"}:
            return False

        # Block dangerous host patterns
        hostname = parsed.hostname or ""

        # Block metadata service IPs
        if re.match(r"^(169\.254\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)", hostname):
            return False

        # Block localhost variations in production
        if settings.env in {"production", "staging"}:
            if hostname in {"localhost", "127.0.0.1", "::1", "[::1]"}:
                return False
            # Only allow approved hosts in production
            allowed_hosts = getattr(settings, "allowed_external_hosts", set())
            if hostname not in allowed_hosts and not hostname.endswith(".supremeai.internal"):
                return False

        return True
    except Exception:
        return False


async def execute_endpoint_request(endpoint_config: dict[str, Any]) -> dict[str, Any] | None:
    """
    Execute an endpoint request with SSRF protection.

    Args:
        endpoint_config: Configuration containing path, method, etc.

    Returns:
        Response data or None if request failed
    """
    try:
        # Construct URL with validation
        path = endpoint_config.get("path", "")
        method = endpoint_config.get("method", "GET").upper()

        if path.startswith("http"):
            url = path
        else:
            # Validate path to ensure it's a safe relative path
            if ".." in path or path.startswith("/") or ":" in path.split("/")[0]:
                logger.warning(f"Potentially unsafe path blocked: {path}")
                return None
            url = f"http://127.0.0.1:8080{path}"

        # Validate URL for SSRF protection
        if not _validate_endpoint_url(url):
            logger.critical(f"SSRF blocked: Attempted access to {url}")
            return None

        timeout = endpoint_config.get("timeout", 30)

        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            response = await client.request(method, url, headers=endpoint_config.get("headers", {}), json=endpoint_config.get("json", None))

            return {"status_code": response.status_code, "headers": dict(response.headers), "content": response.text}

    except httpx.RequestError as e:
        logger.error(f"Request error in endpoint execution: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in endpoint execution: {e}")
        return None
