#!/usr/bin/env python3
"""
CI Benchmark Regression Detector & Performance Gate
===================================================
বাংলা: নাইটলি বা CI রান শেষে সিন্থেটিক বেঞ্চমার্কের p95 ল্যাটেন্সি,
RPS এবং এরর রেট বেসলাইনের সাথে তুলনা করে রিগ্রেশন ডিটেক্ট করে।

Usage:
    python scripts/ci/check_benchmark_regression.py \
        --current benchmark_results.json \
        --baseline backend/baselines/benchmark_baseline.json \
        --fail-on-regression
"""

from __future__ import annotations

import argparse
import json
import os
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def check_regressions(
    current_data: dict,
    baseline_data: dict,
    latency_tolerance_pct: float = 25.0
) -> tuple[bool, list[str], dict]:
    """
    Compares current benchmark output against threshold limits and baseline.
    Returns: (passed, list of violation messages, summary_dict)
    """
    violations: list[str] = []
    thresholds = baseline_data.get("thresholds", {})
    last_known = baseline_data.get("last_known_metrics", {})
    summary = {}

    for scenario, metrics in current_data.items():
        if not isinstance(metrics, dict):
            continue

        p95 = metrics.get("latencies_ms", {}).get("p95", 0.0)
        error_rate = metrics.get("error_rate_pct", 0.0)
        rps = metrics.get("rps", 0.0)

        th = thresholds.get(scenario, {})
        max_p95 = th.get("max_p95_latency_ms", 999999.0)
        max_err = th.get("max_error_rate_pct", 100.0)
        min_rps = th.get("min_rps", 0.0)

        # Baseline comparison
        prev = last_known.get(scenario, {})
        prev_p95 = prev.get("p95_ms", p95)
        allowed_p95 = max(max_p95, prev_p95 * (1.0 + (latency_tolerance_pct / 100.0)))

        is_violating = False
        reasons = []

        if p95 > allowed_p95:
            is_violating = True
            reasons.append(f"p95 latency {p95:.2f}ms > threshold {allowed_p95:.2f}ms")

        if error_rate > max_err:
            is_violating = True
            reasons.append(f"Error rate {error_rate:.1f}% > threshold {max_err:.1f}%")

        if rps < min_rps * 0.5:
            is_violating = True
            reasons.append(f"RPS {rps:.1f} < minimum required {min_rps:.1f}")

        status = "REGRESSION" if is_violating else "PASSED"
        if is_violating:
            violations.append(f"[{scenario}] " + "; ".join(reasons))

        summary[scenario] = {
            "status": status,
            "current_p95_ms": p95,
            "threshold_p95_ms": allowed_p95,
            "current_error_pct": error_rate,
            "current_rps": rps,
            "reasons": reasons,
        }

    all_passed = (len(violations) == 0)
    return all_passed, violations, summary


def main():
    parser = argparse.ArgumentParser(description="SupremeAI Benchmark Regression Gate")
    parser.add_argument("--current", required=True, help="Path to current benchmark JSON report")
    parser.add_argument("--baseline", required=True, help="Path to baseline JSON report")
    parser.add_argument("--tolerance-pct", type=float, default=25.0, help="Allowed latency degradation percentage")
    parser.add_argument("--fail-on-regression", action="store_true", help="Exit with 1 if regression is detected")
    parser.add_argument("--github-summary", action="store_true", help="Write report to GITHUB_STEP_SUMMARY")

    args = parser.parse_args()

    if not os.path.exists(args.current):
        print(f"[ERROR] Current benchmark file not found: {args.current}")
        sys.exit(1)

    if not os.path.exists(args.baseline):
        print(f"[WARN] Baseline file not found: {args.baseline}. Seeding baseline from current...")
        with open(args.current, "r", encoding="utf-8") as f:
            cur = json.load(f)
        os.makedirs(os.path.dirname(args.baseline), exist_ok=True)
        with open(args.baseline, "w", encoding="utf-8") as f:
            json.dump({"thresholds": {}, "last_known_metrics": cur}, f, indent=2)
        print("[OK] Baseline seeded successfully.")
        sys.exit(0)

    with open(args.current, "r", encoding="utf-8") as f:
        current_data = json.load(f)

    with open(args.baseline, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)

    passed, violations, summary = check_regressions(
        current_data,
        baseline_data,
        latency_tolerance_pct=args.tolerance_pct
    )

    print("=" * 78)
    print(" 🚀 SupremeAI Benchmark Regression Analysis")
    print("=" * 78)
    for scenario, res in summary.items():
        mark = "✅ PASSED" if res["status"] == "PASSED" else "❌ REGRESSION"
        print(f"{mark} | {scenario:<30} | p95: {res['current_p95_ms']:>8.2f}ms | err: {res['current_error_pct']:>5.1f}% | rps: {res['current_rps']:>8.1f}")
        if res["reasons"]:
            for r in res["reasons"]:
                print(f"       ⚠️  {r}")
    print("=" * 78)

    # Optional GitHub Step Summary export
    step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if args.github_summary and step_summary_path:
        with open(step_summary_path, "a", encoding="utf-8") as f:
            f.write("### 🚀 Synthetic Benchmark Performance Gate\n\n")
            f.write("| Scenario | Status | Current p95 | Threshold p95 | Error Rate | RPS |\n")
            f.write("|---|---|---|---|---|---|\n")
            for sc, res in summary.items():
                badge = "🟢 Pass" if res["status"] == "PASSED" else "🔴 Regression"
                f.write(f"| {sc} | {badge} | {res['current_p95_ms']:.2f} ms | {res['threshold_p95_ms']:.2f} ms | {res['current_error_pct']:.1f}% | {res['current_rps']:.1f} |\n")
            if violations:
                f.write("\n> ⚠️ **Regression Warnings:**\n")
                for v in violations:
                    f.write(f"> - {v}\n")

    if not passed and args.fail_on_regression:
        print("\n❌ Performance regression gate FAILED!")
        sys.exit(1)
    else:
        print("\n✅ Performance regression gate PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()
