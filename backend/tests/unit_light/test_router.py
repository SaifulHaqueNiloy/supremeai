import warnings
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.router import AutonomousProviderRouter


def test_init_emits_deprecation_warning():
    fake_router = MagicMock()
    with (
        patch("core.router.get_unified_router", return_value=fake_router),
        pytest.warns(DeprecationWarning),
    ):
        AutonomousProviderRouter()


@pytest.mark.asyncio
async def test_select_provider_delegates_to_unified_router():
    from types import SimpleNamespace

    fake_router = MagicMock()
    decision = SimpleNamespace(model=SimpleNamespace(provider="openai"))
    fake_router.route = AsyncMock(return_value=decision)

    with patch("core.router.get_unified_router", return_value=fake_router):
        router = AutonomousProviderRouter()
        provider = await router.select_provider("hello world", preferred_provider="openai")

    fake_router.route.assert_awaited_once()
    criteria = fake_router.route.call_args.args[0]
    assert criteria.prompt == "hello world"
    assert criteria.preferred_provider == "openai"
    assert provider == "openai"
