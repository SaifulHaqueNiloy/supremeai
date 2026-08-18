"""Unit tests for Phase 3 / M3.3 error-bus ↔ OpenTelemetry integration.

বাংলা: telemetry_events মডিউলের record/attach/sink লজিক টেস্ট করে।
Heavy dependency (core.messaging.event_bus) avoid করা হয়েছে — attach-এর
জন্য fake bus module sys.modules-এ দেওয়া হয়েছে।
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from unittest.mock import MagicMock

from core.observability import telemetry_events
from core.observability.telemetry import setup_tracing


class FakeSpan:
    """Minimal stand-in for an OpenTelemetry Span (SDK-independent)."""

    def __init__(self) -> None:
        self._ctx = MagicMock()
        self._ctx.trace_id = 0xABCDEF0123456789ABCDEF0123456789
        self._ctx.span_id = 0x1122334455667788

    def set_attribute(self, *args, **kwargs) -> None:
        pass

    def set_status(self, *args, **kwargs) -> None:
        pass

    def record_exception(self, *args, **kwargs) -> None:
        pass

    def get_span_context(self):
        return self._ctx


class FakeTracer:
    """Minimal stand-in for an OpenTelemetry Tracer."""

    @contextmanager
    def start_as_current_span(self, name, kind=None):  # noqa: ANN001
        yield FakeSpan()


class FakeEvent:
    def __init__(
        self,
        error_type: str = "TEST_ERROR",
        module: str = "telemetry_test",
        severity: str = "ERROR",
        service: str = "backend",
        message: str = "boom",
    ) -> None:
        self.error_type = error_type
        self.module = module
        self.severity = severity
        self.service = service
        self.message = message
        self.context: dict = {}
        self.structured_context = None


def test_setup_tracing_idempotent_no_warning():
    # Calling twice must not raise (OTel "overriding provider" warning is guarded).
    setup_tracing(service_name="test-svc")
    setup_tracing(service_name="test-svc")


def test_record_error_telemetry_returns_context(monkeypatch):
    monkeypatch.setattr(telemetry_events, "get_tracer", lambda: FakeTracer())
    ctx = telemetry_events.record_error_telemetry(FakeEvent())
    assert isinstance(ctx, dict)
    assert ctx["trace_id"] is not None
    assert ctx["span_id"] is not None
    assert len(ctx["trace_id"]) == 32
    assert len(ctx["span_id"]) == 16


def test_record_error_telemetry_no_tracer(monkeypatch):
    monkeypatch.setattr(telemetry_events, "get_tracer", lambda: None)
    ctx = telemetry_events.record_error_telemetry(FakeEvent())
    assert ctx["trace_id"] is None
    assert ctx["span_id"] is None


def test_record_error_telemetry_stitches_trace_id_onto_event(monkeypatch):
    monkeypatch.setattr(telemetry_events, "get_tracer", lambda: FakeTracer())
    evt = FakeEvent()
    telemetry_events.record_error_telemetry(evt)
    assert evt.context.get("telemetry_trace_id") is not None


def test_attach_error_bus_telemetry_idempotent(monkeypatch):
    # Provide a fake event bus module to avoid the heavy import chain.
    fake_bus = MagicMock()
    fake_mod = MagicMock()
    fake_mod.error_event_bus = fake_bus
    monkeypatch.setitem(sys.modules, "core.messaging.event_bus", fake_mod)

    # Reset module-level flag for a deterministic test.
    telemetry_events._attached = False
    first = telemetry_events.attach_error_bus_telemetry()
    second = telemetry_events.attach_error_bus_telemetry()
    assert first is True
    assert second is False
    assert fake_bus.register_listener.call_count == 1
    args, _ = fake_bus.register_listener.call_args
    assert args[0] == "*"
    telemetry_events._attached = False


def test_error_bus_sink_swallows_errors(monkeypatch):
    def boom(event):
        raise RuntimeError("telemetry down")

    monkeypatch.setattr(telemetry_events, "record_error_telemetry", boom)
    # Must never raise — a broken sink must not crash the error bus dispatch.
    telemetry_events._error_bus_sink(FakeEvent())
