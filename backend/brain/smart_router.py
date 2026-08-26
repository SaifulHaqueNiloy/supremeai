import warnings
from core.unified_router import get_unified_router, RoutingCriteria, RoutingStrategy

class SelfSovereignRouter:
    def __init__(self):
        self._real = get_unified_router()
        warnings.warn("SelfSovereignRouter is deprecated, use UnifiedRouter", DeprecationWarning)
        
    async def route(self, prompt, **kwargs):
        decision = await self._real.route(
            RoutingCriteria(prompt=prompt, **kwargs),
            strategy=RoutingStrategy.SOVEREIGN
        )
        return decision.to_dict()
