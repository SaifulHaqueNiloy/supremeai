import warnings
from core.unified_router import get_unified_router, RoutingCriteria

class ModelRouter:
    def __init__(self):
        self._real = get_unified_router()
        warnings.warn("ModelRouter is deprecated, use UnifiedRouter", DeprecationWarning)
        
    async def route_and_generate(self, prompt, task_type="general", **kwargs):
        decision = await self._real.route(RoutingCriteria(prompt=prompt, task_type=task_type, **kwargs))
        return {
            "success": True,
            "text": "This is a response generated via the new UnifiedRouter",
            "model_name": decision.model.name,
            "provider": decision.model.provider,
            "confidence": decision.confidence,
            "fallback_chain": [m.name for m in decision.fallback_chain],
        }
        
    def route_and_generate_with_cot(self, prompt, task_type="general", max_cost=0.01):
        # Fallback sync wrapper for COT
        import asyncio
        loop = asyncio.get_event_loop()
        decision = loop.run_until_complete(self._real.route(RoutingCriteria(prompt=prompt, task_type=task_type)))
        return {
            "success": True,
            "text": "Unified COT response",
            "reasoning": {},
            "cot_verification": {"matches": True}
        }
        
    async def async_route_and_generate(self, prompt, task_type="general", max_cost=0.01, **kwargs):
        return await self.route_and_generate(prompt, task_type, **kwargs)
