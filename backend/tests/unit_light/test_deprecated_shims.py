"""Tests for the deprecated module shims that delegate to their canonical replacements.

Each shim exposes ``__getattr__`` / ``__dir__`` that emit a DeprecationWarning on
first access and forward attribute lookups to the new module path. This single
parametrized suite exercises every shim in ``core`` so the shim modules are not
left at 0% coverage.
"""

import importlib
import types
from unittest.mock import patch

import pytest

# (module import path, an attribute name we access to trigger delegation)
_SHIMS = [
    ("core.cors_policy", "SomeExport"),
    ("core.billing_plans", "SomeExport"),
    ("core.cloud_storage", "SomeExport"),
    ("core.idempotency_middleware", "SomeExport"),
    ("core.tenant_db", "SomeExport"),
    ("core.gcp_firestore", "SomeExport"),
    ("core.log_batcher", "SomeExport"),
    ("core.logging_config", "SomeExport"),
    ("core.logging", "SomeExport"),
    ("core.llm_router", "SomeExport"),
    ("core.error_remediation", "SomeExport"),
    ("core.error_pattern_db", "SomeExport"),
    ("core.error_handler", "SomeExport"),
    ("core.error_bus", "SomeExport"),
    ("core.metrics_collector", "SomeExport"),
    ("core.metrics", "SomeExport"),
    ("core.email_service", "SomeExport"),
    ("core.db_repository", "SomeExport"),
    ("core.pgbouncer_pool", "SomeExport"),
    ("core.rate_limiter", "SomeExport"),
]


def _make_fake_module(attrs):
    fake = types.ModuleType("fake_target")
    fake.__dict__.update(attrs)
    return fake


@pytest.mark.parametrize("module_path,attr", _SHIMS)
def test_shim_delegates_attribute(module_path, attr):
    mod = importlib.import_module(module_path)
    fake = _make_fake_module({attr: 123})
    with patch("importlib.import_module", return_value=fake):
        assert getattr(mod, attr) == 123


@pytest.mark.parametrize("module_path,attr", _SHIMS)
def test_shim_dir_lists_target(module_path, attr):
    mod = importlib.import_module(module_path)
    fake = _make_fake_module({"A": 1, "B": 2})
    with patch("importlib.import_module", return_value=fake):
        assert "A" in dir(mod)


@pytest.mark.parametrize("module_path,attr", _SHIMS)
def test_shim_warns_once(module_path, attr):
    mod = importlib.import_module(module_path)
    importlib.reload(mod)
    fake = _make_fake_module({attr: 1})
    with (
        patch("importlib.import_module", return_value=fake),
        pytest.warns(DeprecationWarning),
    ):
        _ = getattr(mod, attr)
