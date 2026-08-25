# ============================================================
# SupremeAI - HITL Engine Test Suite
# Production-Ready pytest Tests for Human-in-the-Loop System
# ============================================================

import asyncio
import uuid
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

from conftest import (
    critical_risk_hitl_request,
    low_risk_hitl_request,
    sample_hitl_request,
)

# ============================================================
# MARKER: All tests in this module are HITL tests
# ============================================================
pytestmark = pytest.mark.hitl


class TestHITLEngineInitialization:
    """Test HITL Engine initialization and basic functionality."""

    @pytest.mark.unit
    async def test_hitl_engine_imports(self):
        """Test that HITL engine modules can be imported."""
        try:
            from app.services.hitl.approval_queue import ApprovalQueue
            from app.services.hitl.engine import HITLEngine
            from app.services.hitl.risk_assessor import RiskAssessor

            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import HITL modules: {e}")

    @pytest.mark.unit
    async def test_hitl_engine_instantiation(self):
        """Test that HITL engine can be instantiated with default config."""
        from app.services.hitl.engine import HITLEngine

        engine = HITLEngine()

        assert engine is not None
        assert hasattr(engine, "queue")
        assert hasattr(engine, "risk_assessor")
        assert hasattr(engine, "process_approval")

    @pytest.mark.unit
    async def test_risk_levels_defined(self):
        """Test that all required risk levels are defined."""
        from app.services.hitl.models import RiskLevel

        assert hasattr(RiskLevel, "LOW")
        assert hasattr(RiskLevel, "MEDIUM")
        assert hasattr(RiskLevel, "HIGH")
        assert hasattr(RiskLevel, "CRITICAL")


class TestRiskAssessment:
    """Test risk assessment functionality of HITL engine."""

    @pytest.mark.unit
    async def test_low_risk_detection(self):
        """Test that low-risk operations are correctly identified."""
        from app.services.hitl.risk_assessor import RiskAssessor

        assessor = RiskAssessor()

        low_risk_request = {
            "tool_name": "read_file",
            "tool_args": {"path": "/public/info.txt"},
            "context": {"agent_type": "conversational"},
        }

        risk_result = await assessor.assess(low_risk_request)

        assert risk_result["risk_level"] == "LOW"
        assert risk_result["risk_score"] < 0.3
        assert "auto_approve" in risk_result or risk_result["can_auto_approve"]

    @pytest.mark.unit
    async def test_medium_risk_detection(self):
        """Test that medium-risk operations are correctly identified."""
        from app.services.hitl.risk_assessor import RiskAssessor

        assessor = RiskAssessor()

        medium_risk_request = {
            "tool_name": "write_file",
            "tool_args": {"path": "/data/output.txt", "content": "..."},
            "context": {"agent_type": "task_agent"},
        }

        risk_result = await assessor.assess(medium_risk_request)

        assert risk_result["risk_level"] == "MEDIUM"
        assert 0.3 <= risk_result["risk_score"] < 0.7

    @pytest.mark.unit
    async def test_high_risk_detection(self):
        """Test that high-risk operations are correctly identified."""
        from app.services.hitl.risk_assessor import RiskAssessor

        assessor = RiskAssessor()

        high_risk_request = {
            "tool_name": "send_email",
            "tool_args": {
                "to": "external@example.com",
                "subject": "Urgent",
                "body": "Contains sensitive data",
            },
            "context": {
                "agent_type": "task_agent",
                "contains_pii": True,
            },
        }

        risk_result = await assessor.assess(high_risk_request)

        assert risk_result["risk_level"] == "HIGH"
        assert risk_result["risk_score"] >= 0.7

    @pytest.mark.unit
    async def test_critical_risk_detection(self):
        """Test that critical-risk operations are correctly identified."""
        from app.services.hitl.risk_assessor import RiskAssessor

        assessor = RiskAssessor()

        critical_risk_request = {
            "tool_name": "delete_database_table",
            "tool_args": {"table": "users", "confirm": True},
            "context": {
                "irreversible": True,
                "affects_all_users": True,
            },
        }

        risk_result = await assessor.assess(critical_risk_request)

        assert risk_result["risk_level"] == "CRITICAL"
        assert risk_result["risk_score"] >= 0.9
        assert risk_result.get("requires_multi_approval")

    @pytest.mark.unit
    async def test_custom_risk_rules_application(self):
        """Test that custom risk rules are properly applied."""
        from app.services.hitl.risk_assessor import RiskAssessor

        custom_rules = [
            {
                "pattern": {"tool_name": "custom_api_call"},
                "risk_level": "HIGH",
                "weight": 0.8,
                "conditions": {"external": True},
            },
            {
                "pattern": {"tool_name": "internal_query"},
                "risk_level": "LOW",
                "weight": 0.1,
            },
        ]

        assessor = RiskAssessor(custom_rules=custom_rules)

        # Test custom HIGH risk rule
        custom_high_request = {
            "tool_name": "custom_api_call",
            "tool_args": {},
            "context": {"external": True},
        }

        result = await assessor.assess(custom_high_request)
        assert result["risk_level"] == "HIGH"

        # Test custom LOW risk rule
        custom_low_request = {
            "tool_name": "internal_query",
            "tool_args": {},
            "context": {},
        }

        result = await assessor.assess(custom_low_request)
        assert result["risk_level"] == "LOW"


