"""Tests to improve coverage for evolution routes."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


class TestQuarantineSkill:
    """Tests for quarantine_skill endpoint."""

    def test_quarantine_skill_success(self):
        """Admin can quarantine a skill."""
        from api.routes.evolution import QuarantineRequest, quarantine_skill

        mock_admin = {"uid": "admin", "role": "admin"}
        payload = QuarantineRequest(skill_name="bad_skill")

        fake_registry = MagicMock()
        fake_registry.get_skill.return_value = {"name": "bad_skill", "status": "active"}
        fake_fitness = MagicMock()
        fake_fitness.registry = fake_registry

        with patch(
            "api.routes.evolution.get_fitness_engine", return_value=fake_fitness
        ):
            with patch("api.routes.evolution.time"):
                with patch("api.routes.evolution.datetime") as mock_dt:
                    mock_dt.now.return_value.isoformat.return_value = (
                        "2026-01-01T00:00:00"
                    )
                    response = quarantine_skill(payload=payload, admin=mock_admin)

        assert response["status"] == "quarantined"

    def test_quarantine_skill_not_found(self):
        """Quarantine unknown skill should raise 404."""
        from api.routes.evolution import QuarantineRequest, quarantine_skill

        mock_admin = {"uid": "admin", "role": "admin"}
        payload = QuarantineRequest(skill_name="missing_skill")

        fake_registry = MagicMock()
        fake_registry.get_skill.return_value = None
        fake_fitness = MagicMock()
        fake_fitness.registry = fake_registry

        with patch(
            "api.routes.evolution.get_fitness_engine", return_value=fake_fitness
        ):
            with pytest.raises(HTTPException) as exc_info:
                quarantine_skill(payload=payload, admin=mock_admin)

        assert exc_info.value.status_code == 404


class TestGetSwarmGraph:
    """Tests for get_swarm_graph endpoint."""

    def test_get_swarm_graph_returns_graph(self):
        """Should return current swarm graph."""
        from api.routes.evolution import get_swarm_graph

        response = get_swarm_graph()
        assert "nodes" in response
        assert "edges" in response
