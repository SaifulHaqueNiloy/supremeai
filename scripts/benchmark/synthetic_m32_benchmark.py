#!/usr/bin/env python3
"""
CLI Runner for M3.2: Synthetic Benchmark Scenarios
==================================================
Usage:
    python scripts/benchmark/synthetic_m32_benchmark.py --all
    python scripts/benchmark/synthetic_m32_benchmark.py --scenario swarm --concurrency 20
    python scripts/benchmark/synthetic_m32_benchmark.py --scenario cost_guard
    python scripts/benchmark/synthetic_m32_benchmark.py --scenario jit_otp
    python scripts/benchmark/synthetic_m32_benchmark.py --all --output-json report.json
"""

import argparse
import asyncio
import json
import os
import sys

# Ensure backend root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from workers.synthetic_load_benchmark import (
    CostGuardBreachScenario,
    JitOtpValidationScenario,
    SwarmBenchmarkScenario,
    SyntheticBenchmarkSuiteRunner,
)


def format_table_row(name: str, total: int, rps: float, p95: float, err_rate: float) -> str:
    return f"| {name:<32} | {total:>8} | {rps:>10.1f} | {p95:>10.2f} ms | {err_rate:>9.1f}% |"


async def main_async(args):
    runner = SyntheticBenchmarkSuiteRunner()

    print("=" * 82)
    print(" 🚀 SupremeAI Synthetic Benchmark & E2E Verification Runner (Phase 3 M3.2)")
    print("=" * 82)

    results = {}

    if args.all or args.scenario == "swarm":
        print("\n[1/3] Executing Scenario: Demo Agent Swarm Concurrency & Circuit Breaker...")
        swarm_sc = SwarmBenchmarkScenario()
        metrics = await swarm_sc.run_benchmark(num_requests=args.requests, concurrency=args.concurrency)
        results["demo_agent_swarm"] = metrics.to_dict()
        print(f"  ✅ Completed {metrics.total_requests} swarm DAG executions (RPS: {metrics.rps:.1f}, p95: {metrics.p95_latency:.2f}ms)")

    if args.all or args.scenario == "cost_guard":
        print("\n[2/3] Executing Scenario: Cost Guard Budget Breach & Redis Fail-safe...")
        cg_sc = CostGuardBreachScenario()
        metrics = await cg_sc.run_benchmark(num_tenants=max(5, args.concurrency), tasks_per_tenant=args.requests // max(5, args.concurrency))
        results["cost_guard_breach"] = metrics.to_dict()
        print(f"  ✅ Completed {metrics.total_requests} budget checks (Approvals: {metrics.successful_requests}, Rejections: {metrics.failed_requests})")

    if args.all or args.scenario == "jit_otp":
        print("\n[3/3] Executing Scenario: JIT OTP Multi-Channel Verification & Escalation...")
        otp_sc = JitOtpValidationScenario()
        metrics = await otp_sc.run_benchmark(num_verifications=args.requests)
        results["jit_otp_validation"] = metrics.to_dict()
        print(f"  ✅ Completed {metrics.total_requests} OTP cycles (Success: {metrics.successful_requests}, Escalations granted: {metrics.successful_requests})")

    print("\n" + "=" * 82)
    print(" 📊 BENCHMARK PERFORMANCE SUMMARY")
    print("=" * 82)
    print(f"| {'Scenario Name':<32} | {'Requests':>8} | {'Throughput':>10} | {'p95 Latency':>13} | {'Error Rate':>10} |")
    print("|" + "-" * 34 + "|" + "-" * 10 + "|" + "-" * 12 + "|" + "-" * 15 + "|" + "-" * 12 + "|")

    for key, data in results.items():
        print(format_table_row(
            name=data["scenario"],
            total=data["total_requests"],
            rps=data["rps"],
            p95=data["latencies_ms"]["p95"],
            err_rate=data["error_rate_pct"],
        ))

    print("=" * 82)

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"💾 Report exported successfully to {args.output_json}")


def main():
    parser = argparse.ArgumentParser(description="SupremeAI M3.2 Synthetic Benchmark Runner")
    parser.add_argument("--all", action="store_true", default=True, help="Run all 3 benchmark scenarios")
    parser.add_argument("--scenario", choices=["swarm", "cost_guard", "jit_otp"], help="Run a specific scenario")
    parser.add_argument("--requests", type=int, default=50, help="Total requests / cycles per scenario")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrency limit for async execution")
    parser.add_argument("--output-json", type=str, default=None, help="File path to save JSON benchmark report")

    args = parser.parse_args()
    if args.scenario:
        args.all = False

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
