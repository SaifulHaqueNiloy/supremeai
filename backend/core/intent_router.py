"""Intent Router — legacy shim module.

This module historically defined PromptAction and ACTION_PATTERNS, but those
were moved to core/intent_router_v2.py (canonical location) during the
Router Consolidation refactor. They are re-exported here for backwards
compatibility with any code that still imports from core.intent_router.
"""

import warnings

# Re-export PromptAction and ACTION_PATTERNS from the canonical v2 location
# so legacy imports like `from core.intent_router import PromptAction` keep working.
from core.intent_router_v2 import ACTION_PATTERNS, PromptAction  # noqa: F401

# IntentRouter class delegates to UnifiedRouter (the new canonical router).
try:
    from core.unified_router import RoutingCriteria, RoutingStrategy, get_unified_router

    class IntentRouter:
        def __init__(self):
            self._real = get_unified_router()
            warnings.warn("IntentRouter is deprecated, use UnifiedRouter", DeprecationWarning)

        async def route_by_intent(self, user_intent, **kwargs):
            decision = await self._real.route(
                RoutingCriteria(prompt=user_intent, **kwargs),
                strategy=RoutingStrategy.INTENT_BASED,
            )
            return decision.to_dict()
except ImportError:
    # UnifiedRouter not yet available — leave IntentRouter undefined.
    # Callers should use core.intent_router_v2.intent_router_v2 instead.
    pass


__all__ = ["ACTION_PATTERNS", "PromptAction", "IntentRouter"]
