"""
================================================================================
PATCH 01: Unified Router Implementation
================================================================================

This patch consolidates 25+ router classes into a single UnifiedRouter.

INSTRUCTIONS:
1. Create file: backend/core/unified_router.py
2. Update imports in all files that use old routers
3. Keep old routers as deprecated wrappers during transition
4. Test thoroughly before deleting old implementations

ESTIMATED IMPACT:
- Reduces ~8,000 lines of router code to ~800 lines
- Single source of truth for all routing decisions
- Consistent behavior across entire application
"""

from __future__ import annotations

import asyncio
import random
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional

# ============================================================================
# Core Types
# ============================================================================


class RoutingStrategy(Enum):
    """Available routing strategies."""

    COST_BASED = "cost_based"
    PERFORMANCE_BASED = "performance_based"
    INTENT_BASED = "intent_based"
    COGNITIVE = "cognitive"
    ENSEMBLE = "ensemble"
    SOVEREIGN = "sovereign"
    ROUND_ROBIN = "round_robin"
    WEIGHTED_RANDOM = "weighted_random"
    LEAST_LATENCY = "least_latency"


@dataclass
class ModelInfo:
    """Information about an available model."""

    name: str
    provider: str
    cost_per_1k_tokens: float
    avg_latency_ms: int
    max_context_length: int
    supports_streaming: bool = True
    supports_functions: bool = False
    supports_vision: bool = False
    quality_score: float = 0.8  # 0-1, subjective quality rating

    # Runtime stats
    success_rate: float = 1.0
    current_load: int = 0
    last_error: str | None = None
    is_healthy: bool = True


@dataclass
class RoutingCriteria:
    """Input for routing decision."""

    prompt: str
    task_type: str = "general"
    user_id: str | None = None
    session_id: str | None = None

    # Constraints
    budget_constraint: float | None = None  # Max cost in USD
    latency_requirement_ms: int | None = None  # Max latency
    preferred_provider: str | None = None
    required_features: list[str] = field(default_factory=list)  # streaming, vision, etc.

    # Context
    conversation_history: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """Output from routing decision."""

    model: ModelInfo
    strategy_used: RoutingStrategy
    confidence: float  # 0-1 how confident in this choice
    estimated_cost: float
    estimated_latency_ms: int
    fallback_chain: list[ModelInfo]

    def to_dict(self) -> dict:
        return {
            "model": self.model.name,
            "provider": self.model.provider,
            "strategy": self.strategy_used.value,
            "confidence": self.confidence,
            "estimated_cost": self.estimated_cost,
            "estimated_latency_ms": self.estimated_latency_ms,
            "fallbacks": [m.name for m in self.fallback_chain],
        }


# ============================================================================
# Strategy Interface & Implementations
# ============================================================================


class BaseRoutingStrategy(ABC):
    """Base class for routing strategies."""

    @abstractmethod
    async def select_model(
        self, criteria: RoutingCriteria, available_models: list[ModelInfo], context: dict = None
    ) -> tuple[ModelInfo, list[ModelInfo]]:
        """
        Select best model and provide fallback chain.

        Returns: (selected_model, fallback_models)
        """
        pass


class CostBasedStrategy(BaseRoutingStrategy):
    """Select model based on cost constraints."""

    async def select_model(self, criteria, available_models, context=None):
        # Filter by budget if specified
        if criteria.budget_constraint:
            affordable = [
                m for m in available_models if m.cost_per_1k_tokens <= criteria.budget_constraint
            ]
            if not affordable:
                affordable = [min(available_models, key=lambda m: m.cost_per_1k_tokens)]
        else:
            affordable = available_models

        # Sort by cost (cheapest first)
        sorted_models = sorted(affordable, key=lambda m: m.cost_per_1k_tokens)

        return sorted_models[0], sorted_models[1:4]


