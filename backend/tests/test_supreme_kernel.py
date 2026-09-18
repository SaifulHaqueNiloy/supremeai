import pytest

from core.kernel.dispatcher import SupremeKernel
from core.kernel.interface import CircleScope, ExecutionMode, KernelRequest


@pytest.mark.asyncio
async def test_supreme_kernel_dispatch_unregistered():
    kernel = SupremeKernel()
    req = KernelRequest(
        target_circle=CircleScope.EXECUTION,
        capability="non_existent.test_action",
        mode=ExecutionMode.SYNC,
        actor_id="test_actor",
        tenant_id="test_tenant",
    )
    res = await kernel.dispatch(req)
    assert res.request_id == req.request_id
    assert res.target_circle == CircleScope.EXECUTION
    assert res.status in ["unavailable", "failed"]
    assert res.error_code == "capability_not_registered"


@pytest.mark.asyncio
async def test_supreme_kernel_dispatch_registered_mock():
    kernel = SupremeKernel()

    def mock_handler(req):
        return {"result": "ok", "value": 42}

    # Register handler
    try:
        kernel.registry.register_handler("test.mock_action", mock_handler)
    except ValueError:
        kernel.registry.handlers["test.mock_action"] = mock_handler

    req = KernelRequest(
        target_circle=CircleScope.EXECUTION,
        capability="test.mock_action",
        mode=ExecutionMode.SYNC,
        actor_id="test_actor",
        tenant_id="test_tenant",
    )
    res = await kernel.dispatch(req)
    assert res.request_id == req.request_id
    assert res.status == "succeeded"
    assert res.data == {"result": "ok", "value": 42}
