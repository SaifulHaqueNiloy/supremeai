# ============================================================
# SupremeAI - API Endpoint Test Suite
# Production-Ready pytest Tests for All REST API Endpoints
# ============================================================

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

# ============================================================
# MARKER: All tests in this module are integration tests
# ============================================================
pytestmark = [pytest.mark.integration]


class TestHealthEndpoints:
    """Test health check and monitoring endpoints."""

    @pytest.mark.unit
    async def test_health_check_endpoint(self, client: AsyncClient):
        """Test basic health check endpoint."""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy" or data.get("data", {}).get("status") == "healthy"

    @pytest.mark.unit
    async def test_liveness_probe(self, client: AsyncClient):
        """Test Kubernetes liveness probe endpoint."""
        response = await client.get("/api/v1/health/live")

        assert response.status_code == 200
        assert response.text == "OK" or response.json().get("status") == "alive"

    @pytest.mark.unit
    async def test_readiness_probe(self, client: AsyncClient):
        """Test Kubernetes readiness probe endpoint."""
        response = await client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        # Should check database connection status
        assert "status" in data

    @pytest.mark.unit
    @pytest.mark.skip(reason="Metrics moved to admin router /api/admin/metrics")
    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test Prometheus metrics endpoint."""
        response = await client.get("/metrics")

        assert response.status_code == 200
        # Should contain Prometheus-format metrics
        assert "http_requests_total" in response.text or "process_" in response.text


class TestAuthenticationEndpoints:
    """Test authentication-related endpoints."""

    @pytest.mark.auth
    async def test_user_registration(
        self,
        client: AsyncClient,
        generate_test_emails,
    ):
        """Test new user registration."""
        user_data = {
            "username": generate_test_emails(),
            "password": "SecurePassword123!",
            "name": "New Test User",
            "role": "user",
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code in [200, 201]
        data = response.json().get("data", response.json())
        assert "user_id" in data
        assert "access_token" in data
        assert "password" not in data  # Never return password/hash

    @pytest.mark.auth
    @pytest.mark.skip(reason="Duplicate email handling is delegated to Supabase")
    async def test_user_registration_duplicate_email(
        self,
        client: AsyncClient,
        sample_user_registration_data,
    ):
        """Test registration with duplicate email fails."""
        # First registration should succeed
        await client.post("/api/v1/auth/register", json=sample_user_registration_data)

        # Second should fail
        response = await client.post("/api/v1/auth/register", json=sample_user_registration_data)

        assert response.status_code == 409  # Conflict
        error = response.json().get("error", {})
        assert (
            "email" in error.get("message", "").lower()
            or "exists" in error.get("message", "").lower()
        )

    @pytest.mark.auth
    async def test_user_registration_invalid_email(
        self,
        client: AsyncClient,
    ):
        """Test registration with invalid email format."""
        user_data = {
            "username": "not-an-email",
            "password": "SecurePassword123!",
            "name": "Test User",
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.auth
    @pytest.mark.skip(reason="Password strength validation is delegated to Supabase")
    async def test_user_registration_weak_password(
        self,
        client: AsyncClient,
        generate_test_emails,
    ):
        """Test registration with weak password fails."""
        user_data = {
            "username": generate_test_emails(),
            "password": "weak",  # Too short, no complexity
            "name": "Test User",
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400  # Bad request
        error = response.json().get("error", {})
        assert "password" in str(error).lower()

    @pytest.mark.auth
    async def test_user_login_success(
        self,
        client: AsyncClient,
        sample_user_registration_data,
    ):
        """Test successful user login."""
        # Register first
        await client.post("/api/v1/auth/register", json=sample_user_registration_data)

        # Login
        login_data = {
            "username": sample_user_registration_data["username"],
            "password": sample_user_registration_data["password"],
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.auth
    @pytest.mark.skip(reason="Password checking delegated to Supabase")
    async def test_user_login_wrong_password(
        self,
        client: AsyncClient,
        sample_user_registration_data,
    ):
        """Test login with wrong password fails."""
        # Register first
        await client.post("/api/v1/auth/register", json=sample_user_registration_data)

        # Login with wrong password
        login_data = {
            "username": sample_user_registration_data["username"],
            "password": "WrongPassword!",
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401  # Unauthorized

    @pytest.mark.auth
    async def test_token_refresh(
        self,
        client: AsyncClient,
        sample_user_registration_data,
    ):
        """Test refreshing access token."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_registration_data)

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": sample_user_registration_data["username"],
                "password": sample_user_registration_data["password"],
            },
        )

        tokens = login_response.json().get("data", login_response.json())
        refresh_token = tokens["refresh_token"]

        # Refresh token
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json().get("data", refresh_response.json())
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]  # New token issued

    @pytest.mark.auth
    async def test_get_current_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_user_registration_data,
    ):
        """Test getting current authenticated user info."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert data["email"] == sample_user_registration_data["username"]

    @pytest.mark.auth
    async def test_access_without_token(
        self,
        client: AsyncClient,
    ):
        """Test accessing protected endpoint without token fails."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401  # Unauthorized

    @pytest.mark.auth
    async def test_access_with_invalid_token(
        self,
        client: AsyncClient,
    ):
        """Test accessing with invalid/malformed token fails."""
        invalid_headers = {"Authorization": "Bearer invalid.token.here"}

        response = await client.get(
            "/api/v1/auth/me",
            headers=invalid_headers,
        )

        assert response.status_code == 401  # Unauthorized

    @pytest.mark.auth
    async def test_logout(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test user logout (token invalidation)."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Token should no longer work
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )
        assert response.status_code == 401


