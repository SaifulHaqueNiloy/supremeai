"""Unit tests for backend/main.py entrypoint and lifecycle handlers."""

import os
import signal
import pytest
from unittest.mock import patch, MagicMock


def test_main_lazy_app_export():
    """Test that main.py lazily re-exports the FastAPI app instance."""
    import main

    assert hasattr(main, "app")
    assert main.app is not None
    assert main._APP_IMPORT_STRING == "core.app:app"


def test_main_invalid_attribute_raises():
    """Test that accessing an undefined attribute on main raises AttributeError."""
    import main

    with pytest.raises(AttributeError):
        _ = main.non_existent_attribute_12345


def test_handle_sigterm_sets_env():
    """Test that _handle_sigterm records shutdown intent without premature exit."""
    from main import _handle_sigterm

    os.environ.pop("UVICORN_SHUTDOWN_REQUESTED", None)
    _handle_sigterm(signal.SIGTERM, None)

    assert os.environ.get("UVICORN_SHUTDOWN_REQUESTED") == "1"


@patch("uvicorn.run")
def test_run_server_invokes_uvicorn(mock_uvicorn_run):
    """Test run_server configures and invokes uvicorn with expected parameters."""
    from main import run_server

    run_server()
    assert mock_uvicorn_run.called
    args, kwargs = mock_uvicorn_run.call_args
    assert args[0] == "core.app:app"
    assert "host" in kwargs
    assert "port" in kwargs
    assert "log_level" in kwargs
