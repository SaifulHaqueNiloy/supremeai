import ipaddress
import logging
import socket
from urllib.parse import urlparse

from core.config import settings

logger = logging.getLogger(__name__)


class MCPSecurityGuard:
    """
    Enforces security policies for MCP Server connections (SSRF prevention).
    - Prevents connecting to localhost / loopback addresses
    - Prevents connecting to private IP ranges (10.x, 192.168.x, 172.16.x)
    - Enforces HTTPS for external connections in production
    """

    @staticmethod
    def is_safe_url(url: str, enforce_https: bool = True) -> bool:
        try:
            parsed = urlparse(url)

            # Enforce scheme
            if enforce_https and parsed.scheme != "https":
                logger.warning(f"MCP Security: Denied non-HTTPS URL {url}")
                return False

            if parsed.scheme not in ("http", "https"):
                logger.warning(f"MCP Security: Denied invalid scheme {parsed.scheme}")
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            # Resolve IP
            try:
                ip_address = socket.gethostbyname(hostname)
            except socket.gaierror:
                logger.warning(f"MCP Security: Could not resolve hostname {hostname}")
                return False

            # Check for private/loopback IPs
            ip = ipaddress.ip_address(ip_address)

            if ip.is_loopback and settings.env == "local":
                # Allow loopback in local environment
                pass
            elif ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_multicast:
                logger.warning(
                    f"MCP Security: Denied connection to private/reserved IP {ip} for {hostname}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"MCP Security: Error validating URL {url}: {e}")
            return False
