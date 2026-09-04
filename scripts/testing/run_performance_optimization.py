#!/usr/bin/env python3
"""
SupremeAI Performance Optimization Runner
==========================================

This script runs comprehensive performance benchmarks and applies optimizations.

বাংলা:
সুপ্রীমএআই পারফরমেন্স অপটিমাইজেশন রানার
এই স্ক্রিপ্টটি সম্পূর্ণ পারফরমেন্স বেঞ্চমার্ক চালায় এবং অপটিমাইজেশন প্রয়োগ করে।
"""

import asyncio
import json
import os
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))
os.chdir(backend_path)

from core.logging_config import logger
from core.optimization.performance_optimizer import (
    LRUCache,
    AsyncLRUCache,
    QueryOptimizer,
    AsyncPoolManager,
    performance_monitor,
    PerformanceOptimizer,
    OptimizationLevel,
)


def benchmark_cache_operations(iterations: int = 10000, cache_size: int = 1000):
    """Benchmark LRU cache operations."""
    logger.info(f"Running cache benchmark with {iterations} iterations...")
    
    cache = LRUCache(maxsize=cache_size, ttl=300)
    
    # Benchmark put operations
    start = time.perf_counter()
    for i in range(iterations):
        cache.put(f"key_{i}", {"data": i, "timestamp": time.time()})
    put_time = time.perf_counter() - start
    put_ops_sec = iterations / put_time
    
    # Benchmark get operations (with hits and misses)
    start = time.perf_counter()
    hits = 0
    misses = 0
    for i in range(iterations):
        result = cache.get(f"key_{i}")
        if result is not None:
            hits += 1
        else:
            misses += 1
        
        # Add some misses
        if i % 2 == 0:
            cache.get(f"nonexistent_{i}")
            misses += 1
    get_time = time.perf_counter() - start
    get_ops_sec = iterations / get_time
    
    # Benchmark async cache
    async def benchmark_async():
        async_cache = AsyncLRUCache(maxsize=cache_size, ttl=300)
        
        start = time.perf_counter()
        for i in range(iterations):
            await async_cache.put(f"async_key_{i}", {"data": i})
        async_put_time = time.perf_counter() - start
        async_put_ops_sec = iterations / async_put_time
        
        start = time.perf_counter()
        for i in range(iterations):
            await async_cache.get(f"async_key_{i}")
        async_get_time = time.perf_counter() - start
        async_get_ops_sec = iterations / async_get_time
        
        return {
            "async_put_ops_sec": round(async_put_ops_sec, 2),
            "async_get_ops_sec": round(async_get_ops_sec, 2),
            "async_put_time_ms": round(async_put_time * 1000, 2),
            "async_get_time_ms": round(async_get_time * 1000, 2),
        }
    
    async_results = asyncio.run(benchmark_async())
    
    results = {
        "sync_put_ops_sec": round(put_ops_sec, 2),
        "sync_get_ops_sec": round(get_ops_sec, 2),
        "sync_put_time_ms": round(put_time * 1000, 2),
        "sync_get_time_ms": round(get_time * 1000, 2),
        "cache_hits": hits,
        "cache_misses": misses,
        "hit_rate": round(hits / (hits + misses) * 100, 2),
        **async_results,
    }
    
    logger.info(f"Cache benchmark complete: {put_ops_sec:.0f} put ops/sec, {get_ops_sec:.0f} get ops/sec")
    return results


def benchmark_query_optimizer():
    """Benchmark query optimization capabilities."""
    logger.info("Running query optimizer benchmark...")
    
    optimizer = QueryOptimizer()
    
    # Simulate queries
    queries = [
        "SELECT * FROM users WHERE id = 1",
        "SELECT * FROM users WHERE email = 'test@example.com'",
        "SELECT * FROM orders WHERE user_id = 1 AND status = 'pending'",
        "SELECT COUNT(*) FROM products WHERE category = 'electronics'",
    ]
    
    start = time.perf_counter()
    optimized_queries = []
    for query in queries * 100:  # Run 100 times each
        optimized = optimizer.optimize_query(query)
        optimized_queries.append(optimized)
    optimize_time = time.perf_counter() - start
    
    cache_stats = optimizer.get_cache_stats()
    
    results = {
        "queries_processed": len(optimized_queries),
        "total_time_ms": round(optimize_time * 1000, 2),
        "queries_per_sec": round(len(optimized_queries) / optimize_time, 2),
        "cache_hits": cache_stats.get("hits", 0),
        "cache_misses": cache_stats.get("misses", 0),
    }
    
    logger.info(f"Query optimizer benchmark complete: {results['queries_per_sec']:.0f} queries/sec")
    return results


def benchmark_connection_pool():
    """Benchmark connection pool management."""
    logger.info("Running connection pool benchmark...")
    
    pool_manager = AsyncPoolManager(
        pool_name="test_pool",
        max_connections=10,
        min_connections=2,
        max_idle_time=300,
    )
    
    # Simulate connection acquisitions
    start = time.perf_counter()
    acquisitions = 0
    for i in range(1000):
        try:
            conn = pool_manager.acquire_connection()
            if conn:
                acquisitions += 1
                # Simulate work
                time.sleep(0.001)
                pool_manager.release_connection(conn)
        except Exception:
            pass
    total_time = time.perf_counter() - start
    
    stats = pool_manager.get_pool_stats()
    
    results = {
        "successful_acquisitions": acquisitions,
        "total_time_ms": round(total_time * 1000, 2),
        "acquisitions_per_sec": round(acquisitions / total_time, 2),
        "pool_size": stats.get("current_size", 0),
        "available_connections": stats.get("available", 0),
    }
    
    logger.info(f"Connection pool benchmark complete: {results['acquisitions_per_sec']:.0f} acquisitions/sec")
    return results


