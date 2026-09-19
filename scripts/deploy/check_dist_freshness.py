#!/usr/bin/env python3
"""
Pre-deploy freshness gate for Firebase Hosting deploys (FB-04 / Issue #585).

`deploy:frontend` used to run `firebase deploy --only hosting` against whatever
happened to sit in `frontend/dist` — stale from a previous local build, or
missing entirely on a fresh clone. `firebase deploy` uploads an empty/stale
`public` dir with no error, so a developer who edits source and skips the build
ships the OLD bundle. There is no CI gate for firebase deploys, so nothing else
catches this.

This gate runs AFTER the frontend build and BEFORE `firebase deploy` in
`pnpm deploy:frontend` and fails closed when:
  1. `frontend/dist/index.html` does not exist (build produced no output), or
  2. its mtime is older than the newest file under `frontend/src/`
     (the bundle was not produced from the current sources).

Stdlib only — no third-party dependencies, mirrors generate_firebase_config.py.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DIST_INDEX = REPO_ROOT / "frontend" / "dist" / "index.html"
SRC_ROOT = REPO_ROOT / "frontend" / "src"
BUILD_CMD = "pnpm --filter supremeai-studio-client... build"


def _fmt(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds")


def _newest_source_mtime() -> float | None:
    """Newest mtime under frontend/src/ (None when the dir is absent/empty)."""
    if not SRC_ROOT.is_dir():
        return None
    mtimes = [p.stat().st_mtime for p in SRC_ROOT.rglob("*") if p.is_file()]
    return max(mtimes) if mtimes else None


def main() -> int:
    if not DIST_INDEX.is_file():
        print(
            "❌ ERROR: frontend/dist/index.html not found — the frontend build "
            "produced no output (or never ran). Build before deploying: "
            f"{BUILD_CMD}"
        )
        return 1

    dist_mtime = DIST_INDEX.stat().st_mtime
    newest_src = _newest_source_mtime()
    if newest_src is not None and dist_mtime < newest_src:
        print(
            "❌ ERROR: frontend/dist/index.html is STALE — it is older than the "
            f"newest file in frontend/src/ (dist built {_fmt(dist_mtime)}, "
            f"newest source {_fmt(newest_src)}). Refusing to deploy a stale "
            f"bundle. Rebuild first: {BUILD_CMD}"
        )
        return 1

    print(
        "✅ frontend/dist/index.html is fresh "
        f"(built {_fmt(dist_mtime)} >= newest frontend/src mtime)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
