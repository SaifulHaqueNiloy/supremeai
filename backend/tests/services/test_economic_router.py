"""DEPRECATED test — SmartRouter was refactored away in Phase 1 Router
Consolidation. The new canonical router is core.unified_router.UnifiedRouter.

This test imports ModelTier + SmartRouter from services.smart_model_router,
but that module is now a thin shim that only exports SmartRouter (deprecated,
delegates to UnifiedRouter). ModelTier no longer exists.

The test logic also assumes an API that no longer matches (e.g.
router.route() returning .selected_model.tier — that was the OLD SmartRouter
interface pre-consolidation).

Skipping this test until a new economic-router test is written against the
canonical EconomicRouter class in core/optimization/economic_optimizer.py.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="SmartRouter refactored away — ModelTier no longer exported. "
    "Rewrite test against core.optimization.economic_optimizer.EconomicRouter"
)


def test_placeholder():
    pass
