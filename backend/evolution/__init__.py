# backend/evolution/__init__.py
"""Evolution module for SupremeAI.

Provides:
- CostGuard: Distributed Redis-based budget tracking
- AutoSkillCreator: Safe AI-generated skill creation with AST validation
- EvolutionEngine: Event-driven self-healing system
"""

from __future__ import annotations

from evolution.auto_skill_creator import AutoSkillCreator, MaliciousCodeError, SecuritySandbox, SkillExecutionError
from evolution.cost_guard import BudgetExceededError, CostGuard, cost_guard
from evolution.evolution_engine import EvolutionEngine, evolution_engine

__all__ = [
    "CostGuard",
    "cost_guard",
    "BudgetExceededError",
    "AutoSkillCreator",
    "SecuritySandbox",
    "MaliciousCodeError",
    "SkillExecutionError",
    "EvolutionEngine",
    "evolution_engine",
]
