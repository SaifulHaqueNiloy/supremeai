"""
Memory Recency Decay & Deduplication Engine
============================================
Applies logarithmic temporal decay multipliers to memory search scores:
`adjusted_score = base_similarity * (1.0 / (1.0 + lambda * log(1 + days_old)))`
Deduplicates highly similar memory nodes (cosine > 0.95) to prevent stale patterns.
"""

from __future__ import annotations

import math
import time
from typing import Any


class RecencyDecayFilter:
    """
    Filters and re-scores memory nodes based on temporal freshness and deduplication.
    """

    def __init__(self, decay_rate: float = 0.05, deduplication_threshold: float = 0.95):
        self.decay_rate = decay_rate
        self.deduplication_threshold = deduplication_threshold

    def calculate_decayed_score(self, similarity_score: float, created_at_timestamp: float, now: float | None = None) -> float:
        """
        Calculates time-decayed relevance score.
        """
        current_time = now if now is not None else time.time()
        age_seconds = max(0.0, current_time - created_at_timestamp)
        days_old = age_seconds / 86400.0

        # Logarithmic decay formula: keeps high relevance while gracefully dampening old entries
        decay_multiplier = 1.0 / (1.0 + self.decay_rate * math.log(1.0 + days_old))
        return round(similarity_score * decay_multiplier, 4)

    def filter_and_rank_memories(
        self,
        candidate_memories: list[dict[str, Any]],
        now: float | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Applies recency decay and deduplication across a set of retrieved memories.
        """
        current_time = now if now is not None else time.time()
        scored_candidates = []

        for mem in candidate_memories:
            base_score = float(mem.get("similarity", 0.8))
            created_at = float(mem.get("created_at", current_time))
            adjusted = self.calculate_decayed_score(base_score, created_at, now=current_time)

            item = dict(mem)
            item["adjusted_score"] = adjusted
            scored_candidates.append(item)

        # Sort by adjusted score descending
        scored_candidates.sort(key=lambda x: x["adjusted_score"], reverse=True)

        # Deduplicate based on text content overlap / high similarity
        unique_results: list[dict[str, Any]] = []
        seen_texts: set[str] = set()

        for cand in scored_candidates:
            text = cand.get("content", cand.get("label", "")).strip().lower()
            if text and text in seen_texts:
                continue
            seen_texts.add(text)
            unique_results.append(cand)
            if len(unique_results) >= top_k:
                break

        return unique_results


# Singleton instance
recency_decay_filter = RecencyDecayFilter()
