def test_probe_logging_file():
    import importlib

    mod = importlib.import_module("core.logging")
    print("LOGGING_FILE", getattr(mod, "__file__", None))
    assert "core/logging.py" in (getattr(mod, "__file__", "") or "")
