"""Canonical Context Engine (M2) — smallest-sufficient-context assembly.

Doctrine (roadmap M2): NO new context database. This package assembles
context over the EXISTING Files/Memory/RAG surfaces with:

- :mod:`context.scopes` — scope chain GLOBAL→USER→WORKSPACE→PROJECT→CHAT→
  RUN→STEP (RUN/STEP anchored to M1's canonical ``run_id``);
- :mod:`context.items` — ContextItem + immutable Provenance (every item is
  auditable; tenant identity is part of provenance);
- :mod:`context.budget` — token budgeter on the canonical estimator
  (:func:`core.llm.token_budget.estimate_tokens`), drop-report honest;
- :mod:`context.engine` — ContextEngine: injectable source adapters over
  the existing retrieval surfaces, deny-by-default tenant filter,
  cross-source hash dedup, deterministic rendering.

Source adapters for the production surfaces (memory recall, chat
attachment files, RAG/vector stores) land in the integration slice (M2-C);
this package is the pure, offline-testable core.
"""


from context.budget import BudgetReport, ContextBudget, pack_items
from context.engine import ContextBundle, ContextEngine, RawCandidate, render_bundle
from context.items import ContextItem, ItemKind, Provenance, SummaryLevel
from context.scopes import (
    SCOPE_ORDER,
    Scope,
    ScopeChainError,
    ScopeLevel,
    scope_distance,
    scope_match_score,
    validate_scope,
)

__all__ = [
    "BudgetReport",
    "ContextBudget",
    "pack_items",
    "ContextBundle",
    "ContextEngine",
    "RawCandidate",
    "render_bundle",
    "ContextItem",
    "ItemKind",
    "Provenance",
    "SummaryLevel",
    "SCOPE_ORDER",
    "Scope",
    "ScopeChainError",
    "ScopeLevel",
    "scope_distance",
    "scope_match_score",
    "validate_scope",
]
