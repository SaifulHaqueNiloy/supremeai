# backend/__init__.py
"""SupremeAI Master Package.

Living, Self-Evolving Autonomous AI Engine.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

try:
    from core.config import settings
    from core.factory import SupremeAIFactory, get_ai, get_factory
    from core.integration_layer import SupremeAIIntegrator, get_integrator
except ImportError:
    try:
        from backend.core.config import settings
        from backend.core.factory import SupremeAIFactory, get_ai, get_factory
        from backend.core.integration_layer import SupremeAIIntegrator, get_integrator
    except ImportError:
        # Gracefully handle missing dependencies (e.g. when Pytest crawls this from microservices)
        SupremeAIFactory = None
        SupremeAIIntegrator = None
        get_ai = None
        get_factory = None
        get_integrator = None
        settings = None

__version__ = "4.2.0-wired"
__all__ = [
    "SupremeAIFactory",
    "SupremeAIIntegrator",
    "get_ai",
    "get_factory",
    "get_integrator",
    "settings",
]
