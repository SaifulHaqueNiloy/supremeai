"""Unit tests for Real-time Dashboard WebSocket and SwarmPubSub bridging."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from api.routes.realtime_dashboard import DashboardWebSocketManager, dashboard_manager


def test_ws_manager_init():
    """Test DashboardWebSocketManager initialization."""
    manager = DashboardWebSocketManager()
    assert manager.active_connections == {}
    assert manager.subscription_task is None
    assert manager.swarm_streamer is not None


@pytest.mark.asyncio
async def test_ws_manager_connect_and_disconnect():
    """Test connect and disconnect lifecycle in dashboard_manager."""
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()

    user_auth = {"sub": "admin_user", "role": "admin"}

    with patch.object(dashboard_manager.swarm_streamer, "subscribe") as mock_sub:
        async def fake_sub():
            yield '{"type": "metrics.update", "data": {"cpu": 10}}'

        mock_sub.return_value = fake_sub()
        await dashboard_manager.connect(mock_ws, user_auth)

        assert mock_ws in dashboard_manager.active_connections
        assert dashboard_manager.active_connections[mock_ws]["auth"] == user_auth

        dashboard_manager.disconnect(mock_ws)
        assert mock_ws not in dashboard_manager.active_connections


@pytest.mark.asyncio
async def test_ws_manager_subscribe_channel():
    """Test client subscribing to a specific channel."""
    mock_ws = MagicMock()
    dashboard_manager.active_connections[mock_ws] = {
        "auth": {"sub": "user1"},
        "channels": set(),
        "connected_at": 0,
    }

    dashboard_manager.add_channel_subscription(mock_ws, "metrics.update")
    assert "metrics.update" in dashboard_manager.active_connections[mock_ws]["channels"]

    dashboard_manager.remove_channel_subscription(mock_ws, "metrics.update")
    assert "metrics.update" not in dashboard_manager.active_connections[mock_ws]["channels"]

    dashboard_manager.disconnect(mock_ws)


def test_get_event_channel():
    """Test event channel mapping."""
    manager = DashboardWebSocketManager()
    assert manager._get_event_channel("metrics.cpu") == "metrics.update"
    assert manager._get_event_channel("cpu_usage") == "metrics.update"
    assert manager._get_event_channel("log.error") == "logs.stream"
    assert manager._get_event_channel("log_entry") == "logs.stream"
    assert manager._get_event_channel("job.build") == "jobs.status"
    assert manager._get_event_channel("job_started") == "jobs.status"
    assert manager._get_event_channel("alert.firewall") == "alerts.emergency"
    assert manager._get_event_channel("critical_alert") == "alerts.emergency"
    assert manager._get_event_channel("unknown_event_type") == "misc.events"
