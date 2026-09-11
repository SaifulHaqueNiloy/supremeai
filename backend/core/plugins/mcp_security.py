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
            if not hostname or parsed.username or parsed.password:
                return False
            if parsed.port is not None and parsed.port not in {80, 443}:
                logger.warning("MCP Security: Denied non-standard port for %s", hostname)
                return False

            # Resolve every address so DNS rebinding cannot hide a private target.
            try:
                addresses = socket.getaddrinfo(hostname, parsed.port or 443, type=socket.SOCK_STREAM)
            except socket.gaierror:
                logger.warning("MCP Security: Could not resolve hostname %s", hostname)
                return False

            for address in {item[4][0] for item in addresses}:
                ip = ipaddress.ip_address(address)
                if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_multicast or ip.is_link_local:
                    if not (settings.env == "local" and ip.is_loopback):
                        logger.warning("MCP Security: Denied private/reserved IP for %s", hostname)
                        return False

            return True


        except Exception as e:
            logger.error(f"MCP Security: Error validating URL {url}: {e}")
            return False
