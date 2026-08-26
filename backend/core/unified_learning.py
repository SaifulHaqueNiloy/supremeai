"""
================================================================================
PATCH 05: Unified Learning Engine Implementation
================================================================================

This patch consolidates 8+ learning engine implementations into a single
UnifiedLearningEngine.

INSTRUCTIONS:
1. Create file: backend/core/unified_learning.py
2. Update imports in all files that use old learning engines
3. Keep old engines as deprecated wrappers during transition

ESTIMATED IMPACT:
- Reduces ~2,500 lines of learning code to ~600 lines
- Single knowledge base shared across all components
- Consistent learning behavior across entire application
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional

# ============================================================================
# Core Types
# ============================================================================


class LearningType(Enum):
    """Types of learning."""

    PATTERN_RECOGNITION = "pattern_recognition"
    USER_PREFERENCE = "user_preference"
    ERROR_CORRECTION = "error_correction"
    PERFORMANCE_OPTIMIZATION = "performance"
    FEDERATED_AGGREGATION = "federated"
    FEEDBACK = "feedback"


@dataclass
class LearningEvent:
    """Unified learning event."""

    event_type: LearningType
    source: str  # Where it came from (chat, task, etc.)
    input_data: str
    output_data: str

    # Context
    user_id: str | None = None
    session_id: str | None = None
    model_used: str | None = None
    task_type: str | None = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    # Quality signal
    success: bool = True
    quality_score: float = 0.5  # 0-1, how good is this learning example?

    def get_key(self) -> str:
        """Generate unique key for deduplication."""
        content = f"{self.event_type.value}:{self.input_data[:200]}:{self.output_data[:200]}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class KnowledgeNode:
    """Single piece of learned knowledge."""

    id: str
    pattern: str  # Input pattern (what triggers this knowledge)
    outcome: str  # Learned outcome (what to do/response)

    # Quality metrics
    confidence: float = 0.5  # 0-1, how confident are we?
    usage_count: int = 0  # How many times used
    success_count: int = 0  # How many times successful

    # Classification
    learning_type: LearningType = LearningType.PATTERN_RECOGNITION
    tags: list[str] = field(default_factory=list)

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: datetime | None = None
    last_updated: datetime = field(default_factory=datetime.utcnow)

    # Source tracking
    source_events: list[str] = field(default_factory=list)  # IDs of events that contributed

    @property
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return self.confidence
        return self.success_count / self.usage_count


@dataclass
class LearningQuery:
    """Query for retrieving learned knowledge."""

    query_text: str
    max_results: int = 5
    min_confidence: float = 0.3
    learning_types: list[LearningType] = None
    user_id: str | None = None
    tags: list[str] = None
    include_expired: bool = False


@dataclass
class LearningStats:
    """Learning system statistics."""

    total_knowledge_nodes: int = 0
    total_learning_events: int = 0
    events_by_type: dict[str, int] = field(default_factory=dict)
    knowledge_by_type: dict[str, int] = field(default_factory=dict)
    avg_confidence: float = 0.0
    cache_hit_rate: float = 0.0


# ============================================================================
# Strategy Interface & Implementations
# ============================================================================


class BaseLearningStrategy(ABC):
    """Base class for learning strategies."""

    @abstractmethod
    async def learn(
        self, event: LearningEvent, existing_knowledge: KnowledgeNode | None
    ) -> KnowledgeNode | None:
        """
        Process learning event and produce/update knowledge.

        Returns: Updated or new KnowledgeNode, or None if nothing to learn.
        """
        pass

    @abstractmethod
    async def should_learn(self, event: LearningEvent) -> bool:
        """Determine if this event is worth learning from."""
        pass


class PatternRecognitionStrategy(BaseLearningStrategy):
    """Learn from patterns in input/output pairs."""

    async def should_learn(self, event: LearningEvent) -> bool:
        # Don't learn from errors
        if not event.success:
            return False

        # Must have substantial content
        if len(event.input_data) < 10 or len(event.output_data) < 10:
            return False

        # High quality examples are always worth learning
        if event.quality_score >= 0.7:
            return True

        # Otherwise, learn randomly (explore)
        import random

        return random.random() > 0.5

    async def learn(
        self, event: LearningEvent, existing_knowledge: KnowledgeNode | None
    ) -> KnowledgeNode | None:
        if not await self.should_learn(event):
            return None

        if existing_knowledge:
            # Update existing knowledge
            existing_knowledge.success_count += 1
            existing_knowledge.usage_count += 1
            existing_knowledge.last_used = datetime.utcnow()
            existing_knowledge.last_updated = datetime.utcnow()

            # Increase confidence with more evidence
            alpha = 0.3  # Learning rate
            existing_knowledge.confidence = (
                existing_knowledge.confidence * (1 - alpha) + event.quality_score * alpha
            )

            if event.source not in existing_knowledge.source_events:
                existing_knowledge.source_events.append(event.source)

            return existing_knowledge
        else:
            # Create new knowledge node
            return KnowledgeNode(
                id=event.get_key(),
                pattern=event.input_data,
                outcome=event.output_data,
                confidence=event.quality_score,
                usage_count=1,
                success_count=1 if event.success else 0,
                learning_type=LearningType.PATTERN_RECOGNITION,
                source_events=[event.source],
                tags=self._extract_tags(event),
            )

    def _extract_tags(self, event: LearningEvent) -> list[str]:
        """Extract useful tags from event."""
        tags = [event.task_type or "general"]

        if event.user_id:
            tags.append(f"user:{event.user_id}")
        if event.model_used:
            tags.append(f"model:{event.model_used}")

        return tags


class UserPreferenceStrategy(BaseLearningStrategy):
    """Learn user preferences from interactions."""

    async def should_learn(self, event: LearningEvent) -> bool:
        return event.event_type == LearningType.USER_PREFERENCE and event.user_id is not None

    async def learn(
        self, event: LearningEvent, existing_knowledge: KnowledgeNode | None
    ) -> KnowledgeNode | None:
        if not await self.should_learn(event):
            return None

        preference_key = f"pref:{event.user_id}"

        if existing_knowledge:
            # Merge preferences
            try:
                existing_prefs = json.loads(existing_knowledge.outcome)
                new_prefs = json.loads(event.output_data)

                merged = {**existing_prefs, **new_prefs}
                existing_knowledge.outcome = json.dumps(merged)
                existing_knowledge.last_updated = datetime.utcnow()

                return existing_knowledge
            except json.JSONDecodeError:
                # If merge fails, just update
                existing_knowledge.outcome = event.output_data
                return existing_knowledge
        else:
            return KnowledgeNode(
                id=preference_key,
                pattern=f"user_preferences:{event.user_id}",
                outcome=event.output_data,
                confidence=0.8,
                learning_type=LearningType.USER_PREFERENCE,
                tags=["preference", f"user:{event.user_id}"],
            )


class ErrorCorrectionStrategy(BaseLearningStrategy):
    """Learn from errors to avoid repeating them."""

    async def should_learn(self, event: LearningEvent) -> bool:
        return not event.success and event.event_type in [
            LearningType.ERROR_CORRECTION,
            LearningType.FEEDBACK,
        ]

    async def learn(
        self, event: LearningEvent, existing_knowledge: KnowledgeNode | None
    ) -> KnowledgeNode | None:
        if not await self.should_learn(event):
            return None

        error_pattern = f"error:{hashlib.sha256(event.input_data.encode()).hexdigest()[:12]}"

        # Store what NOT to do, or what to do instead
        correction = event.output_data  # Should contain the correction/solution

        if existing_knowledge:
            existing_knowledge.usage_count += 1
            existing_knowledge.last_updated = datetime.utcnow()
            return existing_knowledge
        else:
            return KnowledgeNode(
                id=error_pattern,
                pattern=event.input_data,
                outcome=correction,
                confidence=0.7,  # Start confident since we explicitly learned from error
                learning_type=LearningType.ERROR_CORRECTION,
                tags=["error_correction", "avoid"],
            )


# ============================================================================
# Main Unified Learning Engine
# ============================================================================


class UnifiedLearningEngine:
    """
    SINGLE learning engine to replace ALL 8+ implementations.

    Features:
    - Single unified knowledge base
    - Multiple learning strategies working together
    - Deduplication of similar learnings
    - Confidence-based knowledge retrieval
    - Persistence support
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
            LearningType.PATTERN_RECOGNITION: PatternRecognitionStrategy(),
            LearningType.USER_PREFERENCE: UserPreferenceStrategy(),
            LearningType.ERROR_CORRECTION: ErrorCorrectionStrategy(),
        }

        # Knowledge storage (in-memory for now, can be persisted)
        self.knowledge_base: dict[str, KnowledgeNode] = {}

        # Pattern index for fast lookup
        self.pattern_index: dict[str, str] = {}  # pattern_hash → knowledge_id

        # Statistics
        self._total_events = 0
        self._events_by_type: dict[str, int] = {}

        self._initialized = True

    async def learn(self, event: LearningEvent) -> KnowledgeNode | None:
        """
        Main learning entry point - replaces all other learn_* methods.

        Args:
            event: The learning event to process

        Returns:
            KnowledgeNode that was created/updated, or None if nothing learned
        """
        self._total_events += 1
        type_name = event.event_type.value
        self._events_by_type[type_name] = self._events_by_type.get(type_name, 0) + 1

        # Get appropriate strategy
        strategy = self._strategies.get(event.event_type)
        if not strategy:
            # Default to pattern recognition
            strategy = self._strategies[LearningType.PATTERN_RECOGNITION]

        # Check for existing similar knowledge
        existing = await self._find_similar(event)

        # Apply learning strategy
        knowledge = await strategy.learn(event, existing)

        if knowledge:
            # Store in knowledge base
            self.knowledge_base[knowledge.id] = knowledge

            # Update pattern index
            pattern_hash = hashlib.sha256(knowledge.pattern.encode()).hexdigest()[:16]
            self.pattern_index[pattern_hash] = knowledge.id

            # Persist (if configured)
            await self._persist(knowledge)

        return knowledge

    async def recall(self, query: LearningQuery) -> list[KnowledgeNode]:
        """
        Recall relevant knowledge - replaces all other recall/get_context methods.

        Args:
            query: Query parameters

        Returns:
            List of relevant KnowledgeNodes, sorted by relevance
        """
        candidates = []

        # Search by exact pattern match first
        query_hash = hashlib.sha256(query.query_text.encode()).hexdigest()[:16]
        if query_hash in self.pattern_index:
            k_id = self.pattern_index[query_hash]
            node = self.knowledge_base.get(k_id)
            if node and node.confidence >= query.min_confidence:
                candidates.append(node)

        # Search by substring/keyword matching
        query_lower = query.query_text.lower()
        for node in self.knowledge_base.values():
            if node.id in [c.id for c in candidates]:
                continue

            # Check type filter
            if query.learning_types and node.learning_type not in query.learning_types:
                continue

            # Check confidence
            if node.confidence < query.min_confidence:
                continue

            # Simple keyword matching (could be vector similarity in production)
            if query_lower in node.pattern.lower() or any(
                word in node.pattern.lower() for word in query_lower.split()[:3]
            ):
                candidates.append(node)

        # Sort by confidence * recency
        candidates.sort(
            key=lambda n: (
                n.confidence
                * (
                    1 / (1 + (datetime.utcnow() - n.last_updated).total_seconds() / 86400)
                )  # Time decay
            ),
            reverse=True,
        )

        # Update usage stats
        for node in candidates[: query.max_results]:
            node.usage_count += 1
            node.last_used = datetime.utcnow()

        return candidates[: query.max_results]

    async def learn_from_chat(
        self, prompt: str, response: str, user_id: str = None, session_id: str = None, **kwargs
    ) -> KnowledgeNode | None:
        """
        Convenience method for learning from chat interactions.

        Replaces SupremeLearningEngine.process_chat_message() and similar methods.
        """
        event = LearningEvent(
            event_type=LearningType.PATTERN_RECOGNITION,
            source="chat",
            input_data=prompt,
            output_data=response,
            user_id=user_id,
            session_id=session_id,
            task_type="chat",
            **kwargs,
        )

        return await self.learn(event)

    async def learn_from_error(
        self, error_input: str, error_output: str, correction: str, **kwargs
    ) -> KnowledgeNode | None:
        """
        Convenience method for learning from errors.
        """
        event = LearningEvent(
            event_type=LearningType.ERROR_CORRECTION,
            source="error_handler",
            input_data=error_input,
            output_data=correction,  # Store the correction, not the error
            success=False,
            metadata={"original_error": error_output},
            **kwargs,
        )

        return await self.learn(event)

    async def learn_user_preference(
        self, user_id: str, preference_key: str, preference_value: Any, **kwargs
    ) -> KnowledgeNode | None:
        """
        Convenience method for learning user preferences.
        """
        import json

        event = LearningEvent(
            event_type=LearningType.USER_PREFERENCE,
            source="user_interaction",
            input_data=f"preference:{user_id}:{preference_key}",
            output_data=json.dumps({preference_key: preference_value}),
            user_id=user_id,
            **kwargs,
        )

        return await self.learn(event)

    async def get_user_context(self, user_id: str, limit: int = 20) -> list[KnowledgeNode]:
        """
        Get all learned context for a user.

        Replaces various get_user_memory/get_preferences methods.
        """

        results = []
        for node in self.knowledge_base.values():
            if user_id in node.tags:
                results.append(node)

        # Sort by recency
        results.sort(key=lambda n: n.last_updated, reverse=True)

        return results[:limit]

    async def get_stats(self) -> LearningStats:
        """Get learning statistics."""
        by_type = {}
        for node in self.knowledge_base.values():
            type_name = node.learning_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        total_confidence = sum(n.confidence for n in self.knowledge_base.values())
        avg_confidence = total_confidence / len(self.knowledge_base) if self.knowledge_base else 0

        return LearningStats(
            total_knowledge_nodes=len(self.knowledge_base),
            total_learning_events=self._total_events,
            events_by_type=dict(self._events_by_type),
            knowledge_by_type=by_type,
            avg_confidence=round(avg_confidence, 3),
        )

    async def _find_similar(self, event: LearningEvent) -> KnowledgeNode | None:
        """Find existing similar knowledge."""
        event_key = event.get_key()

        # Exact key match
        if event_key in self.knowledge_base:
            return self.knowledge_base[event_key]

        # Similarity search (simplified - would use embeddings in production)
        event_hash = hashlib.sha256(event.input_data.encode()).hexdigest()[:12]
        if event_hash in self.pattern_index:
            return self.knowledge_base[self.pattern_index[event_hash]]

        return None

    async def _persist(self, knowledge: KnowledgeNode):
        """Persist knowledge to storage (optional)."""
        # Would save to database/vector store here
        pass

    async def load_persisted(self):
        """Load persisted knowledge into memory."""
        # Would load from database/vector store here
        pass


