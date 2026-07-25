# বাংলা মন্তব্য: core.telemetry মডিউল — observability.telemetry থেকে সব symbol re-export করা হয়েছে
# যাতে tests `core.telemetry.BatchSpanProcessor`, `core.telemetry.otel_trace` ইত্যাদি patch করতে পারে।
from opentelemetry import trace as otel_trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from core.observability.telemetry import (
    _NoOpSpan,
    _RealSpan,
    get_tracer,
    setup_tracing,
    trace_span,
)

__all__ = [
    "otel_trace",
    "TracerProvider",
    "BatchSpanProcessor",
    "get_tracer",
    "setup_tracing",
    "trace_span",
    "_NoOpSpan",
    "_RealSpan",
]
