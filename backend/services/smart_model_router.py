import warnings
from core.unified_router import get_unified_router, RoutingCriteria

class SmartRouter:
    def __init__(self):
        self._real = get_unified_router()
        warnings.warn("SmartRouter is deprecated, use UnifiedRouter", DeprecationWarning)
        
    async def route(self, query, task_type="general", **kwargs):
        decision = await self._real.route(RoutingCriteria(prompt=query, task_type=task_type, **kwargs))
        return decision.to_dict()
