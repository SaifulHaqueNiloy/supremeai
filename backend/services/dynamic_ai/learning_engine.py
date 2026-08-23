# backend/services/dynamic_ai/learning_engine.py
"""
Self-Learning AI Router
Learns from experience which providers work best for different types of tasks
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from loguru import logger


class TaskType(Enum):
    """Categories of AI tasks"""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    REASONING = "reasoning"
    CREATIVE_WRITING = "creative_writing"
    ANALYSIS = "analysis"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"
    EMBEDDING = "embedding"
    CHAT = "chat"
    GENERAL = "general"


@dataclass
class ProviderPerformance:
    """Performance metrics for a provider on specific task type"""

    provider_id: str
    task_type: TaskType

    # Performance metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0

    # Quality scores (if measurable)
    avg_quality_score: float = 0.0  # 1-10 scale
    quality_ratings: int = 0

    # Cost tracking
    estimated_cost_usd: float = 0.0

    # Temporal patterns (learned)
    hourly_performance: dict[int, float] = field(default_factory=dict)  # hour -> success_rate

    # Last updated
    last_updated: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 100.0  # Optimistic default
        return (self.successful_requests / self.total_requests) * 100

    @property
    def avg_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests

    @property
    def score(self) -> float:
        """
        Composite score for ranking (higher = better)
        Considers: success rate, latency, cost, quality
        """
        if self.total_requests < 3:
            return 50.0  # Neutral score for insufficient data

        # Weighted components
        success_weight = 0.4
        latency_weight = 0.3
        quality_weight = 0.2
        cost_weight = 0.1

        # Normalize each component to 0-100
        success_score = self.success_rate

        # Lower latency is better (assume 10s = worst, 0s = best)
        latency_score = max(0, 100 - (self.avg_latency_ms / 100))  # 100ms = 99, 10s = 0

        quality_score = self.avg_quality_score * 10  # 1-10 -> 10-100

        # Lower cost is better (assume $0.10/request = worst)
        cost_per_request = self.estimated_cost_usd / max(1, self.total_requests)
        cost_score = max(0, 100 - (cost_per_request * 1000))  # $0.01 = 90, $0.10 = 0

        composite = (
            success_score * success_weight
            + latency_score * latency_weight
            + quality_score * quality_weight
            + cost_score * cost_weight
        )

        return composite


class LearningEngine:
    """
    Learns which providers work best for different tasks
    Continuously improves routing decisions based on actual performance
    """

    def __init__(self, storage_path: str | None = None):
        self._performance_data: dict[str, dict[TaskType, ProviderPerformance]] = {}
        self._task_detection_cache: dict[str, TaskType] = {}
        self._storage_path = storage_path
        self._last_save: float = 0.0
        self._save_interval: float = 300.0  # Save every 5 minutes

        # Global fallback order (used when no task-specific data)
        self._global_provider_ranking: list[tuple[str, float]] = []

    def detect_task_type(self, prompt: str, context: dict | None = None) -> TaskType:
        """
        Detect the type of task from the prompt
        Uses keyword matching + heuristics
        """
        # Check cache first
        cache_key = hash(prompt[:200]) % 10000
        if cache_key in self._task_detection_cache:
            return self._task_detection_cache[cache_key]

        prompt_lower = prompt.lower()

        # Code-related indicators
        code_keywords = [
            "code",
            "function",
            "def ",
            "class ",
            "python",
            "javascript",
            "api",
            "endpoint",
            "debug",
            "fix bug",
            "implement",
            "write",
        ]
        if any(kw in prompt_lower for kw in code_keywords):
            if any(kw in prompt_lower for kw in ["review", "improve", "optimize"]):
                task_type = TaskType.CODE_REVIEW
            else:
                task_type = TaskType.CODE_GENERATION

        # Reasoning indicators
        elif any(
            kw in prompt_lower
            for kw in ["why", "how does", "explain", "analyze", "compare", "reason", "think step"]
        ):
            task_type = TaskType.REASONING

        # Creative writing indicators
        elif any(
            kw in prompt_lower
            for kw in [
                "write a story",
                "create content",
                "blog post",
                "poem",
                "creative",
                "imagine",
                "draft",
            ]
        ):
            task_type = TaskType.CREATIVE_WRITING

        # Translation indicators
        elif any(
            kw in prompt_lower
            for kw in ["translate", "in bengali", "in english", "to bangla", "convert to"]
        ):
            task_type = TaskType.TRANSLATION

        # Summarization indicators
        elif any(
            kw in prompt_lower
            for kw in ["summarize", "summary", "brief", "tl;dr", "key points", "overview"]
        ):
            task_type = TaskType.SUMMARIZATION

        # Question answering
        elif "?" in prompt or any(
            kw in prompt_lower for kw in ["what", "who", "when", "where", "which"]
        ):
            task_type = TaskType.QUESTION_ANSWERING

        # Embedding (usually called programmatically)
        elif context and context.get("purpose") == "embedding":
            task_type = TaskType.EMBEDDING

        # Chat/conversational
        elif len(prompt.split()) < 20 and not any(
            kw in prompt_lower for kw in ["code", "write", "explain", "analyze", "translate"]
        ):
            task_type = TaskType.CHAT

        else:
            task_type = TaskType.GENERAL

        # Cache result
        self._task_detection_cache[cache_key] = task_type

        # Limit cache size
        if len(self._task_detection_cache) > 1000:
            self._task_detection_cache.clear()

        return task_type

    async def get_best_providers_for_task(
        self, prompt: str, available_providers: list, context: dict | None = None, top_k: int = 5
    ) -> list[tuple[str, float]]:
        """
        Get ranked list of best providers for this specific task
        Returns: [(provider_id, confidence_score), ...]
        """
        task_type = self.detect_task_type(prompt, context)

        # Get performance data for this task type
        candidates = []

        for provider in available_providers:
            provider_id = provider.provider_id

            # Get or create performance record
            if provider_id not in self._performance_data:
                self._performance_data[provider_id] = {}

            if task_type not in self._performance_data[provider_id]:
                self._performance_data[provider_id][task_type] = ProviderPerformance(
                    provider_id=provider_id, task_type=task_type
                )

            perf = self._performance_data[provider_id][task_type]

            # Calculate score
            score = perf.score

            # Boost for free tier providers (prefer free when quality is similar)
            if provider.is_free_tier and perf.total_requests > 5:
                if perf.success_rate > 70:  # Good enough free option
                    score *= 1.1  # 10% boost for free tier

            # Boost for recently successful (recency bias)
            if perf.last_updated > time.time() - 3600:  # Last hour
                if perf.success_rate > 80:
                    score *= 1.05  # 5% boost for recent success

            candidates.append((provider_id, score, perf))

        # Sort by score (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Return top K
        result = [(pid, score) for pid, score, _ in candidates[:top_k]]

        return result

    def record_interaction(
        self,
        provider_id: str,
        task_type: TaskType,
        success: bool,
        latency_ms: float,
        estimated_cost: float = 0.0,
        quality_score: float | None = None,
        prompt_hash: str | None = None,
    ):
        """
        Record an interaction with a provider for learning
        Call this after EVERY provider interaction
        """
        # Ensure provider exists in tracking
        if provider_id not in self._performance_data:
            self._performance_data[provider_id] = {}

        if task_type not in self._performance_data[provider_id]:
            self._performance_data[provider_id][task_type] = ProviderPerformance(
                provider_id=provider_id, task_type=task_type
            )

        perf = self._performance_data[provider_id][task_type]

        # Update metrics
        perf.total_requests += 1
        perf.total_latency_ms += latency_ms
        perf.estimated_cost_usd += estimated_cost
        perf.last_updated = time.time()

        if success:
            perf.successful_requests += 1
        else:
            perf.failed_requests += 1

        # Update quality score if provided
        if quality_score is not None:
            if perf.quality_ratings > 0:
                # Rolling average
                perf.avg_quality_score = (
                    perf.avg_quality_score * perf.quality_ratings + quality_score
                ) / (perf.quality_ratings + 1)
            else:
                perf.avg_quality_score = quality_score
            perf.quality_ratings += 1

        # Update hourly pattern
        current_hour = datetime.now().hour
        if current_hour not in perf.hourly_performance:
            perf.hourly_performance[current_hour] = {"success": 0, "total": 0}
        perf.hourly_performance[current_hour]["total"] += 1
        if success:
            perf.hourly_performance[current_hour]["success"] += 1

        # Periodic save
        if time.time() - self._last_save > self._save_interval:
            asyncio.create_task(self.save_learning_data())

    def get_provider_insights(self, provider_id: str) -> dict:
        """Get detailed insights about a provider's performance"""
        if provider_id not in self._performance_data:
            return {"error": "No data for this provider"}

        insights = {
            "provider_id": provider_id,
            "task_types": {},
            "overall": {
                "total_requests": 0,
                "overall_success_rate": 0,
                "best_task_type": None,
                "worst_task_type": None,
            },
        }

        total_requests = 0
        total_successes = 0
        best_score = -1
        worst_score = 101
        best_task = None
        worst_task = None

        for task_type, perf in self._performance_data[provider_id].items():
            insights["task_types"][task_type.value] = {
                "success_rate": round(perf.success_rate, 1),
                "avg_latency_ms": round(perf.avg_latency_ms, 1),
                "avg_quality_score": round(perf.avg_quality_score, 1),
                "total_requests": perf.total_requests,
                "score": round(perf.score, 1),
            }

            total_requests += perf.total_requests
            total_successes += perf.successful_requests

            if perf.score > best_score and perf.total_requests >= 3:
                best_score = perf.score
                best_task = task_type.value
            if perf.score < worst_score and perf.total_requests >= 3:
                worst_score = perf.score
                worst_task = task_type.value

        insights["overall"]["total_requests"] = total_requests
        insights["overall"]["overall_success_rate"] = round(
            (total_successes / total_requests * 100) if total_requests > 0 else 0, 1
        )
        insights["overall"]["best_task_type"] = best_task
        insights["overall"]["worst_task_type"] = worst_task

        return insights

    async def save_learning_data(self):
        """Persist learning data to disk"""
        if not self._storage_path:
            return

        try:
            import aiofiles

            # Convert to serializable format
            data = {}
            for provider_id, tasks in self._performance_data.items():
                data[provider_id] = {}
                for task_type, perf in tasks.items():
                    data[provider_id][task_type.value] = {
                        "total_requests": perf.total_requests,
                        "successful_requests": perf.successful_requests,
                        "failed_requests": perf.failed_requests,
                        "total_latency_ms": perf.total_latency_ms,
                        "avg_quality_score": perf.avg_quality_score,
                        "quality_ratings": perf.quality_ratings,
                        "estimated_cost_usd": perf.estimated_cost_usd,
                        "hourly_performance": perf.hourly_performance,
                        "last_updated": perf.last_updated,
                    }

            async with aiofiles.open(self._storage_path, "w") as f:
                await f.write(json.dumps(data, indent=2))

            self._last_save = time.time()
            logger.debug(f"💾 Learning data saved ({len(data)} providers)")

        except Exception as e:
            logger.debug(f"Failed to save learning data: {e}")

    async def load_learning_data(self):
        """Load persisted learning data"""
        if not self._storage_path:
            return

        try:
            import aiofiles

            async with aiofiles.open(self._storage_path) as f:
                content = await f.read()

            data = json.loads(content)

            for provider_id, tasks in data.items():
                self._performance_data[provider_id] = {}
                for task_type_str, perf_data in tasks.items():
                    task_type = TaskType(task_type_str)
                    perf = ProviderPerformance(
                        provider_id=provider_id, task_type=task_type, **perf_data
                    )
                    self._performance_data[provider_id][task_type] = perf

            logger.debug(f"📂 Learning data loaded ({len(data)} providers)")

        except FileNotFoundError:
            logger.debug("ℹ️ No existing learning data found, starting fresh")
        except Exception as e:
            logger.debug(f"Failed to load learning data: {e}")
