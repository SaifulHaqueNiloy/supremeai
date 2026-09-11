"""Canonical data-service boundary.

Implementations remain owned by ``backend.database``. The facade is lazy so
health checks and capability discovery do not import optional database clients.
"""

from __future__ import annotations

import importlib

_TARGETS = ("database.db_repository", "database.tenant_db")


def __getattr__(name: str):
    for target in _TARGETS:
        module = importlib.import_module(target)
        if hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    names = set(globals())
    for target in _TARGETS:
        try:
            names.update(vars(importlib.import_module(target)))
        except ImportError:
            continue
    return sorted(names)
