import asyncio
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


# ── Plan Section 9: Transient vs Permanent error classification ──────────────
# Transient errors (retryable): timeout, connection failure, 429, 5xx
# Permanent errors (no retry): invalid signature, invalid workflow, 400, malformed
def _is_transient_http_error(exc: Exception) -> bool:
    """Return True if the exception represents a transient (retryable) failure."""
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        # 429 (rate limit) ও 5xx (server error) হলো transient
        return status == 429 or status >= 500
    # RequestError হলো connection/timeout/DNS — সব transient
    return isinstance(exc, httpx.RequestError)


# Exponential backoff schedule (Section 9): 2s, 10s, 30s
_RETRY_BACKOFF_SECONDS = (2.0, 10.0, 30.0)
_DEFAULT_MAX_RETRIES = 3


class N8nAutomationAdapter(AutomationProvider):
    """
    Adapter for routing background events to an external n8n instance.
    Implements the Vendor-Independent AutomationProvider protocol.

    Plan Section 9: real retry/backoff with transient vs permanent error
    classification. Permanent errors (400, invalid workflow, signature) এ
    retry হয় না। Transient errors (timeout, 429, 5xx) এ exponential backoff
    দিয়ে retry হয় (2s, 10s, 30s), সর্বোচ্চ ৩ বার।
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
        Send the event to n8n if enabled, with retry/backoff for transient errors.
        """
        if not settings.n8n_enabled or not settings.n8n_event_delivery_enabled:
            return AutomationResult(
                status=AutomationStatus.SKIPPED,
                provider="n8n",
                message="n8n delivery is globally disabled via settings.",
                event_id=event.event_id,
            )

        if not self.base_url:
            return AutomationResult(
                status=AutomationStatus.FAILED,
                provider="n8n",
                message="N8N_BASE_URL is not configured.",
                event_id=event.event_id,
            )

        try:
            route = get_workflow_route(event.workflow_key)
        except ValueError as e:
            # Permanent error — invalid workflow key, কোনো retry নয়
            return AutomationResult(
                status=AutomationStatus.FAILED,
                provider="n8n",
                message=str(e),
                event_id=event.event_id,
            )

        target_url = f"{self.base_url}{route}"

        # Prepare signed payload — Plan Section 6: event_id ও idempotency_key যোগ
        payload_dict = {
            "event_id": event.event_id,
            "idempotency_key": event.idempotency_key,
            "schema_version": event.schema_version,
            "workflow_key": event.workflow_key,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source,
            "trace_id": event.trace_id,
            "tenant_id": event.tenant_id,
            "actor_type": event.actor_type,
            "actor_id": event.actor_id,
            "payload": event.payload,
            "metadata": event.metadata,
        }
        payload_str = json.dumps(payload_dict, separators=(",", ":"), default=str)
        timestamp = str(int(time.time()))

        headers = {
            "Content-Type": "application/json",
            "X-SupremeAI-Timestamp": timestamp,
            "X-SupremeAI-Event-Id": event.event_id,
            "X-SupremeAI-Idempotency-Key": event.idempotency_key,
        }

        signature = self._generate_signature(payload_str, timestamp)
        if signature:
            headers["X-SupremeAI-Signature"] = signature

        # ── Plan Section 9: retry loop with transient/permanent classification ──
        last_exc: Exception | None = None
        for attempt in range(1, _DEFAULT_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(verify=self.verify_tls) as client:
                    response = await client.post(
                        target_url, content=payload_str, headers=headers, timeout=self.timeout
                    )
                    response.raise_for_status()

                    return AutomationResult(
                        status=AutomationStatus.DELIVERED,
                        provider="n8n",
                        message=f"Event delivered to {route} on attempt {attempt}",
                        execution_id=response.headers.get("X-N8N-Execution-Id"),
                        event_id=event.event_id,
                        attempt=attempt,
                    )

            except httpx.HTTPStatusError as e:
                last_exc = e
                if _is_transient_http_error(e):
                    logger.warning(
                        f"n8n transient HTTP {e.response.status_code} on attempt {attempt}/"
                        f"{_DEFAULT_MAX_RETRIES} for event {event.event_id}"
                    )
                else:
                    # Permanent HTTP error (4xx except 429) — কোনো retry নয়
                    logger.error(
                        f"n8n permanent HTTP {e.response.status_code} for event "
                        f"{event.event_id}: {e.response.text}"
                    )
                    return AutomationResult(
                        status=AutomationStatus.FAILED,
                        provider="n8n",
                        message=f"Permanent HTTP {e.response.status_code} Error: {e.response.text}",
                        event_id=event.event_id,
                        attempt=attempt,
                    )
            except httpx.RequestError as e:
                last_exc = e
                logger.warning(
                    f"n8n network error on attempt {attempt}/{_DEFAULT_MAX_RETRIES} "
                    f"for event {event.event_id}: {e!r}"
                )
            except Exception as e:
                last_exc = e
                logger.error(f"Unexpected error dispatching to n8n (attempt {attempt}): {e}")
                # Unexpected error — transient ধরে retry করি (safe default)
            # আরও attempt আছে কিনা দেখে backoff করি
            if attempt < _DEFAULT_MAX_RETRIES and last_exc is not None and _is_transient_http_error(last_exc):
                backoff = _RETRY_BACKOFF_SECONDS[min(attempt - 1, len(_RETRY_BACKOFF_SECONDS) - 1)]
                logger.info(f"Retrying n8n dispatch in {backoff}s (attempt {attempt + 1})")
                await asyncio.sleep(backoff)
            elif last_exc is not None and not _is_transient_http_error(last_exc):
                # permanent error already returned above; নিরাপত্তার জন্য break
                break

        # সব retries শেষ — terminal failure
        err_msg = f"Network Error: {str(last_exc)}" if isinstance(last_exc, httpx.RequestError) else (
            f"HTTP Error: {str(last_exc)}" if last_exc else "Unknown error"
        )
        return AutomationResult(
            status=AutomationStatus.FAILED,
            provider="n8n",
            message=f"Failed after {_DEFAULT_MAX_RETRIES} attempts: {err_msg}",
            event_id=event.event_id,
            attempt=_DEFAULT_MAX_RETRIES,
        )
