"""Persistent Learning Store package (Sprint 2, Self-Evolution Zero-Cost plan).

Public surface for later sprints:

    from core.learning import get_learning_store, record_llm_event

NOTE: this package is deliberately NOT wired into ``core/llm/llm_gateway.py``
yet — gateway integration is owned by a later sprint. The singleton is
returned un-started; callers (or app lifespan) may ``start()``/``stop()`` it.
"""

from __future__ import annotations

from .store import (
    ALLOWED_FEEDBACK_TYPES,
    LEARNING_EVENT_FIELDS,
    LearningEvent,
    LearningStore,
    aggregate_provider_metrics,
    get_learning_store,
    record_feedback,
    record_llm_event,
    sanitize_metadata,
)

__all__ = [
    "ALLOWED_FEEDBACK_TYPES",
    "LEARNING_EVENT_FIELDS",
    "LearningEvent",
    "LearningStore",
    "aggregate_provider_metrics",
    "get_learning_store",
    "record_feedback",
    "record_llm_event",
    "sanitize_metadata",
]
