"""Fixer registry."""
from __future__ import annotations

from typing import Any

from pyerrorfix.fixers.await_fixer import AwaitFixer
from pyerrorfix.fixers.base import BaseFixer
from pyerrorfix.fixers.except_fixer import BareExceptFixer
from pyerrorfix.fixers.fstring_log_fixer import FStringLogFixer
from pyerrorfix.fixers.import_fixer import ImportSortFixer, UnusedImportFixer
from pyerrorfix.fixers.with_fixer import WithOpenFixer

ALL_FIXERS: list[type[BaseFixer]] = [
    UnusedImportFixer,
    AwaitFixer,
    BareExceptFixer,
    FStringLogFixer,
    WithOpenFixer,
    ImportSortFixer,
]

__all__ = ["ALL_FIXERS", "BaseFixer"]
