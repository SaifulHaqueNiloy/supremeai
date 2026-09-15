import pytest
from httpx import ASGITransport, AsyncClient

from core.app import app


@pytest.mark.asyncio
async def test_task_gateway_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test submit task
        submit_res = await client.post(
            "/api/v1/tasks",
            json={"goal": "Test background task", "metadata": {"priority": "high"}},
            headers={"Authorization": "Bearer mock-token", "X-Tenant-ID": "tenant_test"},
        )
        assert submit_res.status_code == 200
        data = submit_res.json()
        task_id = data["task_id"]
        assert data["status"] == "pending"

        # 2. Test get status
        status_res = await client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": "Bearer mock-token", "X-Tenant-ID": "tenant_test"},
        )
        assert status_res.status_code == 200
        assert status_res.json()["task_id"] == task_id

        # 3. Test cancel task
        cancel_res = await client.post(
            f"/api/v1/tasks/{task_id}/cancel",
            headers={"Authorization": "Bearer mock-token", "X-Tenant-ID": "tenant_test"},
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "cancelled"

        # A different tenant must not be able to discover the task.
        cross_tenant_res = await client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": "Bearer mock-token", "X-Tenant-ID": "tenant_other"},
        )
        assert cross_tenant_res.status_code == 404
