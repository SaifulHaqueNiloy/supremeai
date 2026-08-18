"""Error-bus ↔ OpenTelemetry integration (Phase 3 / M3.3).

বাংলা: Error Bus-এর সব ErrorEvent-কে OpenTelemetry span-এ রূপান্তর করে, যাতে
observability dashboard-এ trace + error একসাথে দেখা যায় ("error bus full telemetry events")।
Zero silent failure — span record ফেইল হলেও error log থেমে থাকবে না।

Design notes:
- Tracing setup lives in `core.observability.telemetry` (setup_tracing / get_tracer).
- This module only WIRING: it turns every emitted ErrorEvent into a telemetry span
  via a registered error-bus listener (`_error_bus_sink`).
- ভারী dependency (core.messaging.event_bus) শুধুমাত্র function-এর ভেতরে import করা হয়,
  যাতে module import-এ কোনো heavy side-effect না ঘটে।
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from core.observability.telemetry import get_tracer, setup_tracing


class _TelemetryError(RuntimeError):
    """Lightweight exception carrier so spans can record_error_type context."""


_attached = False


def _build_context(event: Any) -> dict[str, Any]:
    """Extract a correlation context dict from an ErrorEvent-like object."""
    ctx: dict[str, Any] = {
        "trace_id": None,
        "span_id": None,
        "correlation_id": getattr(event, "correlation_id", None),
    }
    sc = getattr(event, "structured_context", None)
    if sc is not None:
        ctx["correlation_id"] = (
            ctx.get("correlation_id")
            or getattr(sc, "request_id", None)
            or getattr(sc, "task_id", None)
        )
    return ctx


def record_error_telemetry(event: Any, attributes: dict[str, Any] | None = None) -> dict[str, Any]:
    """Record a telemetry span for a single ErrorEvent.

    Returns the span context (trace_id/span_id) so callers can correlate the
    error with a trace. Safe no-op (still returns a context dict) when tracing
    has not been initialized.

    Args:
        event: An object exposing `error_type`, `module`, `severity`, `service`
            and optionally `structured_context` (i.e. core.messaging.event_bus.ErrorEvent).
        attributes: Optional extra span attributes.
    """
    from opentelemetry.trace import Status, StatusCode

    tracer = get_tracer()
    ctx = _build_context(event)
    if tracer is None:
        logger.debug(
            f"[telemetry] no tracer active — skipping span for "
            f"{getattr(event, 'error_type', '?')}"
        )
        return ctx

    span_name = f"error_bus.event:{getattr(event, 'error_type', 'UNKNOWN_ERROR')}"
    try:
        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("error.module", str(getattr(event, "module", "unknown")))
            span.set_attribute("error.type", str(getattr(event, "error_type", "UNKNOWN_ERROR")))
            span.set_attribute("error.severity", str(getattr(event, "severity", "ERROR")))
            span.set_attribute("error.service", str(getattr(event, "service", "backend")))
            sc = getattr(event, "structured_context", None)
            if sc is not None:
                span.set_attribute("error.user_id", str(getattr(sc, "user_id", "") or ""))
                span.set_attribute("error.task_id", str(getattr(sc, "task_id", "") or ""))
                span.set_attribute("error.request_id", str(getattr(sc, "request_id", "") or ""))
            if attributes:
                for k, v in attributes.items():
                    try:
                        span.set_attribute(k, v)
                    except Exception:
                        # Non-serializable attribute — skip, never break the span.
                        pass
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(
                _TelemetryError(
                    f"{getattr(event, 'error_type', 'UNKNOWN_ERROR')}: "
                    f"{getattr(event, 'message', '')}"
                )
            )
            # বাংলা: non-recording span (বা mocked SDK) trace_id int নাও হতে পারে —
            # তখন format() crash করবে না, শুধু None রাখবে।
            try:
                span_ctx = span.get_span_context()
                if isinstance(getattr(span_ctx, "trace_id", None), int):
                    ctx["trace_id"] = format(span_ctx.trace_id, "032x")
                if isinstance(getattr(span_ctx, "span_id", None), int):
                    ctx["span_id"] = format(span_ctx.span_id, "016x")
            except Exception:
                pass
            # Optional: stitch trace id back onto the event for downstream correlation.
            try:
                event_context = getattr(event, "context", None)
                if isinstance(event_context, dict):
                    event_context["telemetry_trace_id"] = ctx["trace_id"]
            except Exception:
                pass
    except Exception as exc:  # Never let telemetry crash the caller path.
        logger.warning(f"[telemetry] record_error_telemetry failed: {exc}")
    return ctx


def _error_bus_sink(event: Any) -> None:
    """ErrorEventBus listener — emits a telemetry span for every error event.

    Registered against "*" so ALL error types are captured ("full telemetry events").
    """
    try:
        record_error_telemetry(event)
    except Exception as exc:  # Sink must never break the error bus dispatch.
        logger.warning(f"[telemetry] error-bus sink failed: {exc}")


def attach_error_bus_telemetry() -> bool:
    """Register the telemetry sink on the central error bus (idempotent).

    Returns True if a NEW listener was attached, False if already attached.
    """
    global _attached
    if _attached:
        return False
    try:
        from core.messaging.event_bus import error_event_bus

        error_event_bus.register_listener("*", _error_bus_sink)
        _attached = True
        logger.info("[telemetry] Error-bus -> OpenTelemetry telemetry sink attached.")
        return True
    except Exception as exc:
        logger.warning(f"[telemetry] could not attach error-bus sink: {exc}")
        return False


def init_observability_telemetry(
    service_name: str = "supremeai",
    otlp_endpoint: str | None = None,
    attach_error_bus: bool = True,
) -> None:
    """Idempotent observability bootstrap for Phase 3.

    1. Sets up OpenTelemetry tracing (no-op exporter when no OTLP endpoint).
    2. Attaches the error-bus telemetry sink so every error becomes a span.
    """
    setup_tracing(service_name=service_name, otlp_endpoint=otlp_endpoint)
    if attach_error_bus:
        attach_error_bus_telemetry()


__all__ = [
    "record_error_telemetry",
    "attach_error_bus_telemetry",
    "init_observability_telemetry",
]
