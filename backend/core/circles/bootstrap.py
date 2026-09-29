"""Federation bootstrap — wires circle centers into the GovernanceCore.

The FCC construction rule: the Global Governance Core stays domain-free;
ONLY this module knows both the core and the concrete centers.
"""

import threading
from collections.abc import Iterable

from core.circles.centers import CircleCenter, build_default_centers
from core.circles.centers.realtime_center import RealtimeCenter
from core.circles.contracts import CircleManifest, CircleName
from core.circles.governance_core import GovernanceCore, PolicyEvaluator
from core.circles.manifests import default_manifests
from core.circles.registry import CircleRegistry


def build_circle_registry(manifests: Iterable[CircleManifest] | None = None) -> CircleRegistry:
    """Legacy flat registry (pre-FCC compatibility surface)."""
    registry = CircleRegistry()
    for manifest in manifests or default_manifests():
        registry.register(manifest)
    return registry


def build_federation(
    policy_evaluator: PolicyEvaluator | None = None,
    centers: Iterable[CircleCenter] | None = None,
) -> GovernanceCore:
    """Construct the federated control plane:

    1. one instance of every default circle center,
    2. the Global Governance Core routing between them,
    3. realtime sync: every execution event is mirrored into the
       Realtime Circle (zero-infrastructure event bus).
    """
    built = tuple(centers) if centers is not None else build_default_centers()
    core = GovernanceCore(policy_evaluator=policy_evaluator)

    realtime: RealtimeCenter | None = None
    for center in built:
        core.register_center(center)
        if isinstance(center, RealtimeCenter):
            realtime = center
    if realtime is not None:
        core.subscribe(realtime.receive)
    return core


# ── process-wide federation singleton (moved from governance_core) ─────────
# Issue #2476: singleton factory আগে governance_core.py-তে ছিল, যেখান থেকে
# এই composition-root-কে lazily import করত — সেই উল্টো edge-টিই ছিল
# bootstrap ↔ governance_core static cycle-এর দ্বিতীয় ধার। FCC নিয়ম অনুযায়ী
# "core ও centers দুজনকেই চেনে" একমাত্র এই মডিউলই — তাই process-wide
# get_governance_core() এখানেই থাকা স্থাপত্যগতভাবে সঠিক; এখন নির্ভরতা
# সম্পূর্ণ একমুখী: callers → bootstrap → governance_core।
_governance_core: GovernanceCore | None = None
_governance_lock = threading.Lock()


def get_governance_core() -> GovernanceCore:
    """Process-wide GovernanceCore; wired with all default centers once."""
    global _governance_core
    if _governance_core is None:
        with _governance_lock:
            if _governance_core is None:
                _governance_core = build_federation()
    return _governance_core


def reset_governance_core() -> None:
    """Test helper: drop the singleton so the next access rebuilds."""
    global _governance_core
    with _governance_lock:
        _governance_core = None


__all__ = [
    "build_circle_registry",
    "build_federation",
    "get_governance_core",
    "reset_governance_core",
]
