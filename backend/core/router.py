import warnings

from core.unified_router import RoutingCriteria, get_unified_router


class AutonomousProviderRouter:
    def __init__(self):
        self._real = get_unified_router()
        warnings.warn(
            "AutonomousProviderRouter is deprecated, use UnifiedRouter", DeprecationWarning
        )

    async def select_provider(self, prompt, **kwargs):
        decision = await self._real.route(RoutingCriteria(prompt=prompt, **kwargs))
        return decision.model.provider
