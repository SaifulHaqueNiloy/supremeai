"""backend/core/circles/evolution/__init__.py — Evolution Circle Boundary Facade.

Governs:
- Dynamic learning, Self-healing, Adaptive experience, Skills mutation
"""


from core.circles.contracts import CircleName


class EvolutionCircleFacade:
    """Bounded facade for Evolution operations."""

    name = CircleName.EVOLUTION


evolution_circle = EvolutionCircleFacade()
