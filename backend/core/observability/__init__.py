"""Observability package — standardized logging, tracing & error-bus telemetry.

বাংলা: কেন্দ্রীভূত observability — OpenTelemetry tracing এবং Error Bus-এর
telemetry integration (Phase 3 / M3.3)।
"""

from core.observability.telemetry import (
    get_tracer,
    setup_tracing,
    trace_span,
)
from core.observability.telemetry_events import (
    attach_error_bus_telemetry,
    init_observability_telemetry,
    record_error_telemetry,
)

__all__ = [
    "get_tracer",
    "setup_tracing",
    "trace_span",
    "attach_error_bus_telemetry",
    "init_observability_telemetry",
    "record_error_telemetry",
]