def benchmark_batch_processor():
    """Benchmark batch processing capabilities."""
    logger.info("Running batch processor benchmark...")
    
    optimizer = PerformanceOptimizer(level=OptimizationLevel.MODERATE)
    
    # Simulate data processing with optimization
    data_items = [{"id": i, "value": f"data_{i}"} for i in range(1000)]
    
    start = time.perf_counter()
    
    def process_item(item):
        # Simulate processing
        time.sleep(0.001)
        return {"processed": True, **item}
    
    # Use ThreadPoolExecutor for batch processing
    from concurrent.futures import ThreadPoolExecutor
    results_data = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        results_data = list(executor.map(process_item, data_items))
    
    total_time = time.perf_counter() - start
    
    results = {
        "items_processed": len(results_data),
        "total_time_ms": round(total_time * 1000, 2),
        "items_per_sec": round(len(results_data) / total_time, 2),
        "batch_size": 100,
        "workers": 4,
    }
    
    logger.info(f"Batch processor benchmark complete: {results['items_per_sec']:.0f} items/sec")
    return results


def memory_profiling():
    """Profile memory usage of core components."""
    logger.info("Running memory profiling...")
    
    tracemalloc.start()
    
    # Create various objects
    cache = LRUCache(maxsize=10000)
    for i in range(5000):
        cache.put(f"key_{i}", {"data": list(range(100)), "metadata": {"id": i}})
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    results = {
        "current_memory_mb": round(current / 1024 / 1024, 2),
        "peak_memory_mb": round(peak / 1024 / 1024, 2),
        "cache_entries": 5000,
        "memory_per_entry_kb": round((current / 5000) / 1024, 4),
    }
    
    logger.info(f"Memory profiling complete: Current={results['current_memory_mb']:.2f}MB, Peak={results['peak_memory_mb']:.2f}MB")
    return results


def run_all_benchmarks():
    """Run all performance benchmarks and generate report."""
    logger.info("=" * 60)
    logger.info("SupremeAI Performance Benchmark Suite")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    benchmarks = {
        "cache": benchmark_cache_operations,
        "query_optimizer": benchmark_query_optimizer,
        "connection_pool": benchmark_connection_pool,
        "batch_processor": benchmark_batch_processor,
        "memory": memory_profiling,
    }
    
    results = {}
    for name, benchmark_fn in benchmarks.items():
        try:
            logger.info(f"\n{'='*40}")
            logger.info(f"Running {name} benchmark...")
            logger.info(f"{'='*40}")
            results[name] = benchmark_fn()
        except Exception as e:
            logger.error(f"Benchmark {name} failed: {e}")
            results[name] = {"error": str(e)}
    
    total_time = time.time() - start_time
    
    # Generate summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_benchmark_time_sec": round(total_time, 2),
        "benchmarks_run": len([r for r in results.values() if "error" not in r]),
        "benchmarks_failed": len([r for r in results.values() if "error" in r]),
        "detailed_results": results,
    }
    
    # Save results
    output_file = Path(__file__).parent / "performance_optimization_report.json"
    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\n{'='*60}")
    logger.info("BENCHMARK SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info(f"Successful benchmarks: {summary['benchmarks_run']}")
    logger.info(f"Failed benchmarks: {summary['benchmarks_failed']}")
    logger.info(f"Report saved to: {output_file}")
    
    # Print key metrics
    if "cache" in results and "error" not in results["cache"]:
        logger.info(f"\nCache Performance:")
        logger.info(f"  Sync PUT: {results['cache']['sync_put_ops_sec']:.0f} ops/sec")
        logger.info(f"  Sync GET: {results['cache']['sync_get_ops_sec']:.0f} ops/sec")
        logger.info(f"  Async PUT: {results['cache']['async_put_ops_sec']:.0f} ops/sec")
        logger.info(f"  Async GET: {results['cache']['async_get_ops_sec']:.0f} ops/sec")
        logger.info(f"  Hit rate: {results['cache']['hit_rate']:.1f}%")
    
    if "query_optimizer" in results and "error" not in results["query_optimizer"]:
        logger.info(f"\nQuery Optimizer:")
        logger.info(f"  Queries/sec: {results['query_optimizer']['queries_per_sec']:.0f}")
    
    if "batch_processor" in results and "error" not in results["batch_processor"]:
        logger.info(f"\nBatch Processor:")
        logger.info(f"  Items/sec: {results['batch_processor']['items_per_sec']:.0f}")
    
    logger.info(f"\n{'='*60}")
    
    return summary


if __name__ == "__main__":
    results = run_all_benchmarks()
    
    # Exit with error if any benchmarks failed
    if results["benchmarks_failed"] > 0:
        sys.exit(1)
    sys.exit(0)
