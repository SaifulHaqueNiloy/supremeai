"""Lightweight Load Test Script for Phase 2 M2.6.

Bangla: লোড টেস্ট স্ক্রিপ্ট — RPS, p95, error rate পরিমাপ করে।
Usage:
    python -m workers.load_test --url http://localhost:8080/health --concurrency 10 --requests 1000
"""

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

# Use only free/zero-cost tools — httpx is already in the dependency tree


@dataclass
class LoadTestResult:
    """Load test result metrics."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration: float
    latencies: list[float] = field(default_factory=list)
    status_codes: dict[int, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def rps(self) -> float:
        """Requests per second."""
        return self.total_requests / self.total_duration if self.total_duration > 0 else 0

    @property
    def error_rate(self) -> float:
        """Error rate as percentage."""
        return (self.failed_requests / self.total_requests * 100) if self.total_requests > 0 else 0

    @property
    def p50(self) -> float:
        """50th percentile latency."""
        return statistics.quantiles(self.latencies, n=2)[0] if len(self.latencies) >= 2 else 0

    @property
    def p95(self) -> float:
        """95th percentile latency."""
        if len(self.latencies) < 2:
            return 0
        return statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) >= 20 else max(self.latencies)

    @property
    def p99(self) -> float:
        """99th percentile latency."""
        if len(self.latencies) < 2:
            return 0
        return statistics.quantiles(self.latencies, n=100)[98] if len(self.latencies) >= 100 else max(self.latencies)


async def single_request(
    client: httpx.AsyncClient,
    url: str,
    method: str,
    payload: Optional[str],
    timeout: float,
    semaphore: asyncio.Semaphore,
) -> tuple[float, int | None, str | None]:
    """Execute a single request and return (latency, status_code, error)."""
    async with semaphore:
        start = time.monotonic()
        try:
            if method.upper() == "POST" and payload:
                resp = await client.post(url, content=payload, timeout=timeout)
            elif method.upper() == "GET":
                resp = await client.get(url, timeout=timeout)
            else:
                resp = await client.request(method, url, content=payload or "", timeout=timeout)
            latency = time.monotonic() - start
            return latency, resp.status_code, None
        except Exception as e:
            latency = time.monotonic() - start
            return latency, None, str(e)


async def run_load_test(
    url: str,
    concurrency: int,
    total_requests: int,
    method: str,
    payload: Optional[str],
    timeout: float,
    """Run the load test with specified parameters."""
    semaphore = asyncio.Semaphore(concurrency)
    result = LoadTestResult(
        total_requests=total_requests,
        successful_requests=0,
        failed_requests=0,
        total_duration=0.0
    )

    headers = {"Content-Type": "application/json"} if payload else {}

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        start_time = time.monotonic()

        tasks = [
            single_request(client, url, method, payload, timeout, semaphore)
            for _ in range(total_requests)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        result.total_duration = time.monotonic() - start_time

        for latency, status_code, error in results:
            if isinstance(latency, Exception):
                result.failed_requests += 1
                result.errors.append(str(latency))
            elif error:
                result.failed_requests += 1
                result.errors.append(error)
            else:
                result.latencies.append(latency)
                if status_code:
                    result.status_codes[status_code] = result.status_codes.get(status_code, 0) + 1
                    if 200 <= status_code < 400:
                        result.successful_requests += 1
                    else:
                        result.failed_requests += 1

    return result


def format_report(result: LoadTestResult, url: str, concurrency: int) -> str:
    """Format the load test results as a report."""
    report = []
    report.append("=" * 70)
    report.append("SupremeAI Phase 2 — Load Test Report (M2.6)")
    report.append("=" * 70)
    report.append(f"URL:              {url}")
    report.append(f"Concurrency:      {concurrency}")
    report.append(f"Total Requests:   {result.total_requests}")
    report.append(f"Duration:         {result.total_duration:.2f}s")
    report.append("")
    report.append("-" * 70)
    report.append(f"RPS:              {result.rps:.2f}")
    report.append(f"Success:          {result.successful_requests} ({result.successful_requests / result.total_requests * 100:.1f}%)")
    report.append(f"Failed:           {result.failed_requests} ({result.error_rate:.1f}%)")
    report.append("")
    report.append("Latency (ms):")
    report.append(f"  p50:            {result.p50 * 1000:.1f}")
    report.append(f"  p95:            {result.p95 * 1000:.1f}")
    report.append(f"  p99:            {result.p99 * 1000:.1f}")
    report.append(f"  Max:            {max(result.latencies) * 1000:.1f}" if result.latencies else "  Max:            N/A")
    report.append(f"  Min:            {min(result.latencies) * 1000:.1f}" if result.latencies else "  Min:            N/A")
    report.append("")
    if result.status_codes:
        report.append("Status Codes:")
        for code, count in sorted(result.status_codes.items()):
            report.append(f"  {code}: {count}")
    if result.errors:
        report.append(f"\nUnique Errors: {len(set(result.errors[:20]))}")
        for err in sorted(set(result.errors[:5])):
            report.append(f"  - {err[:100]}")
    report.append("=" * 70)

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="SupremeAI Phase 2 Load Test (M2.6)")
    parser.add_argument("--url", required=True, help="Target URL to test")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--requests", type=int, default=1000, help="Total number of requests")
    parser.add_argument("--method", default="GET", choices=["GET", "POST", "PUT", "DELETE"])
    parser.add_argument("--payload", default=None, help="JSON payload for POST/PUT")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout (seconds)")
    args = parser.parse_args()

    print(f"Starting load test: {args.url} ({args.concurrency}c / {args.requests}req)")
    result = asyncio.run(run_load_test(
        url=args.url,
        concurrency=args.concurrency,
        total_requests=args.requests,
        method=args.method,
        payload=args.payload,
        timeout=args.timeout,
    ))

    report = format_report(result, args.url, args.concurrency)
    print(report)

    # Save report to file
    report_path = os.path.join(os.getcwd(), "load_test_report.txt")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")

    # Exit non-zero if error rate > 5%
    if result.error_rate > 5.0:
        print(f"\n⚠️  Error rate ({result.error_rate:.1f}%) exceeds 5% threshold — failure!")
        sys.exit(1)
    else:
        print(f"\n✅ Load test passed (error rate: {result.error_rate:.1f}%, p95: {result.p95 * 1000:.1f}ms)")


if __name__ == "__main__":
    main()