class PerformanceBasedStrategy(BaseRoutingStrategy):
    """Select model based on latency requirements."""

    async def select_model(self, criteria, available_models, context=None):
        # Filter by latency requirement
        if criteria.latency_requirement_ms:
            fast_enough = [
                m for m in available_models if m.avg_latency_ms <= criteria.latency_requirement_ms
            ]
            if not fast_enough:
                fast_enough = [min(available_models, key=lambda m: m.avg_latency_ms)]
        else:
            fast_enough = available_models

        # Sort by latency (fastest first)
        sorted_models = sorted(fast_enough, key=lambda m: m.avg_latency_ms)

        return sorted_models[0], sorted_models[1:4]


class IntentBasedStrategy(BaseRoutingStrategy):
    """Select model based on detected intent."""

    INTENT_KEYWORDS = {
        "code": ["code", "programming", "function", "debug", "error"],
        "math": ["calculate", "equation", "math", "solve", "formula"],
        "creative": ["write", "story", "poem", "creative", "imagine"],
        "analysis": ["analyze", "compare", "evaluate", "assess", "review"],
        "question": ["what", "why", "how", "who", "when", "where"],
    }

    async def select_model(self, criteria, available_models, context=None):
        # Detect intent from prompt
        intent = self._detect_intent(criteria.prompt)

        # Score models by intent suitability (could be ML-based)
        scored_models = []
        for model in available_models:
            score = self._score_for_intent(model, intent)
            scored_models.append((score, model))

        scored_models.sort(key=lambda x: x[0], reverse=True)
        best = scored_models[0][1]
        fallbacks = [m for _, m in scored_models[1:4]]

        return best, fallbacks

    def _detect_intent(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        scores = {}

        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in prompt_lower)
            scores[intent] = score

        return max(scores, key=scores.get) if any(scores.values()) else "question"

    def _score_for_intent(self, model: ModelInfo, intent: str) -> float:
        # Simple scoring - could be enhanced with ML
        base_score = model.quality_score

        intent_preferences = {
            "code": {"claude", "gpt-4", "gemini-pro"},
            "math": {"gpt-4", "claude"},
            "creative": {"gpt-4", "claude"},
            "analysis": {"gpt-4", "gemini-pro"},
            "question": {"gpt-3.5-turbo", "gemini-flash"},
        }

        preferred = intent_preferences.get(intent, set())
        if any(p in model.name.lower() for p in preferred):
            base_score += 0.2

        return min(1.0, base_score)


class EnsembleStrategy(BaseRoutingStrategy):
    """Route to multiple models and combine results."""

    async def select_model(self, criteria, available_models, context=None):
        # Pick top 3 diverse models
        providers_seen = set()
        diverse_models = []

        for model in sorted(available_models, key=lambda m: -m.quality_score):
            if model.provider not in providers_seen:
                diverse_models.append(model)
                providers_seen.add(model.provider)
                if len(diverse_models) >= 3:
                    break

        if not diverse_models:
            diverse_models = available_models[:1]

        return diverse_models[0], diverse_models[1:]


class LeastLatencyStrategy(BaseRoutingStrategy):
    """Select model with lowest current latency."""

    async def select_model(self, criteria, available_models, context=None):
        # Consider current load and recent latency
        scored = []
        for model in available_models:
            # Effective latency = base + (load * penalty)
            effective_latency = model.avg_latency_ms + (model.current_load * 50)
            scored.append((effective_latency, model))

        scored.sort(key=lambda x: x[0])
        best = scored[0][1]
        fallbacks = [m for _, m in scored[1:4]]

        return best, fallbacks


# ============================================================================
# Model Registry
# ============================================================================


