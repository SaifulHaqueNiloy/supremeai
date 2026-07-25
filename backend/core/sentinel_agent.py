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

    def __init__(self):
        self.running = True
        # Track if single worker lock is engaged
        self._is_active = False

    def _validate_endpoint_url(self, url: str) -> bool:
        """Validate URL to prevent SSRF attacks - blocks metadata IPs and disallowed schemes."""
        import re
        from urllib.parse import urlparse

        from core.config import settings

        try:
            parsed = urlparse(url)
            # Block dangerous schemes
            if parsed.scheme in {"file", "gopher", "ftp", "sftp"}:
                return False
            # Block cloud metadata IPs (AWS, GCP, Azure)
            hostname = parsed.hostname or ""
            if re.match(
                r"^(169\.254\.169\.|10\.\d+\.|172\.(1[6-9]|2[0-9]|3[01])\.)", hostname
            ):
                return False
            # Block localhost access in production unless it targets the backend port 8080
            # বাংলা মন্তব্য: প্রোডাকশনে লোকালহোস্ট ব্লক করা হচ্ছে, কিন্তু আমাদের নিজস্ব ব্যাকএন্ড পোর্ট ৮০৮০ মনিটর করার জন্য পোলিং এলাও করা হলো।
            if settings.env in {"production", "staging"}:
                if "localhost" in hostname or "127.0.0.1" in hostname:
                    if parsed.port != 8080:
                        return False
            return True
        except Exception:
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

                            # SSRF protection
                            if not self._validate_endpoint_url(url):
                                logger.critical(
                                    f"SSRF Blocked: Attempted access to {url}"
                                )
                                continue

                            # Make the request only after SSRF validation
                            resp = await client.request(ep.method, url)
                            latency = (
                                datetime.now(UTC) - start_time
                            ).total_seconds() * 1000

                            ep.latency_ms = int(latency)
                            ep.last_check_at = datetime.now(UTC)

                            if resp.status_code != ep.expected_status:
                                ep.last_ping_status = "down"
                                if ep.is_critical:
                                    # Create Incident
                                    incident = SystemIncident(
                                        incident_type="api_endpoint_failure",
                                        severity="critical",
                                        remediation_log=f"Endpoint {ep.path} returned {resp.status_code} instead of {ep.expected_status}.",
                                    )
                                    session.add(incident)
                            else:
                                ep.last_ping_status = "up"

                        except Exception as e:  # noqa: BLE001
                            ep.last_ping_status = "down"
                            ep.last_check_at = datetime.now(UTC)
                            incident = SystemIncident(
                                incident_type="api_endpoint_unreachable",
                                severity="critical" if ep.is_critical else "warning",
                                remediation_log=f"Exception connecting to {ep.path}: {str(e)}",
                            )
                            session.add(incident)

                await session.commit()
        except Exception as e:  # noqa: BLE001
            logger.error(f"[SentinelAgent] Error during monitor_endpoints: {e}")

    async def audit_dependencies(self):
        """
        Runs heavy auditing logic (e.g., pip-audit / pip list --outdated)
        and updates SystemDependency status dynamically.

        বাংলা মন্তব্য: আগে এখানে শুধু ডামি রিলেশন টাচ করে টাইমস্ট্যাম্প আপডেট করা হতো।
        এখন এটি pip-audit/pip command রান করে অরফ্যানড বা আউটডেটেড প্যাকেজ সনাক্ত করে
        সিস্টেমের ডিপেনডেন্সি ডাটাবেস আপডেট করে।
        """
        import asyncio
        import json

        logger.info(
            "[SentinelAgent] Running dependency audit via system environment tools..."
        )

        # Check if pip-audit is available, fallback to pip list --outdated
        audit_cmd = None
        if shutil.which("pip-audit"):
            audit_cmd = ["pip-audit", "--format=json"]
        elif shutil.which("pip"):
            audit_cmd = ["pip", "list", "--outdated", "--format=json"]

        vulnerabilities = []
        if audit_cmd:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *audit_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                if proc.returncode in (0, 1) and stdout:
                    vulnerabilities = json.loads(stdout.decode("utf-8"))
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[SentinelAgent] Failed executing audit process: {e}")

        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(SystemDependency))
                deps = result.scalars().all()
                for dep in deps:
                    dep.last_audit_at = datetime.now(UTC)
                    # Check if package is flagged as vulnerable in scan report
                    # Depending on command output structure (dict or list)
                    is_vuln = False
                    if isinstance(vulnerabilities, list):
                        is_vuln = any(
                            v.get("name", "").lower() == dep.package_name.lower()
                            for v in vulnerabilities
                        )
                    elif isinstance(vulnerabilities, dict):
                        is_vuln = dep.package_name in vulnerabilities.get(
                            "dependencies", {}
                        )

                    if is_vuln:
                        dep.status = "vulnerable"
                        # Trigger immediate remediation alert
                        logger.error(
                            f"[SentinelAgent] Flagged security risk: package {dep.package_name} is vulnerable!"
                        )
                        await self.trigger_event(
                            "SECURITY_RISK",
                            f"Dependency {dep.package_name} failed security scan.",
                        )
                    else:
                        dep.status = "secure"
                await session.commit()
        except Exception as e:  # noqa: BLE001
            logger.error(f"[SentinelAgent] Error during audit_dependencies: {e}")

    async def trigger_event(self, event_type: str, details: str):
        """
        Event-driven hook for middleware to immediately trigger an incident review.
        """
        try:
            async with AsyncSessionLocal() as session:
                incident = SystemIncident(
                    incident_type=event_type,
                    severity="warning",
                    remediation_log=details,
                )
                session.add(incident)
                await session.commit()
                logger.info(
                    f"[SentinelAgent] Event-driven incident recorded: {event_type}"
                )
        except Exception as e:  # noqa: BLE001
            logger.error(f"[SentinelAgent] Error triggering event: {e}")

    async def run_periodic_loop(self):
        """
        The main async loop to be attached to FastAPI lifespan.
        Uses a basic active flag to prevent multiple executions if workers > 1.
        """
        if self._is_active:
            logger.warning(
                "[SentinelAgent] Agent already active, skipping duplicate startup."
            )
            return

        self._is_active = True
        logger.info(
            "[SentinelAgent] Starting Periodic Loop (Heartbeat: 60s, Audit: 12h)..."
        )

        audit_counter = 0

        try:
            while self.running:
                # 1. Quick Heartbeat (60 seconds)
                await self.monitor_endpoints()

                # 2. Long Audit (Every 12 hours) - 12h = 720 minutes = 720 iterations of 60s
                if audit_counter >= 720:
                    await self.audit_dependencies()
                    audit_counter = 0

                audit_counter += 1
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            logger.info(
                "[SentinelAgent] Periodic Loop cancelled. Shutting down gracefully."
            )
            self._is_active = False
            raise


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