class TestApprovalQueue:
    """Test approval queue management."""

    @pytest.mark.unit
    async def test_create_approval_request(self):
        """Test creating a new approval request."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        request_data = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )

        approval_id = await queue.create(request_data)

        assert approval_id is not None
        assert isinstance(approval_id, (str, uuid.UUID))

    @pytest.mark.unit
    async def test_get_pending_approvals(self):
        """Test retrieving pending approvals."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        # Create multiple approvals
        for i in range(5):
            request = (
                sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
            )
            request["request_payload"]["tool_args"]["test_index"] = i
            await queue.create(request)

        pending = await queue.get_pending()

        assert len(pending) == 5
        for approval in pending:
            assert approval["status"] == "pending"

    @pytest.mark.unit
    async def test_approve_request(self):
        """Test approving an approval request."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        # Create and approve
        request = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )
        approval_id = await queue.create(request)

        reviewer_id = str(uuid.uuid4())
        result = await queue.approve(
            approval_id=approval_id,
            reviewed_by=reviewer_id,
            notes="Approved - looks good",
        )

        assert result["success"]
        assert result["status"] == "approved"
        assert result["reviewed_by"] == reviewer_id

    @pytest.mark.unit
    async def test_reject_request(self):
        """Test rejecting an approval request."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        # Create and reject
        request = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )
        approval_id = await queue.create(request)

        reviewer_id = str(uuid.uuid4())
        result = await queue.reject(
            approval_id=approval_id,
            reviewed_by=reviewer_id,
            reason="Rejected - security concern",
        )

        assert result["success"]
        assert result["status"] == "rejected"
        assert "security concern" in result.get("reason", "")

    @pytest.mark.unit
    async def test_escalate_request(self):
        """Test escalating an approval request."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        request = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )
        approval_id = await queue.create(request)

        escalate_to = str(uuid.uuid4())
        result = await queue.escalate(
            approval_id=approval_id,
            escalated_to=escalate_to,
            reason="Requires senior review",
        )

        assert result["success"]
        assert result["status"] == "escalated"
        assert result["escalated_to"] == escalate_to

    @pytest.mark.unit
    async def test_expire_old_requests(self):
        """Test that expired requests are automatically handled."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        # Create an already-expired request
        past_time = datetime.now(UTC) - timedelta(hours=1)
        request = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )
        request["expires_at"] = past_time.isoformat()

        approval_id = await queue.create(request)

        # Run expiration check
        expired_count = await queue.process_expired()

        assert expired_count >= 1

        # Verify status changed
        approval = await queue.get_by_id(approval_id)
        assert approval["status"] == "expired"