class ModelRegistry:
    """Central registry of all available models."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models = {}
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        # Load from config/env
        self._load_default_models()

    def register(self, model: ModelInfo):
        """Register a model."""
        self._models[model.name] = model

    def get(self, name: str) -> ModelInfo | None:
        """Get model by name."""
        return self._models.get(name)

    def get_all(
        self, provider: str = None, features: list[str] = None, healthy_only: bool = True
    ) -> list[ModelInfo]:
        """Get filtered list of models."""
        models = list(self._models.values())

        if provider:
            models = [m for m in models if m.provider == provider]

        if features:
            for feature in features:
                if feature == "streaming":
                    models = [m for m in models if m.supports_streaming]
                elif feature == "vision":
                    models = [m for m in models if m.supports_vision]
                elif feature == "functions":
                    models = [m for m in models if m.supports_functions]

        if healthy_only:
            models = [m for m in models if m.is_healthy]

        return models

    def update_stats(self, name: str, **stats):
        """Update runtime statistics for a model."""
        model = self._models.get(name)
        if model:
            for key, value in stats.items():
                if hasattr(model, key):
                    setattr(model, key, value)

    def _load_default_models(self):
        """Load default models from environment/config."""
        # These would normally come from config/database
        default_models = [
            ModelInfo(
                name="gpt-4o",
                provider="openai",
                cost_per_1k_tokens=0.005,
                avg_latency_ms=800,
                max_context_length=128000,
                supports_streaming=True,
                supports_functions=True,
                supports_vision=True,
                quality_score=0.95,
            ),
            ModelInfo(
                name="claude-3.5-sonnet",
                provider="anthropic",
                cost_per_1k_tokens=0.003,
                avg_latency_ms=600,
                max_context_length=200000,
                supports_streaming=True,
                supports_functions=True,
                quality_score=0.94,
            ),
            ModelInfo(
                name="gemini-2.5-pro",
                provider="google",
                cost_per_1k_tokens=0.0025,
                avg_latency_ms=400,
                max_context_length=1000000,
                supports_streaming=True,
                supports_functions=True,
                supports_vision=True,
                quality_score=0.92,
            ),
            ModelInfo(
                name="llama-3.1-405b",
                provider="groq",
                cost_per_1k_tokens=0.0002,
                avg_latency_ms=200,
                max_context_length=128000,
                supports_streaming=True,
                quality_score=0.85,
            ),
        ]

        for model in default_models:
            self.register(model)


# ============================================================================
# Main Unified Router
# ============================================================================


class UnifiedRouter:
    """
    SINGLE router to replace ALL 25+ router classes.

    Usage:
        router = get_unified_router()
        decision = await router.route(
            RoutingCriteria(prompt="Hello", task_type="chat")
        )
        logger.info(decision.model.name)  # Best model for this request
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._strategies = {}
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Initialize strategies
        self._strategies = {
            RoutingStrategy.COST_BASED: CostBasedStrategy(),
            RoutingStrategy.PERFORMANCE_BASED: PerformanceBasedStrategy(),
            RoutingStrategy.INTENT_BASED: IntentBasedStrategy(),
            RoutingStrategy.COGNITIVE: IntentBasedStrategy(),  # Reuse for now
            RoutingStrategy.ENSEMBLE: EnsembleStrategy(),
            RoutingStrategy.LEAST_LATENCY: LeastLatencyStrategy(),
        }

        # Initialize registry
        self.registry = ModelRegistry()

        # Default strategy
        self.default_strategy = RoutingStrategy.INTENT_BASED

        self._initialized = True

    async def route(
        self, criteria: RoutingCriteria, strategy: RoutingStrategy = None
    ) -> RoutingDecision:
        """
        Main routing method - replaces all other router.route() methods.

        Args:
            criteria: Routing input parameters
            strategy: Force specific strategy (auto-detect if None)

        Returns:
            RoutingDecision with selected model and fallbacks
        """
        # Auto-detect strategy if not specified
        if strategy is None:
            strategy = await self._detect_best_strategy(criteria)

        # Get available models
        available = self.registry.get_all(features=criteria.required_features, healthy_only=True)

        if not available:
            # Fall back to unhealthy models
            available = self.registry.get_all(
                features=criteria.required_features, healthy_only=False
            )

        if not available:
            raise NoModelsAvailableError("No models available for routing")

        # Execute strategy
        strategy_impl = self._strategies.get(strategy, self._strategies[self.default_strategy])

        selected, fallbacks = await strategy_impl.select_model(
            criteria, available, context={"user_id": criteria.user_id}
        )

        # Calculate estimates
        estimated_cost = self._estimate_cost(criteria.prompt, selected)
        estimated_latency = selected.avg_latency_ms  # Could be more sophisticated

        return RoutingDecision(
            model=selected,
            strategy_used=strategy,
            confidence=self._calculate_confidence(selected, criteria),
            estimated_cost=estimated_cost,
            estimated_latency_ms=estimated_latency,
            fallback_chain=fallbacks,
        )

    async def route_simple(self, prompt: str, task_type: str = "general", **kwargs) -> dict:
        """
        Simplified routing interface - easiest migration path.

        Returns dict compatible with old router APIs.
        """
        criteria = RoutingCriteria(prompt=prompt, task_type=task_type, **kwargs)

        decision = await self.route(criteria)

        return decision.to_dict()

    async def _detect_best_strategy(self, criteria: RoutingCriteria) -> RoutingStrategy:
        """Auto-select strategy based on criteria."""
        if criteria.budget_constraint:
            return RoutingStrategy.COST_BASED
        if criteria.latency_requirement_ms and criteria.latency_requirement_ms < 500:
            return RoutingStrategy.PERFORMANCE_BASED
        if criteria.task_type in ["ensemble", "research"]:
            return RoutingStrategy.ENSEMBLE

        return self.default_strategy

    def _estimate_cost(self, prompt: str, model: ModelInfo) -> float:
        """Estimate cost for this request."""
        # Rough estimation based on token count
        est_tokens = len(prompt.split()) * 1.3  # Rough tokenization
        cost = (est_tokens / 1000) * model.cost_per_1k_tokens
        return round(cost, 6)

    def _calculate_confidence(self, model: ModelInfo, criteria: RoutingCriteria) -> float:
        """Calculate confidence in this routing decision."""
        confidence = model.quality_score

        # Adjust for health
        if not model.is_healthy:
            confidence *= 0.5

        # Adjust for load
        if model.current_load > 10:
            confidence *= 0.8

        # Adjust for success rate
        confidence *= model.success_rate

        return round(min(1.0, confidence), 2)


