import warnings
from core.unified_router import get_unified_router, RoutingCriteria, RoutingStrategy

class IntentRouter:
    def __init__(self):
        self._real = get_unified_router()
        warnings.warn("IntentRouter is deprecated, use UnifiedRouter", DeprecationWarning)
        
    async def route_by_intent(self, user_intent, **kwargs):
        decision = await self._real.route(
            RoutingCriteria(prompt=user_intent, **kwargs),
            strategy=RoutingStrategy.INTENT_BASED
        )
        return decision.to_dict()