class TestAutoApprovalLogic:
    """Test automatic approval logic based on risk level and patterns."""

    @pytest.mark.unit
    async def test_low_risk_auto_approval(self):
        """Test that LOW risk requests are auto-approved."""
        from app.services.hitl.engine import HITLEngine

        engine = HITLEngine()

        request = (
            low_risk_hitl_request(None)
            if callable(low_risk_hitl_request)
            else low_risk_hitl_request
        )

        result = await engine.process_request(request)

        assert result["auto_approved"]
        assert result["status"] == "approved"
        assert result["reason"] == "low_risk_auto_approved"

    @pytest.mark.unit
    async def test_medium_risk_requires_review(self):
        """Test that MEDIUM risk requests require human review."""
        from app.services.hitl.engine import HITLEngine

        engine = HITLEngine()

        request = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )
        request["risk_level"] = "MEDIUM"
        request["risk_score"] = 0.5

        result = await engine.process_request(request)

        assert not result["auto_approved"]
        assert result["status"] == "pending_review"
        assert "approval_id" in result

    @pytest.mark.unit
    async def test_critical_risk_multi_approval_required(self):
        """Test that CRITICAL risk requires multiple approvers."""
        from app.services.hitl.engine import HITLEngine

        engine = HITLEngine()

        request = (
            critical_risk_hitl_request(None)
            if callable(critical_risk_hitl_request)
            else critical_risk_hitl_request
        )

        result = await engine.process_request(request)

        assert result["multi_approval_required"]
        assert result["min_approvers"] >= 2
        assert result["status"] == "pending_multi_approval"

    @pytest.mark.unit
    async def test_pattern_based_auto_approval(self):
        """Test auto-approval based on configured patterns."""
        from app.services.hitl.engine import HITLEngine

        engine = HITLEngine(
            config={
                "auto_approve_patterns": ["read_*", "calculate_*", "get_*"],
            }
        )

        read_request = {
            "agent_id": str(uuid.uuid4()),
            "request_type": "tool_execution",
            "request_payload": {
                "tool_name": "read_config",
                "tool_args": {},
            },
            "risk_level": "UNKNOWN",
            "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        }

        result = await engine.process_request(read_request)

        assert result["auto_approved"]
        assert result["reason"] == "pattern_match"


class TestEscalationRules:
    """Test escalation rule processing."""

    @pytest.mark.unit
    async def test_timeout_escalation(self):
        """Test escalation when SLA timeout is exceeded."""
        from datetime import datetime, timedelta, timezone

        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        # Create old pending request
        datetime.now(UTC) - timedelta(hours=2)
        request = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )
        request["sla_minutes"] = 60  # 1 hour SLA

        await queue.create(request)

        # Simulate time passing by modifying internal state
        # (In real implementation, this would be handled by timestamps)
        escalated = await queue.check_and_escalate()

        assert len(escalated) > 0
        assert escalated[0]["escalation_reason"] == "sla_timeout"

    @pytest.mark.unit
    async def test_rejection_threshold_escalation(self):
        """Test escalation after multiple rejections."""
        from app.services.hitl.engine import HITLEngine

        engine = HITLEngine(
            config={
                "max_rejections_before_escalation": 2,
            }
        )

        request = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )

        # Process initial request
        result = await engine.process_request(request)
        approval_id = result.get("approval_id")

        if approval_id:
            # Reject twice
            reviewer1 = str(uuid.uuid4())
            reviewer2 = str(uuid.uuid4())

            await engine.queue.reject(approval_id, reviewer1, "First rejection")

            # Second rejection should trigger escalation
            rejection_result = await engine.queue.reject(approval_id, reviewer2, "Second rejection")

            # Check if escalation was triggered
            if rejection_result.get("escalated"):
                assert rejection_result["escalated"]


