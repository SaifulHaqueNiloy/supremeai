"""Tests to improve coverage for events routes."""

from unittest.mock import MagicMock, patch


class TestDashboardStream:
    """Tests for dashboard_stream and event generator."""

    def test_event_generator_runs(self):
        """Event generator should yield SSE events."""
        from api.routes.events import dashboard_stream

        mock_request = MagicMock()
        mock_request.is_disconnected.return_value = False

        with patch("api.routes.events.settings"):
            generator = dashboard_stream.event_generator(mock_request)
            events = []
            for item in generator:
                events.append(item)

        assert len(events) > 0

    def test_event_generator_disconnect(self):
        """Event generator should stop on client disconnect."""
        from api.routes.events import dashboard_stream

        mock_request = MagicMock()
        mock_request.is_disconnected.side_effect = [False, True]

        with patch("api.routes.events.settings"):
            generator = dashboard_stream.event_generator(mock_request)
            events = []
            for item in generator:
                events.append(item)
            assert len(events) == 0
