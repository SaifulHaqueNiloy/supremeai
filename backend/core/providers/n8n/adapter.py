import hashlib
import hmac
import json
import time
from typing import Optional

import httpx
from loguru import logger

from ...automation.interfaces import AutomationProvider
from ...automation.models import AutomationEvent, AutomationResult, AutomationStatus
from ...automation.registry import get_workflow_route
from ...config import settings


class N8nAutomationAdapter(AutomationProvider):
    """
    Adapter for routing background events to an external n8n instance.
    Implements the Vendor-Independent AutomationProvider protocol.
    """

    def __init__(self):
        self.base_url = settings.n8n_base_url.rstrip("/")
        self.timeout = settings.n8n_timeout_seconds
        self.secret = (
            settings.n8n_webhook_secret.get_secret_value() if settings.n8n_webhook_secret else ""
        )
        self.verify_tls = settings.n8n_verify_tls

    def _generate_signature(self, payload_str: str, timestamp: str) -> str:
        """
        Generate an HMAC SHA-256 signature for the payload to prevent spoofing.
        """
        if not self.secret:
            return ""

        message = f"{timestamp}.{payload_str}".encode()
        signature = hmac.new(self.secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
        return signature

    async def dispatch(self, event: AutomationEvent) -> AutomationResult:
        """
        Send the event to n8n if enabled.
        """
        if not settings.n8n_enabled or not settings.n8n_event_delivery_enabled:
            return AutomationResult(
                status=AutomationStatus.SKIPPED,
                provider="n8n",
                message="n8n delivery is globally disabled via settings.",
            )

        if not self.base_url:
            return AutomationResult(
                status=AutomationStatus.FAILED,
                provider="n8n",
                message="N8N_BASE_URL is not configured.",
            )

        try:
            route = get_workflow_route(event.workflow_key)
        except ValueError as e:
            return AutomationResult(status=AutomationStatus.FAILED, provider="n8n", message=str(e))

        target_url = f"{self.base_url}{route}"

        # Prepare signed payload
        payload_dict = {
            "workflow_key": event.workflow_key,
            "payload": event.payload,
            "metadata": event.metadata,
        }
        payload_str = json.dumps(payload_dict, separators=(",", ":"))
        timestamp = str(int(time.time()))

        headers = {
            "Content-Type": "application/json",
            "X-SupremeAI-Timestamp": timestamp,
        }

        signature = self._generate_signature(payload_str, timestamp)
        if signature:
            headers["X-SupremeAI-Signature"] = signature

        try:
            async with httpx.AsyncClient(verify=self.verify_tls) as client:
                response = await client.post(
                    target_url, content=payload_str, headers=headers, timeout=self.timeout
                )

                response.raise_for_status()

                return AutomationResult(
                    status=AutomationStatus.DELIVERED,
                    provider="n8n",
                    message=f"Event delivered to {route}",
                    execution_id=response.headers.get("X-N8N-Execution-Id"),
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"n8n webhook returned HTTP {e.response.status_code}: {e.response.text}")
            return AutomationResult(
                status=AutomationStatus.FAILED,
                provider="n8n",
                message=f"HTTP {e.response.status_code} Error: {e.response.text}",
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to n8n webhook: {e}")
            return AutomationResult(
                status=AutomationStatus.FAILED, provider="n8n", message=f"Network Error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error dispatching to n8n: {e}")
            return AutomationResult(
                status=AutomationStatus.FAILED, provider="n8n", message=f"Internal Error: {str(e)}"
            )