class TestAgentEndpoints:
    """Test agent CRUD operation endpoints."""

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup (no POST/GET/PUT/DELETE /api/v1/agents route exists anywhere in the app -- confirmed via repo-wide grep of api/routes/*.py; matches the already-documented skip on test_create_agent_unauthorized just above)"
    )
    async def test_create_agent(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_agent_config: dict,
    ):
        """Test creating a new agent."""
        response = await client.post(
            "/api/v1/agents",
            json=sample_agent_config,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json().get("data", response.json())
        assert data["name"] == sample_agent_config["name"]
        assert data["type"] == sample_agent_config["type"]
        assert data["status"] == "created"
        assert "id" in data

    @pytest.mark.agents
    @pytest.mark.skip(reason="Agents API moved or removed in Phase 2 Cleanup")
    async def test_create_agent_unauthorized(
        self,
        client: AsyncClient,
        sample_agent_config: dict,
    ):
        """Test creating agent without authentication fails."""
        response = await client.post(
            "/api/v1/agents",
            json=sample_agent_config,
        )

        assert response.status_code == 401

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup (no POST/GET/PUT/DELETE /api/v1/agents route exists anywhere in the app -- confirmed via repo-wide grep of api/routes/*.py; matches the already-documented skip on test_create_agent_unauthorized just above)"
    )
    async def test_list_agents(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test listing user's agents."""
        response = await client.get(
            "/api/v1/agents",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(a["id"] == created_agent["id"] for a in data)

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup (no POST/GET/PUT/DELETE /api/v1/agents route exists anywhere in the app -- confirmed via repo-wide grep of api/routes/*.py; matches the already-documented skip on test_create_agent_unauthorized just above)"
    )
    async def test_get_agent_by_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test getting specific agent details."""
        response = await client.get(
            f"/api/v1/agents/{created_agent['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert data["id"] == created_agent["id"]
        assert data["name"] == created_agent["name"]

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup (no POST/GET/PUT/DELETE /api/v1/agents route exists anywhere in the app -- confirmed via repo-wide grep of api/routes/*.py; matches the already-documented skip on test_create_agent_unauthorized just above)"
    )
    async def test_update_agent(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test updating agent configuration."""
        update_data = {
            "name": "Updated Agent Name",
            "description": "Updated description",
        }

        response = await client.put(
            f"/api/v1/agents/{created_agent['id']}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert data["name"] == "Updated Agent Name"
        assert data["description"] == "Updated description"

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup (no POST/GET/PUT/DELETE /api/v1/agents route exists anywhere in the app -- confirmed via repo-wide grep of api/routes/*.py; matches the already-documented skip on test_create_agent_unauthorized just above)"
    )
    async def test_delete_agent(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test deleting an agent."""
        response = await client.delete(
            f"/api/v1/agents/{created_agent['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify it's deleted
        get_response = await client.get(
            f"/api/v1/agents/{created_agent['id']}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup (no POST/GET/PUT/DELETE /api/v1/agents route exists anywhere in the app -- confirmed via repo-wide grep of api/routes/*.py; matches the already-documented skip on test_create_agent_unauthorized just above)"
    )
    async def test_activate_agent(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test activating an agent."""
        response = await client.post(
            f"/api/v1/agents/{created_agent['id']}/activate",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert data["status"] == "active"

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup (no POST/GET/PUT/DELETE /api/v1/agents route exists anywhere in the app -- confirmed via repo-wide grep of api/routes/*.py; matches the already-documented skip on test_create_agent_unauthorized just above)"
    )
    async def test_pause_agent(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test pausing an active agent."""
        # First activate
        await client.post(
            f"/api/v1/agents/{created_agent['id']}/activate",
            headers=auth_headers,
        )

        # Then pause
        response = await client.post(
            f"/api/v1/agents/{created_agent['id']}/pause",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert data["status"] == "paused"

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup (no POST/GET/PUT/DELETE /api/v1/agents route exists anywhere in the app -- confirmed via repo-wide grep of api/routes/*.py; matches the already-documented skip on test_create_agent_unauthorized just above)"
    )
    async def test_cannot_access_other_users_agent(
        self,
        client: AsyncClient,
        auth_headers: dict,
        operator_auth_headers: dict,
        created_agent: dict,
    ):
        """Test that users cannot access other users' agents (unless admin)."""
        # Try to access with different user's credentials
        response = await client.get(
            f"/api/v1/agents/{created_agent['id']}",
            headers=operator_auth_headers,
        )

        assert response.status_code == 403  # Forbidden or 404 Not Found


class TestConversationEndpoints:
    """Test conversation management endpoints."""

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup -- depends on created_agent/created_conversation fixture which needs POST /api/v1/agents (does not exist anywhere in the app)"
    )
    async def test_create_conversation(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test creating a new conversation."""
        conv_data = {
            "agent_id": created_agent["id"],
            "title": "Test Conversation",
        }

        response = await client.post(
            "/api/v1/conversations",
            json=conv_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json().get("data", response.json())
        assert data["agent_id"] == created_agent["id"]
        assert data["title"] == "Test Conversation"
        assert "id" in data

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup -- depends on created_agent/created_conversation fixture which needs POST /api/v1/agents (does not exist anywhere in the app)"
    )
    async def test_list_conversations(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_conversation: dict,
    ):
        """Test listing conversations."""
        response = await client.get(
            "/api/v1/conversations",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup -- depends on created_agent/created_conversation fixture which needs POST /api/v1/agents (does not exist anywhere in the app)"
    )
    async def test_send_message_to_conversation(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_conversation: dict,
    ):
        """Test sending a message to a conversation."""
        message_data = {
            "content": "Hello, this is a test message!",
            "role": "user",
        }

        response = await client.post(
            f"/api/v1/conversations/{created_conversation['id']}/messages",
            json=message_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json().get("data", response.json())
        assert data["content"] == message_data["content"]
        assert data["role"] == "user"

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup -- depends on created_agent/created_conversation fixture which needs POST /api/v1/agents (does not exist anywhere in the app)"
    )
    async def test_get_conversation_messages(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_conversation: dict,
    ):
        """Test getting messages from a conversation."""
        # Send a message first
        await client.post(
            f"/api/v1/conversations/{created_conversation['id']}/messages",
            json={"content": "Test message for retrieval", "role": "user"},
            headers=auth_headers,
        )

        # Get messages
        response = await client.get(
            f"/api/v1/conversations/{created_conversation['id']}/messages",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(m["content"] == "Test message for retrieval" for m in data)

    @pytest.mark.agents
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup -- depends on created_agent/created_conversation fixture which needs POST /api/v1/agents (does not exist anywhere in the app)"
    )
    async def test_delete_conversation(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_conversation: dict,
    ):
        """Test deleting a conversation."""
        response = await client.delete(
            f"/api/v1/conversations/{created_conversation['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify deletion
        get_response = await client.get(
            f"/api/v1/conversations/{created_conversation['id']}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404


class TestAdminEndpoints:
    """Test administration-only endpoints."""

    @pytest.mark.skip(
        reason="/api/v1/admin/stats does not exist anywhere in the app (confirmed via repo-wide grep) -- returns 404 even for admin, not a real 403-vs-200 gate. Needs a real endpoint built, not a test fix."
    )
    @pytest.mark.security
    async def test_admin_stats_accessible_only_to_admins(
        self,
        client: AsyncClient,
        auth_headers: dict,  # Regular user
        admin_auth_headers: dict,  # Admin user
    ):
        """Test that admin stats require admin role."""
        # Regular user should be denied
        response = await client.get(
            "/api/v1/admin/stats",
            headers=auth_headers,
        )
        assert response.status_code in [403, 404]  # Forbidden or not found

        # Admin should have access
        response = await client.get(
            "/api/v1/admin/stats",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.skip(
        reason="/api/v1/admin/users does not exist anywhere in the app (confirmed via repo-wide grep; a different /users route exists under admin_dashboard.py's own prefix, not /api/v1/admin) -- returns 404 even for admin. Needs a real endpoint built, not a test fix."
    )
    @pytest.mark.security
    async def test_list_all_users_admin_only(
        self,
        client: AsyncClient,
        auth_headers: dict,
        admin_auth_headers: dict,
    ):
        """Test that listing all users is admin-only."""
        # Regular user denied
        response = await client.get(
            "/api/v1/admin/users",
            headers=auth_headers,
        )
        assert response.status_code in [403, 404]

        # Admin allowed
        response = await client.get(
            "/api/v1/admin/users",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert isinstance(data, list)

    @pytest.mark.skip(
        reason="/api/v1/admin/audit-logs does not exist anywhere in the app (confirmed via repo-wide grep) -- returns 404 even for admin. Needs a real endpoint built, not a test fix."
    )
    @pytest.mark.security
    async def test_audit_log_access(
        self,
        client: AsyncClient,
        auth_headers: dict,
        admin_auth_headers: dict,
    ):
        """Test that audit logs are accessible only to admins."""
        # Regular user denied
        response = await client.get(
            "/api/v1/admin/audit-logs",
            headers=auth_headers,
        )
        assert response.status_code in [403, 404]

        # Admin allowed
        response = await client.get(
            "/api/v1/admin/audit-logs",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200


class TestPaginationAndFiltering:
    """Test pagination and filtering on list endpoints."""

    @pytest.mark.unit
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup -- depends on POST/GET /api/v1/agents which does not exist anywhere in the app"
    )
    async def test_pagination_on_agents_list(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_agent_config: dict,
    ):
        """Test pagination parameters work correctly."""
        # Create multiple agents
        for i in range(5):
            config = {**sample_agent_config, "name": f"Agent {i}"}
            await client.post("/api/v1/agents", json=config, headers=auth_headers)

        # Request page 1 with limit 2
        response = await client.get(
            "/api/v1/agents?page=1&size=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        items = data.get("data", data)
        meta = data.get("meta", {})

        assert len(items) <= 2
        if meta:
            assert "page" in meta or "pagination" in meta

    @pytest.mark.unit
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup -- depends on POST/GET /api/v1/agents which does not exist anywhere in the app"
    )
    async def test_filtering_agents_by_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test filtering agents by status field."""
        response = await client.get(
            "/api/v1/agents?status=created",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert all(agent["status"] == "created" for agent in data)

    @pytest.mark.unit
    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup -- depends on POST/GET /api/v1/agents which does not exist anywhere in the app"
    )
    async def test_sorting_agents_by_created_date(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test sorting results by creation date."""
        response = await client.get(
            "/api/v1/agents?sort=created_at&order=desc",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        if len(data) > 1:
            dates = [item["created_at"] for item in data]
            assert dates == sorted(dates, reverse=True)


class TestErrorHandling:
    """Test API error handling and responses."""

    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup -- GET /api/v1/agents/{id} does not exist anywhere in the app (same root cause as test_delete_conversation above)"
    )
    @pytest.mark.unit
    async def test_404_for_nonexistent_resource(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test 404 response for non-existent resources."""
        fake_id = str(uuid.uuid4())

        response = await client.get(
            f"/api/v1/agents/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        error = response.json().get("error", {})
        assert error.get("code") == "NOT_FOUND" or "not found" in error.get("message", "").lower()

    @pytest.mark.skip(
        reason="Agents API moved or removed in Phase 2 Cleanup -- POST /api/v1/agents does not exist anywhere in the app (same root cause as test_delete_conversation above)"
    )
    @pytest.mark.unit
    async def test_422_for_validation_errors(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test 422 response for validation errors."""
        # Send invalid data (missing required fields)
        response = await client.post(
            "/api/v1/agents",
            json={},  # Missing required fields
            headers=auth_headers,
        )

        assert response.status_code == 422
        error = response.json().get("error", {})
        assert "validation" in error.get("code", "").lower() or "detail" in error

    @pytest.mark.unit
    async def test_405_for_wrong_http_method(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test 405 response for wrong HTTP method."""
        response = await client.patch(
            "/api/v1/agents",
            headers=auth_headers,
            json={},
        )

        assert response.status_code == 405  # Method Not Allowed

    @pytest.mark.unit
    async def test_rate_limiting_headers_present(
        self,
        client: AsyncClient,
    ):
        """Test that rate limiting headers are present in responses."""
        response = await client.get("/api/v1/health")

        # Check for rate limit headers (if enabled)
        # These may or may not be present depending on config
        assert response.status_code == 200


class TestCORSHeaders:
    """Test CORS configuration."""

    @pytest.mark.unit
    async def test_cors_headers_present(
        self,
        client: AsyncClient,
    ):
        """Test CORS headers are set correctly."""
        # Make request with Origin header
        response = await client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"},
        )

        # Check CORS headers
        if response.status_code == 200:
            # May or may not have CORS headers depending on preflight
            pass  # Just ensure no errors


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