# ============================================================================
# Singleton & Convenience
# ============================================================================


def get_unified_router() -> UnifiedRouter:
    """Get global unified router instance."""
    return UnifiedRouter()


# Short alias
router = get_unified_router()


# ============================================================================
# Exceptions
# ============================================================================


class NoModelsAvailableError(Exception):
    """Raised when no models are available for routing."""

    pass


# ============================================================================
# BACKWARD COMPATIBILITY WRAPPERS
# ============================================================================

# These allow gradual migration without breaking existing code:


class ModelRouter:
    """Wrapper around UnifiedRouter for brain/model_router.py compatibility."""

    def __init__(self):
        self._real = get_unified_router()

    async def route_and_generate(self, prompt, task_type="general", **kwargs):
        """Old API compatibility."""
        decision = await self._real.route(
            RoutingCriteria(prompt=prompt, task_type=task_type, **kwargs)
        )
        return {
            "model_name": decision.model.name,
            "provider": decision.model.provider,
            "confidence": decision.confidence,
            "fallback_chain": [m.name for m in decision.fallback_chain],
        }


class SmartRouter:
    """Wrapper for services/smart_model_router.py compatibility."""

    def __init__(self):
        self._real = get_unified_router()

    async def route(self, query, task_type="general", **kwargs):
        """Old API compatibility."""
        return await self._real.route_simple(query, task_type, **kwargs)


class PerformanceAwareRouter:
    """Wrapper for brain/performance_aware_router.py compatibility."""

    def __init__(self):
        self._real = get_unified_router()

    async def route_with_performance(self, prompt, **kwargs):
        """Old API compatibility - forces performance strategy."""
        decision = await self._real.route(
            RoutingCriteria(prompt=prompt, **kwargs), strategy=RoutingStrategy.PERFORMANCE_BASED
        )
        return decision.to_dict()


# Add more wrappers as needed for other router classes...
