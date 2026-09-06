from collections.abc import Iterable

from .contracts import CircleManifest
from .manifests import default_manifests
from .registry import CircleRegistry


def build_circle_registry(manifests: Iterable[CircleManifest] | None = None) -> CircleRegistry:
    registry = CircleRegistry()
    for manifest in manifests or default_manifests():
        registry.register(manifest)
    return registry