# ============================================================================
# Singleton & Convenience
# ============================================================================

_unified_learning_engine: UnifiedLearningEngine | None = None


def get_learning_engine() -> UnifiedLearningEngine:
    """Get global learning engine instance."""
    global _unified_learning_engine
    if _unified_learning_engine is None:
        _unified_learning_engine = UnifiedLearningEngine()
    return _unified_learning_engine


# Short alias
learning = get_learning_engine()


# ============================================================================
# BACKWARD COMPATIBILITY WRAPPERS
# ============================================================================


class SupremeLearningEngine:
    """Wrapper around UnifiedLearningEngine for brain/supreme_learning_engine.py compatibility."""

    def __init__(self):
        self._real = get_learning_engine()

    async def process_chat_message(self, query, user_id=None, **kwargs):
        """Old API compatibility."""
        context = await self._real.recall(
            LearningQuery(query_text=query, user_id=user_id, max_results=5)
        )

        if context:
            best = context[0]
            return {
                "response": best.outcome,
                "confidence": best.confidence,
                "was_self_sufficient": best.confidence > 0.7,
            }

        return {"response": None, "confidence": 0, "was_self_sufficient": False}

    async def learn_from_chat_response(self, conversation, response, **kwargs):
        """Old API compatibility."""
        if isinstance(conversation, list):
            prompt = conversation[-1].get("content", "") if conversation else ""
        else:
            prompt = str(conversation)

        return await self._real.learn_from_chat(prompt, response, **kwargs)


class LearningEngine:
    """Wrapper for services/dynamic_ai/learning_engine.py compatibility."""

    def __init__(self):
        self._real = get_learning_engine()

    async def observe_and_learn(self, input_data, output_data, **kwargs):
        """Old API compatibility."""
        event = LearningEvent(
            event_type=LearningType.PATTERN_RECOGNITION,
            source="dynamic_ai",
            input_data=str(input_data),
            output_data=str(output_data),
            **kwargs,
        )
        return await self._real.learn(event)


# More wrappers as needed...
