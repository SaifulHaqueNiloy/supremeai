import asyncio
import unittest

from core.circles import (
    CapabilityRef,
    CapabilityRequest,
    CircleManifest,
    CircleName,
    CircleRegistry,
    ExecutionContext,
    ExecutionStatus,
    RiskLevel,
)


class CircleRegistryTests(unittest.TestCase):
    def test_dispatches_through_circle_center(self) -> None:
        registry = CircleRegistry()
        capability = CapabilityRef(
            name="memory.recall",
            owner_circle=CircleName.MEMORY,
            risk_level=RiskLevel.LOW,
        )
        registry.register(
            CircleManifest(
                name=CircleName.MEMORY,
                display_name="Memory",
                owner="memory-team",
                capabilities=(capability,),
            )
        )
        registry.register_handler("memory.recall", lambda request: {"count": 1})
        request = CapabilityRequest(
            capability=capability,
            context=ExecutionContext(actor_id="user-1", tenant_id="tenant-1"),
        )

        result = asyncio.run(registry.dispatch(request))

        self.assertEqual(result.status, ExecutionStatus.SUCCEEDED)
        self.assertEqual(result.data, {"count": 1})
        self.assertEqual(len(registry.events()), 1)

    def test_default_manifests_are_unique_and_discoverable(self) -> None:
        from core.circles import build_circle_registry

        registry = build_circle_registry()
        self.assertEqual(len(registry.manifests()), 10)
        self.assertIn("memory.recall", registry.manifests()[2].model_dump_json())

    def test_unregistered_capability_is_explicitly_unavailable(self) -> None:
        registry = CircleRegistry()
        capability = CapabilityRef(name="browser.open", owner_circle=CircleName.BROWSER)
        request = CapabilityRequest(
            capability=capability,
            context=ExecutionContext(actor_id="user-1", tenant_id="tenant-1"),
        )

        result = asyncio.run(registry.dispatch(request))

        self.assertEqual(result.status, ExecutionStatus.UNAVAILABLE)
        self.assertEqual(result.error_code, "capability_not_registered")
        self.assertEqual(registry.events(), ())


if __name__ == "__main__":
    unittest.main()