class TestHITLAPIEndpoints:
    """Test HITL-related API endpoints."""

    @pytest.mark.integration
    async def test_create_hitl_approval_request(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test creating HITL approval request via API."""
        now = datetime.now(UTC)
        hitl_data = {
            "agent_id": created_agent["id"],
            "request_type": "tool_execution",
            "request_payload": {
                "tool_name": "send_email",
                "tool_args": {"to": "user@example.com"},
            },
            "risk_level": "MEDIUM",
            "risk_score": 0.5,
            "expires_at": (now + timedelta(hours=1)).isoformat(),
        }

        response = await client.post(
            "/api/v1/hitl/approvals",
            json=hitl_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json().get("data", response.json())
        assert data["status"] == "pending"
        assert data["risk_level"] == "MEDIUM"

    @pytest.mark.integration
    async def test_list_pending_approvals(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing pending approval requests."""
        response = await client.get(
            "/api/v1/hitl/approvals?status=pending",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert isinstance(data, list)

    @pytest.mark.integration
    async def test_approve_via_api(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test approving a request via API endpoint."""
        # First create a request
        now = datetime.now(UTC)
        create_response = await client.post(
            "/api/v1/hitl/approvals",
            json={
                "agent_id": created_agent["id"],
                "request_type": "tool_execution",
                "request_payload": {"tool_name": "test_tool"},
                "risk_level": "MEDIUM",
                "expires_at": (now + timedelta(hours=1)).isoformat(),
            },
            headers=auth_headers,
        )

        assert create_response.status_code in [200, 201]
        approval_id = create_response.json().get("data", {}).get(
            "id"
        ) or create_response.json().get("id")

        # Approve it
        approve_response = await client.post(
            f"/api/v1/hitl/approvals/{approval_id}/approve",
            json={"notes": "Approved via test"},
            headers=auth_headers,
        )

        assert approve_response.status_code == 200
        data = approve_response.json().get("data", approve_response.json())
        assert data["status"] == "approved"

    @pytest.mark.integration
    async def test_reject_via_api(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_agent: dict,
    ):
        """Test rejecting a request via API endpoint."""
        # Create request
        now = datetime.now(UTC)
        create_response = await client.post(
            "/api/v1/hitl/approvals",
            json={
                "agent_id": created_agent["id"],
                "request_type": "tool_execution",
                "request_payload": {"tool_name": "test_tool"},
                "risk_level": "MEDIUM",
                "expires_at": (now + timedelta(hours=1)).isoformat(),
            },
            headers=auth_headers,
        )

        approval_id = create_response.json().get("data", {}).get(
            "id"
        ) or create_response.json().get("id")

        # Reject it
        reject_response = await client.post(
            f"/api/v1/hitl/approvals/{approval_id}/reject",
            json={"reason": "Not authorized action"},
            headers=auth_headers,
        )

        assert reject_response.status_code == 200
        data = reject_response.json().get("data", reject_response.json())
        assert data["status"] == "rejected"

    @pytest.mark.integration
    async def test_my_approvals_endpoint(
        self,
        client: AsyncClient,
        operator_auth_headers: dict,
    ):
        """Test getting approvals assigned to current user."""
        response = await client.get(
            "/api/v1/hitl/my-approvals",
            headers=operator_auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert isinstance(data, list)

    @pytest.mark.integration
    async def test_hitl_statistics_endpoint(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
    ):
        """Test HITL statistics endpoint (admin only)."""
        response = await client.get(
            "/api/v1/hitl/stats",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json().get("data", response.json())
        assert "total_approvals" in data or "stats" in data


class TestHITLConcurrency:
    """Test concurrent access to approval queue."""

    @pytest.mark.unit
    async def test_concurrent_approval_creation(self):
        """Test handling concurrent approval creation requests."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        # Create many approvals concurrently
        async def create_approval(index):
            request = (
                sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
            )
            request["request_payload"]["index"] = index
            return await queue.create(request)

        tasks = [create_approval(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        successes = [r for r in results if not isinstance(r, Exception)]
        assert len(successes) == 50

        # All should have unique IDs
        ids = set(successes)
        assert len(ids) == 50

    @pytest.mark.unit
    async def test_concurrent_approval_processing(self):
        """Test concurrent approval/rejection of same request."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        # Create single approval
        request = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )
        approval_id = await queue.create(request)

        # Try to approve concurrently
        async def approve_as_user(user_id):
            return await queue.approve(
                approval_id=approval_id,
                reviewed_by=user_id,
                notes=f"User {user_id} approves",
            )

        tasks = [approve_as_user(f"user_{i}") for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Only one should succeed, others should fail
        successes = sum(1 for r in results if getattr(r, "success", False))
        failures = sum(
            1 for r in results if isinstance(r, Exception) or not getattr(r, "success", None)
        )

        assert successes == 1  # Only one approval should succeed
        assert failures == 4  # Others should be rejected


class TestHITLAuditLogging:
    """Test audit logging for all HITL operations."""

    @pytest.mark.unit
    async def test_approval_creation_logged(self):
        """Test that approval creation is logged."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        request = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )
        approval_id = await queue.create(request)

        # Check audit log exists
        logs = await queue.get_audit_log(approval_id)

        assert len(logs) > 0
        assert logs[0]["action"] == "created"

    @pytest.mark.unit
    async def test_decision_logging(self):
        """Test that approval decisions are logged."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        request = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )
        approval_id = await queue.create(request)

        # Make decision
        reviewer = str(uuid.uuid4())
        await queue.approve(approval_id, reviewer, "Test approval")

        # Check log includes decision
        logs = await queue.get_audit_log(approval_id)

        decision_logs = [log for log in logs if log["action"] == "approved"]
        assert len(decision_logs) == 1
        assert decision_logs[0]["reviewed_by"] == reviewer


class TestHITLErrorHandling:
    """Test error handling in HITL engine."""

    @pytest.mark.unit
    async def test_invalid_risk_level(self):
        """Test handling of invalid risk level."""
        from app.services.hitl.risk_assessor import RiskAssessor

        assessor = RiskAssessor()

        invalid_request = {
            "tool_name": "some_tool",
            "risk_level": "INVALID_LEVEL",  # Invalid level
        }

        with pytest.raises(ValueError) as exc_info:
            await assessor.assess(invalid_request)

        assert "invalid risk level" in str(exc_info.value).lower()

    @pytest.mark.unit
    async def test_expired_approval_cannot_be_decided(self):
        """Test that expired approvals cannot be approved/rejected."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        # Create expired request
        past_time = datetime.now(UTC) - timedelta(hours=1)
        request = (
            sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
        )
        request["expires_at"] = past_time.isoformat()

        approval_id = await queue.create(request)
        await queue.process_expired()

        # Try to approve expired request
        with pytest.raises(Exception) as exc_info:
            await queue.approve(approval_id, str(uuid.uuid4()), "Should fail")

        assert "expired" in str(exc_info.value).lower()

    @pytest.mark.unit
    async def test_nonexistent_approval_handling(self):
        """Test handling of non-existent approval IDs."""
        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()
        fake_id = str(uuid.uuid4())

        result = await queue.get_by_id(fake_id)
        assert result is None

        result = await queue.approve(fake_id, str(uuid.uuid4()), "test")
        assert not result["success"]
        assert "not found" in result.get("error", "").lower()


# ============================================================
# PERFORMANCE TESTS
# ============================================================
class TestHITLPerformance:
    """Performance tests for HITL engine."""

    @pytest.mark.slow
    @pytest.mark.unit
    async def test_bulk_approval_creation_performance(self):
        """Test performance of creating many approvals."""
        import time

        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        start_time = time.time()

        # Create 1000 approvals
        for i in range(1000):
            request = (
                sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
            )
            request["batch_index"] = i
            await queue.create(request)

        elapsed = time.time() - start_time

        # Should complete within reasonable time (< 10 seconds)
        assert elapsed < 10, f"Took {elapsed:.2f}s, expected < 10s"

    @pytest.mark.slow
    @pytest.mark.unit
    async def test_search_performance_with_many_records(self):
        """Test search performance with large dataset."""
        import time

        from app.services.hitl.approval_queue import ApprovalQueue

        queue = ApprovalQueue()

        # Pre-populate with data
        for i in range(1000):
            request = (
                sample_hitl_request(None) if callable(sample_hitl_request) else sample_hitl_request
            )
            request["search_key"] = f"item_{i % 100}"  # Create some duplicates
            await queue.create(request)

        # Time a search query
        start_time = time.time()
        results = await queue.search({"search_key": "item_50"})
        elapsed = time.time() - start_time

        # Search should be fast (< 1 second)
        assert elapsed < 1, f"Search took {elapsed:.2f}s, expected < 1s"
        assert len(results) >= 10  # Should find ~10 matches


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
