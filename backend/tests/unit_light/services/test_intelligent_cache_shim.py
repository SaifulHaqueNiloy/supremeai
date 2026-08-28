import importlib
import types
from unittest.mock import patch

import pytest

import services.intelligent_cache as ic_module


def _make_fake_module(attrs):
    fake = types.ModuleType("fake_target")
    fake.__dict__.update(attrs)
    return fake


def test_intelligent_cache_delegates_attribute():
    fake = _make_fake_module({"IntelligentCache": 123})
    with patch("importlib.import_module", return_value=fake):
        assert ic_module.IntelligentCache == 123


def test_intelligent_cache_dir_lists_target():
    fake = _make_fake_module({"A": 1, "B": 2})
    with patch("importlib.import_module", return_value=fake):
        assert "A" in dir(ic_module)


def test_intelligent_cache_warns_once():
    importlib.reload(ic_module)
    fake = _make_fake_module({"X": 1})
    with patch("importlib.import_module", return_value=fake), pytest.warns(DeprecationWarning):
        _ = ic_module.X
