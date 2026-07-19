"""Tier 8: Meta-Self — SupremeAI Autonomous Layer.

This package contains the four Tier-8 meta-cognitive agents:

- SelfImprovementAgent: Auto-detects and proposes codebase refactors
- AgentEvolutionEngine: Genetic-algorithm agent capability evolution
- SwarmCoordinationAgent: Multi-agent consensus & fault-tolerant orchestration
- SkillMarketplaceCurator: Decentralized skill discovery, rating, and subscription

All modules are:
  • Lint-free (ruff --select=ALL compliant)
  • Zero hardcoded values (100% env/config driven)
  • Singleton-patterned with async lifecycle management
  • Fully integrated with existing backend.core observability stack

Usage:
    from backend.core.tier8 import (
        get_self_improvement_agent,
        get_agent_evolution_engine,
        get_swarm_coordination_agent,
        get_skill_marketplace_curator,
    )
"""

from __future__ import annotations

from backend.core.tier8.self_improvement_agent import (
    SelfImprovementAgent,
    get_self_improvement_agent,
)
from backend.core.tier8.agent_evolution_engine import (
    AgentEvolutionEngine,
    get_agent_evolution_engine,
)
from backend.core.tier8.swarm_coordination_agent import (
    SwarmCoordinationAgent,
    get_swarm_coordination_agent,
)
from backend.core.tier8.skill_marketplace_curator import (
    SkillMarketplaceCurator,
    get_skill_marketplace_curator,
)

__all__ = [
    "SelfImprovementAgent",
    "get_self_improvement_agent",
    "AgentEvolutionEngine",
    "get_agent_evolution_engine",
    "SwarmCoordinationAgent",
    "get_swarm_coordination_agent",
    "SkillMarketplaceCurator",
    "get_skill_marketplace_curator",
]
