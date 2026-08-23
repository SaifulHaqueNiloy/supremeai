"""pyerrorfix — reusable Python error-detection & auto-fix engine.

Designed to run in GitHub Actions pipelines and as a library inside any system
that needs to find (and fix) common Python bugs in arbitrary user code.

Zero runtime dependencies — uses only the Python standard library (ast, tokenize,
re, pathlib, json, argparse). Optional PyYAML support for YAML config files.

Quick start
------------
CLI::

    python -m pyerrorfix analyze backend/ --format json --fix
    python -m pyerrorfix catalog --format json
    echo 'def f():\n  x' | python -m pyerrorfix analyze --stdin --format json

Library::

    from pyerrorfix.core.scanner import Scanner
    result = Scanner().scan_source(source_code, filename="app.py")
    print(result.issues)
"""

from __future__ import annotations

__version__ = "1.0.0"
__all__ = ["__version__"]
