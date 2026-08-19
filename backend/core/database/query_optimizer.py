"""Database query optimization utilities for SupremeAI.

Lightweight, dependency-free analyzer that records SQL queries, detects
N+1 query patterns, and exposes a profiling hook plus an eager-load
strategy registry used by db_optimization_middleware.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass
class QueryRecord:
    sql: str
    duration_ms: float
    timestamp: float


class QueryAnalyzer:
    """Collects executed queries and surfaces N+1 access patterns."""

    def __init__(self, n_plus_one_threshold: int = 5):
        self.queries: list[QueryRecord] = []
        self.n_plus_one_threshold = n_plus_one_threshold

    def record(self, sql: str, duration_ms: float = 0.0) -> None:
        self.queries.append(QueryRecord(sql=sql, duration_ms=duration_ms, timestamp=time.time()))

    def reset(self) -> None:
        self.queries = []

    @staticmethod
    def _normalize(sql: str) -> str:
        # Strip literals/whitespace so repeated parameterized queries group together.
        s = re.sub(r"('[^']*'|\?|\$\d+|%s)", "?", sql, flags=re.IGNORECASE)
        s = re.sub(r"\s+", " ", s).strip().lower()
        return s

    def get_n_plus_one_warnings(self) -> list[dict[str, Any]]:
        counts: dict[str, int] = defaultdict(int)
        for q in self.queries:
            counts[self._normalize(q.sql)] += 1
        warnings = []
        for normalized, count in counts.items():
            if count >= self.n_plus_one_threshold:
                warnings.append(
                    {
                        "normalized_sql": normalized,
                        "occurrence_count": count,
                        "threshold": self.n_plus_one_threshold,
                    }
                )
        return warnings


class OptimizationCache:
    """Tiny stats-tracking cache used to measure query-plan reuse."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        if key in self._store:
            self._hits += 1
            return self._store[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        hit_rate = (self._hits / total) if total else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._store),
            "hit_rate": round(hit_rate, 3),
        }


class QueryOptimizer:
    """Aggregates analyzer + cache + eager-load strategy registry."""

    def __init__(self) -> None:
        self.analyzer = QueryAnalyzer()
        self.optimization_cache = OptimizationCache()
        self.eager_load_strategies: dict[str, dict[str, Any]] = {}

    def register_eager_load_strategy(
        self, model: Any, relations: list[str], strategy: str = "selectinload"
    ) -> None:
        key = getattr(model, "__tablename__", getattr(model, "__name__", str(model)))
        self.eager_load_strategies[key] = {"relations": relations, "strategy": strategy}

    def record_query(self, sql: str, duration_ms: float = 0.0) -> None:
        self.analyzer.record(sql, duration_ms)


query_optimizer = QueryOptimizer()


class DatabaseOptimizationMiddleware:
    """Middleware wrapper that profiles queries for a single request session."""

    def __init__(self, optimizer: QueryOptimizer | None = None) -> None:
        self.optimizer = optimizer or query_optimizer

    async def __call__(self, request: Any, call_next: Any) -> Any:
        before = len(self.optimizer.analyzer.queries)
        response = await call_next(request)
        after = len(self.optimizer.analyzer.queries)
        if after - before >= self.optimizer.analyzer.n_plus_one_threshold:
            warnings = self.optimizer.analyzer.get_n_plus_one_warnings()
            if warnings:
                response.headers["X-Performance-Warning"] = "Potential N+1 query detected"
        return response


def setup_query_profiling(engine: Any) -> None:
    """Attach a do-execute hook to an SQLAlchemy engine to record queries.

    No-op safe: if the engine does not support event listeners the function
    simply records nothing rather than raising.
    """
    try:
        from sqlalchemy import event

        @event.listens_for(engine, "after_cursor_execute")
        def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
            query_optimizer.record_query(statement)
    except Exception:
        # Engine not available / not SQLAlchemy -- profiling stays disabled.
        pass
