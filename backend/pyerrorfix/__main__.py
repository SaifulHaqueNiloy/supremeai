"""Allow `python -m pyerrorfix ...`."""
from __future__ import annotations

from pyerrorfix.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
