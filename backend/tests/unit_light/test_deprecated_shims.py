"""Tests for the deprecated module shims that delegate to their canonical replacements.

Each shim exposes ``__getattr__`` / ``__dir__`` that emit a DeprecationWarning on
first access and forward attribute lookups to the new module path.
"""

import importlib
import types
from unittest.mock import patch

import pytest


def _make_fake_module(attrs):
    fake = types.ModuleType("fake_target")
    fake.__dict__.update(attrs)
    return fake


# --- core.cloud_storage -> services.storage.cloud_storage -------------------
def test_cloud_storage_delegates_attribute():
    import core.cloud_storage

    fake = _make_fake_module({"SomeExport": 123})
    with patch("importlib.import_module", return_value=fake):
        assert core.cloud_storage.SomeExport == 123


def test_cloud_storage_dir_lists_target():
    import core.cloud_storage

    fake = _make_fake_module({"A": 1, "B": 2})
    with patch("importlib.import_module", return_value=fake):
        assert "A" in dir(core.cloud_storage)


def test_cloud_storage_warns_once():
    import core.cloud_storage

    importlib.reload(core.cloud_storage)
    fake = _make_fake_module({"X": 1})
    with patch("importlib.import_module", return_value=fake), pytest.warns(DeprecationWarning):
        _ = core.cloud_storage.X


# --- core.email_service -> services.email.email_service --------------------
def test_email_service_delegates_attribute():
    import core.email_service

    fake = _make_fake_module({"send_email": lambda: "sent"})
    with patch("importlib.import_module", return_value=fake):
        assert core.email_service.send_email() == "sent"


def test_email_service_warns_once():
    import core.email_service

    importlib.reload(core.email_service)
    fake = _make_fake_module({"Y": 1})
    with patch("importlib.import_module", return_value=fake), pytest.warns(DeprecationWarning):
        _ = core.email_service.Y


# --- core.error_bus -> core.errors.error_bus -------------------------------
def test_error_bus_delegates_attribute():
    import core.error_bus

    fake = _make_fake_module({"publish": 42})
    with patch("importlib.import_module", return_value=fake):
        assert core.error_bus.publish == 42


def test_error_bus_warns_once():
    import core.error_bus

    importlib.reload(core.error_bus)
    fake = _make_fake_module({"Z": 1})
    with patch("importlib.import_module", return_value=fake), pytest.warns(DeprecationWarning):
        _ = core.error_bus.Z


# --- core.log_batcher -> monitoring.log_batcher ----------------------------
def test_log_batcher_delegates_attribute():
    import core.log_batcher

    fake = _make_fake_module({"flush": "ok"})
    with patch("importlib.import_module", return_value=fake):
        assert core.log_batcher.flush == "ok"


def test_log_batcher_warns_once():
    import core.log_batcher

    importlib.reload(core.log_batcher)
    fake = _make_fake_module({"W": 1})
    with patch("importlib.import_module", return_value=fake), pytest.warns(DeprecationWarning):
        _ = core.log_batcher.W
