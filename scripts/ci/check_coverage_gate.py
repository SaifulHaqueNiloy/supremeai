#!/usr/bin/env python3
"""Coverage degradation gate (Phase 3 / M3.1).

Bangla: Coverage regression-কে রুখতে একটি fail-on-degradation গেট।
রোডম্যাপ অনুযায়ী এটি "slow (warning → hard)" মোডে শুরু হয়:
- প্রথম রানে baseline ফাইল না থাকলে বর্তমান coverage দিয়ে seed করে।
- বর্তমান coverage বেসলাইন থেকে allowed_degradation-এর বেশি কমে গেলে
  --fail-on-regression থাকলে exit 1 (hard fail), না থাকলে warning (exit 0)।

ASCII markers are used (no emoji) so the gate never crashes on non-UTF-8
consoles (e.g. Windows cp1252) while still being readable in CI logs.

Usage:
    python scripts/ci/check_coverage_gate.py \
        --coverage-json backend/coverage.json \
        --baseline backend/coverage-baseline.json \
        --allowed-degradation 2.0 [--fail-on-regression]
"""

from __future__ import annotations

import argparse
import json
import sys


def _human(value: float) -> str:
    return f"{value:.2f}%"


def read_overall(coverage_json_path: str) -> float | None:
    """Extract overall line coverage % from a pytest-cov JSON report."""
    try:
        with open(coverage_json_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[WARN] Could not parse coverage JSON '{coverage_json_path}': {exc}", file=sys.stderr)
        return None

    totals = data.get("totals", {})
    # pytest-cov writes `percent_covered` as a float 0..100.
    overall = totals.get("percent_covered")
    if overall is None:
        # Fallback: some reports use a nested key.
        overall = (totals.get("percent_covered_display") or "0").replace("%", "")
        try:
            overall = float(overall)
        except (TypeError, ValueError):
            overall = None
    return float(overall) if overall is not None else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Coverage degradation gate")
    parser.add_argument("--coverage-json", default="coverage.json", help="pytest-cov JSON report path")
    parser.add_argument(
        "--baseline",
        default="coverage-baseline.json",
        help="Committed baseline coverage JSON path",
    )
    parser.add_argument(
        "--allowed-degradation",
        type=float,
        default=2.0,
        help="Allowed absolute % drop vs baseline before failing",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Hard-fail (exit 1) when coverage drops beyond allowed degradation",
    )
    args = parser.parse_args()

    current = read_overall(args.coverage_json)
    if current is None:
        print(
            f"[INFO] Coverage report '{args.coverage_json}' not found -- "
            f"skipping degradation gate (likely a smoke-only run).",
            file=sys.stderr,
        )
        return 0

    try:
        with open(args.baseline, "r", encoding="utf-8") as fh:
            baseline_data = json.load(fh)
        baseline = float(baseline_data.get("overall", 0.0))
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        # Seed the baseline on first run so subsequent runs can detect regression.
        baseline = current
        with open(args.baseline, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "overall": baseline,
                    "seeded_by": "check_coverage_gate.py",
                    "note": "Auto-seeded baseline; tune upward as coverage grows toward 80% target.",
                },
                fh,
                indent=2,
            )
        print(
            f"[SEED] Seeded coverage baseline at {_human(baseline)} "
            f"(from '{args.coverage_json}'). Future runs will block regressions."
        )
        return 0

    delta = current - baseline
    if delta >= 0:
        print(f"[OK] Coverage {_human(current)} (baseline {_human(baseline)}, +{_human(delta)}). No regression.")
        return 0

    drop = abs(delta)
    if drop <= args.allowed_degradation:
        print(
            f"[WARN] Coverage {_human(current)} is {_human(drop)} below baseline "
            f"{_human(baseline)} -- within allowed degradation "
            f"({_human(args.allowed_degradation)}). Warning only."
        )
        return 1 if args.fail_on_regression else 0

    print(
        f"[FAIL] Coverage {_human(current)} dropped {_human(drop)} below baseline "
        f"{_human(baseline)} (allowed {_human(args.allowed_degradation)}).",
        file=sys.stderr,
    )
    if args.fail_on_regression:
        print("[ALERT] Coverage regression detected -- failing gate.", file=sys.stderr)
        return 1
    print("[WARN] Warning only (--fail-on-regression not set).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
