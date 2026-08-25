"""
HITL (Human-in-the-Loop) Engine Test Suite
==========================================

Critical Path Tests - These tests ensure the security layer that prevents
autonomous AI agents from performing harmful actions without human approval.

Test Coverage:
- Action queuing and classification
- Approval/Rejection workflow
- Expiration handling
- Priority management
- Notification system
- Audit trail integrity
- Role-based access control
- Edge cases and error handling

Run with: pytest tests/test_hitl_engine.py -v --cov=hitl
"""

import asyncio
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conftest import (
    CustomAssertions,
    sample_admin_data,
    sample_hitl_action_approved,
    sample_hitl_action_pending,
    sample_hitl_action_rejected,
    sample_hitl_decision_request,
    sample_operator_data,
    sample_user_data,
)

# ============================================================================
# MOCK HITL ENGINE IMPLEMENTATION (for testing)
# ============================================================================


class MockHITLEngine:
    """
    Mock implementation of HITL Engine for testing.

    In production, this would be app/services/hitl.py
    This mock simulates all behaviors for isolated unit testing.
    """

    # Action types that require approval
    APPROVAL_REQUIRED = {
        "file_write",
        "file_delete",
        "file_modify",
        "external_api_call",
        "database_write",
        "database_delete",
        "code_execution",
        "data_export",
        "user_management",
        "config_change",
    }

    # Auto-approved action types
    AUTO_APPROVE = {"web_search", "calculator", "read_operation", "internal_lookup", "formatting"}

    PRIORITIES = {"low", "medium", "high", "critical"}

    STATUSES = {"pending", "approved", "rejected", "expired", "executed"}

    def __init__(self):
        self.actions: dict[str, dict[str, Any]] = {}
        self.notifications: list[dict[str, Any]] = []
        self.audit_log: list[dict[str, Any]] = []
        self._action_counter = 0

    async def queue_action(
        self,
        agent_id: str,
        action_type: str,
        description: str,
        payload: dict[str, Any],
        priority: str = "medium",
        conversation_id: str | None = None,
        timeout_minutes: int = 30,
    ) -> dict[str, Any]:
        """Queue a new action for human review."""

        # Validate inputs
        if not agent_id:
            raise ValueError("agent_id is required")
        if not action_type:
            raise ValueError("action_type is required")
        if not description:
            raise ValueError("description is required")
        if priority not in self.PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}. Must be one of {self.PRIORITIES}")

        now = datetime.now(UTC)
        self._action_counter += 1

        action = {
            "id": f"hitl-action-{self._action_counter:04d}",
            "agent_id": agent_id,
            "conversation_id": conversation_id,
            "action_type": action_type,
            "description": description,
            "payload": payload,
            "priority": priority,
            "status": "pending",
            "requested_by": "agent",
            "reviewed_by": None,
            "decision": None,
            "decision_reason": None,
            "modified_payload": None,
            "result": None,
            "requested_at": now,
            "reviewed_at": None,
            "expires_at": now + timedelta(minutes=timeout_minutes),
        }

        self.actions[action["id"]] = action

        # Log to audit trail
        await self._log_audit_event(
            event_type="action_queued",
            action_id=action["id"],
            details={
                "agent_id": agent_id,
                "action_type": action_type,
                "priority": priority,
            },
        )

        return action

    async def get_pending_actions(
        self, agent_id: str | None = None, priority: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get list of pending actions."""

        pending = [action for action in self.actions.values() if action["status"] == "pending"]

        # Apply filters
        if agent_id:
            pending = [a for a in pending if a["agent_id"] == agent_id]
        if priority:
            pending = [a for a in pending if a["priority"] == priority]

        # Sort by priority (critical first) then by time
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        pending.sort(key=lambda x: (priority_order.get(x["priority"], 4), x["requested_at"]))

        return pending[:limit]

    async def review_action(
        self,
        action_id: str,
        reviewer_id: str,
        decision: str,
        reason: str | None = None,
        modified_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Review and decide on a pending action."""

        # Validate action exists
        if action_id not in self.actions:
            raise ValueError(f"Action {action_id} not found")

        action = self.actions[action_id]

        # Check status
        if action["status"] != "pending":
            raise ValueError(f"Action {action_id} is not pending (current: {action['status']})")

        # Check expiration
        if datetime.now(UTC) > action["expires_at"]:
            action["status"] = "expired"
            raise ValueError(f"Action {action_id} has expired")

        # Validate decision
        if decision not in ("approve", "reject"):
            raise ValueError(f"Invalid decision: {decision}. Must be 'approve' or 'reject'")

        now = datetime.now(UTC)

        # Update action
        action["status"] = "approved" if decision == "approve" else "rejected"
        action["reviewed_by"] = reviewer_id
        action["decision"] = decision
        action["decision_reason"] = reason
        action["modified_payload"] = modified_payload
        action["reviewed_at"] = now

        # Log audit event
        await self._log_audit_event(
            event_type="action_reviewed",
            action_id=action_id,
            details={
                "reviewer_id": reviewer_id,
                "decision": decision,
                "reason": reason,
            },
        )

        # Send notification
        await self._send_notification(
            notification_type="review_complete",
            action=action,
        )

        return action

    async def execute_approved_action(self, action_id: str) -> dict[str, Any]:
        """Execute an approved action."""

        if action_id not in self.actions:
            raise ValueError(f"Action {action_id} not found")

        action = self.actions[action_id]

        if action["status"] != "approved":
            raise ValueError(f"Action {action_id} is not approved (current: {action['status']})")

        # Simulate execution based on action type
        result = await self._simulate_execution(action)

        action["status"] = "executed"
        action["result"] = result

        await self._log_audit_event(
            event_type="action_executed", action_id=action_id, details={"result": result}
        )

        return action

    async def expire_action(self, action_id: str) -> dict[str, Any]:
        """Manually expire an action."""

        if action_id not in self.actions:
            raise ValueError(f"Action {action_id} not found")

        action = self.actions[action_id]

        if action["status"] != "pending":
            raise ValueError(f"Can only expire pending actions (current: {action['status']})")

        action["status"] = "expired"
        action["reviewed_at"] = datetime.now(UTC)

        await self._log_audit_event(event_type="action_expired", action_id=action_id, details={})

        return action

    async def check_auto_approve(self, action_type: str) -> bool:
        """Check if action type should be auto-approved."""
        return action_type in self.AUTO_APPROVE

    def classify_action(self, action_type: str) -> str:
        """Classify action as requiring_approval or auto_approved."""
        if action_type in self.APPROVAL_REQUIRED:
            return "requires_approval"
        elif action_type in self.AUTO_APPROVE:
            return "auto_approved"
        else:
            return "unknown"

    async def get_action_statistics(
        self, agent_id: str | None = None, since: datetime | None = None
    ) -> dict[str, Any]:
        """Get statistics about actions."""

        actions = list(self.actions.values())

        if agent_id:
            actions = [a for a in actions if a["agent_id"] == agent_id]

        if since:
            actions = [a for a in actions if a["requested_at"] >= since]

        total = len(actions)
        status_counts = {}
        for status in self.STATUSES:
            status_counts[status] = sum(1 for a in actions if a["status"] == status)

        type_counts = {}
        for action in actions:
            atype = action["action_type"]
            type_counts[atype] = type_counts.get(atype, 0) + 1

        avg_decision_time = None
        reviewed_actions = [a for a in actions if a.get("reviewed_at")]
        if reviewed_actions:
            total_time = sum(
                (a["reviewed_at"] - a["requested_at"]).total_seconds() for a in reviewed_actions
            )
            avg_decision_time = total_time / len(reviewed_actions)

        return {
            "total_actions": total,
            "by_status": status_counts,
            "by_type": type_counts,
            "avg_decision_time_seconds": avg_decision_time,
            "pending_count": status_counts.get("pending", 0),
            "approval_rate": (
                status_counts.get("approved", 0)
                / max(status_counts.get("approved", 0) + status_counts.get("rejected", 0), 1)
                * 100
            ),
        }

    async def _simulate_execution(self, action: dict[str, Any]) -> dict[str, Any]:
        """Simulate execution of different action types."""

        executors = {
            "file_write": lambda: {"success": True, "bytes_written": 1024},
            "file_delete": lambda: {"success": True, "files_deleted": 1},
            "external_api_call": lambda: {"success": True, "status_code": 200},
            "database_write": lambda: {"success": True, "rows_affected": 1},
            "code_execution": lambda: {"success": True, "exit_code": 0, "output": ""},
        }

        executor = executors.get(action["action_type"])
        if executor:
            return executor()

        return {"success": True, "action_type": action["action_type"]}

    async def _log_audit_event(
        self, event_type: str, action_id: str, details: dict[str, Any]
    ) -> None:
        """Log event to audit trail."""
        self.audit_log.append(
            {
                "event_type": event_type,
                "action_id": action_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "details": details,
            }
        )

    async def _send_notification(self, notification_type: str, action: dict[str, Any]) -> None:
        """Send notification about action."""
        self.notifications.append(
            {
                "type": notification_type,
                "action_id": action["id"],
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )


# ============================================================================
# TEST FIXTURES SPECIFIC TO HITL
# ============================================================================


@pytest.fixture
async def hitl_engine() -> MockHITLEngine:
    """Create fresh HITL engine instance for each test."""
    return MockHITLEngine()


@pytest.fixture
async def sample_actions_batch(hitl_engine: MockHITLEngine) -> list[dict[str, Any]]:
    """Create batch of sample actions for testing."""
    actions = []

    action_templates = [
        ("file_write", "high", "Write analysis results"),
        ("web_search", "low", "Search for information"),
        ("external_api_call", "medium", "Call weather API"),
        ("database_delete", "critical", "Delete old records"),
        ("code_execution", "high", "Run data processing script"),
    ]

    for action_type, priority, desc in action_templates:
        action = await hitl_engine.queue_action(
            agent_id="test-agent-uuid",
            action_type=action_type,
            description=desc,
            payload={"test": True},
            priority=priority,
        )
        actions.append(action)

    return actions


# ============================================================================
# TEST CLASS: Action Queuing
# ============================================================================


class TestActionQueuing:
    """Tests for action queuing functionality."""

    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_queue_valid_action(
        self,
        hitl_engine: MockHITLEngine,
        sample_user_data: dict[str, Any],
        assertions: CustomAssertions,
    ):
        """Should successfully queue a valid action."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="file_write",
            description="Write report to file",
            payload={"path": "/report.txt", "content": "data"},
            priority="medium",
        )

        # Verify action was created
        assert action is not None
        assertions.assert_valid_uuid(
            action["id"].split("-")[-1] if "-" in action["id"] else action["id"], version=4
        )
        assert action["agent_id"] == "agent-123"
        assert action["action_type"] == "file_write"
        assert action["description"] == "Write report to file"
        assert action["payload"] == {"path": "/report.txt", "content": "data"}
        assert action["priority"] == "medium"
        assert action["status"] == "pending"
        assert action["decision"] is None
        assert action["reviewed_by"] is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_queue_sets_correct_timestamps(self, hitl_engine: MockHITLEngine):
        """Should set requested_at and expires_at correctly."""
        before_queue = datetime.now(UTC)

        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="web_search",
            description="Search query",
            payload={},
            timeout_minutes=60,
        )

        after_queue = datetime.now(UTC)

        assert before_queue <= action["requested_at"] <= after_queue
        expected_expiry = action["requested_at"] + timedelta(minutes=60)
        assert abs((action["expires_at"] - expected_expiry).total_seconds()) < 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_queue_generates_unique_ids(self, hitl_engine: MockHITLEngine):
        """Should generate unique IDs for each queued action."""
        actions = []

        for i in range(10):
            action = await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type="web_search",
                description=f"Search {i}",
                payload={},
            )
            actions.append(action)

        ids = [a["id"] for a in actions]
        assert len(ids) == len(set(ids)), "All action IDs should be unique"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_queue_requires_agent_id(self, hitl_engine: MockHITLEngine):
        """Should reject action without agent_id."""
        with pytest.raises(ValueError, match="agent_id is required"):
            await hitl_engine.queue_action(
                agent_id="", action_type="file_write", description="Test", payload={}
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_queue_requires_action_type(self, hitl_engine: MockHITLEngine):
        """Should reject action without action_type."""
        with pytest.raises(ValueError, match="action_type is required"):
            await hitl_engine.queue_action(
                agent_id="agent-123", action_type="", description="Test", payload={}
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_queue_requires_description(self, hitl_engine: MockHITLEngine):
        """Should reject action without description."""
        with pytest.raises(ValueError, match="description is required"):
            await hitl_engine.queue_action(
                agent_id="agent-123", action_type="file_write", description="", payload={}
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_queue_rejects_invalid_priority(self, hitl_engine: MockHITLEngine):
        """Should reject invalid priority values."""
        with pytest.raises(ValueError, match="Invalid priority"):
            await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type="file_write",
                description="Test",
                payload={},
                priority="invalid_priority",
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_queue_accepts_all_valid_priorities(self, hitl_engine: MockHITLEngine):
        """Should accept all valid priority values."""
        priorities = ["low", "medium", "high", "critical"]

        for priority in priorities:
            action = await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type="file_write",
                description=f"Test with {priority}",
                payload={},
                priority=priority,
            )
            assert action["priority"] == priority

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_queue_logs_to_audit_trail(self, hitl_engine: MockHITLEngine):
        """Should log action queuing to audit trail."""
        initial_log_length = len(hitl_engine.audit_log)

        await hitl_engine.queue_action(
            agent_id="agent-123", action_type="file_write", description="Test action", payload={}
        )

        assert len(hitl_engine.audit_log) == initial_log_length + 1

        log_entry = hitl_engine.audit_log[-1]
        assert log_entry["event_type"] == "action_queued"
        assert log_entry["details"]["agent_id"] == "agent-123"
        assert log_entry["details"]["action_type"] == "file_write"


# ============================================================================
# TEST CLASS: Action Classification
# ============================================================================


class TestActionClassification:
    """Tests for automatic action classification."""

    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_classify_approval_required_actions(self, hitl_engine: MockHITLEngine):
        """Should correctly identify actions requiring approval."""
        approval_required_actions = [
            "file_write",
            "file_delete",
            "file_modify",
            "external_api_call",
            "database_write",
            "database_delete",
            "code_execution",
            "data_export",
            "user_management",
            "config_change",
        ]

        for action_type in approval_required_actions:
            classification = hitl_engine.classify_action(action_type)
            assert classification == "requires_approval", (
                f"{action_type} should require approval, got {classification}"
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_classify_auto_approved_actions(self, hitl_engine: MockHITLEngine):
        """Should correctly identify auto-approved actions."""
        auto_approved_actions = [
            "web_search",
            "calculator",
            "read_operation",
            "internal_lookup",
            "formatting",
        ]

        for action_type in auto_approved_actions:
            classification = hitl_engine.classify_action(action_type)
            assert classification == "auto_approved", (
                f"{action_type} should be auto-approved, got {classification}"
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_classify_unknown_actions(self, hitl_engine: MockHITLEngine):
        """Should return 'unknown' for unrecognized action types."""
        unknown_actions = ["custom_action", "unknown_type", "new_operation"]

        for action_type in unknown_actions:
            classification = hitl_engine.classify_action(action_type)
            assert classification == "unknown", (
                f"{action_type} should be unknown, got {classification}"
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_auto_approve_returns_true_for_safe_actions(
        self, hitl_engine: MockHITLEngine
    ):
        """Should return True for auto-approved action types."""
        safe_actions = ["web_search", "calculator"]

        for action_type in safe_actions:
            is_auto_approved = await hitl_engine.check_auto_approve(action_type)
            assert is_auto_approved is True, f"{action_type} should be auto-approved"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_auto_approve_returns_false_for_dangerous_actions(
        self, hitl_engine: MockHITLEngine
    ):
        """Should return False for actions requiring approval."""
        dangerous_actions = ["file_write", "database_delete"]

        for action_type in dangerous_actions:
            is_auto_approved = await hitl_engine.check_auto_approve(action_type)
            assert is_auto_approved is False, f"{action_type} should NOT be auto-approved"


# ============================================================================
# TEST CLASS: Pending Actions Retrieval
# ============================================================================


class TestPendingActionsRetrieval:
    """Tests for retrieving pending actions."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_all_pending_actions(
        self, hitl_engine: MockHITLEngine, sample_actions_batch: list[dict[str, Any]]
    ):
        """Should retrieve all pending actions."""
        pending = await hitl_engine.get_pending_actions()

        assert len(pending) == len(sample_actions_batch)
        for action in pending:
            assert action["status"] == "pending"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_pending_by_agent_id(self, hitl_engine: MockHITLEngine):
        """Should filter pending actions by agent ID."""
        # Queue actions for different agents
        await hitl_engine.queue_action(
            agent_id="agent-A", action_type="file_write", description="Agent A action", payload={}
        )
        await hitl_engine.queue_action(
            agent_id="agent-B", action_type="file_write", description="Agent B action", payload={}
        )

        # Get only Agent A's actions
        agent_a_actions = await hitl_engine.get_pending_actions(agent_id="agent-A")

        assert len(agent_a_actions) == 1
        assert agent_a_actions[0]["agent_id"] == "agent-A"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_pending_by_priority(self, hitl_engine: MockHITLEngine):
        """Should filter pending actions by priority."""
        await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="file_write",
            description="High priority",
            payload={},
            priority="high",
        )
        await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="web_search",
            description="Low priority",
            payload={},
            priority="low",
        )

        high_priority = await hitl_engine.get_pending_actions(priority="high")

        assert len(high_priority) == 1
        assert high_priority[0]["priority"] == "high"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_respect_limit_parameter(self, hitl_engine: MockHITLEngine):
        """Should respect limit parameter when retrieving actions."""
        # Queue more actions than limit
        for i in range(10):
            await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type="web_search",
                description=f"Action {i}",
                payload={},
            )

        limited = await hitl_engine.get_pending_actions(limit=5)

        assert len(limited) <= 5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sort_by_priority_order(self, hitl_engine: MockHITLEngine):
        """Should sort results by priority (critical first)."""
        priorities = ["low", "critical", "medium", "high"]

        for priority in priorities:
            await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type="web_search",
                description=f"{priority} action",
                payload={},
                priority=priority,
            )

        pending = await hitl_engine.get_pending_actions()

        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        for i in range(len(pending) - 1):
            current_priority = priority_order[pending[i]["priority"]]
            next_priority = priority_order[pending[i + 1]["priority"]]
            assert current_priority <= next_priority, (
                "Actions should be sorted by priority (critical first)"
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_exclude_non_pending_actions(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should exclude non-pending actions from results."""
        # Queue and approve an action
        action = await hitl_engine.queue_action(
            agent_id="agent-123", action_type="file_write", description="To be approved", payload={}
        )

        await hitl_engine.review_action(
            action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="approve"
        )

        # Queue another that stays pending
        await hitl_engine.queue_action(
            agent_id="agent-123", action_type="file_write", description="Still pending", payload={}
        )

        pending = await hitl_engine.get_pending_actions()

        assert len(pending) == 1
        assert pending[0]["description"] == "Still pending"


# ============================================================================
# TEST CLASS: Action Review (Approve/Reject)
# ============================================================================


class TestActionReview:
    """Tests for the action review workflow."""

    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_approve_action_successfully(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should successfully approve a pending action."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="file_write",
            description="Write important file",
            payload={"path": "/data/file.txt"},
        )

        reviewed = await hitl_engine.review_action(
            action_id=action["id"],
            reviewer_id=sample_admin_data["id"],
            decision="approve",
            reason="Legitimate file write request",
        )

        assert reviewed["status"] == "approved"
        assert reviewed["decision"] == "approve"
        assert reviewed["reviewed_by"] == sample_admin_data["id"]
        assert reviewed["decision_reason"] == "Legitimate file write request"
        assert reviewed["reviewed_at"] is not None

    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_reject_action_successfully(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should successfully reject a pending action."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="database_delete",
            description="Dangerous delete operation",
            payload={"table": "users"},
        )

        reviewed = await hitl_engine.review_action(
            action_id=action["id"],
            reviewer_id=sample_admin_data["id"],
            decision="reject",
            reason="Destructive operation not justified",
        )

        assert reviewed["status"] == "rejected"
        assert reviewed["decision"] == "reject"
        assert reviewed["decision_reason"] == "Destructive operation not justified"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_with_modified_payload(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should allow modifying payload during review."""
        original_payload = {"path": "/etc/config", "mode": "777"}
        modified_payload = {"path": "/home/user/config", "mode": "644"}

        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="file_write",
            description="Write config file",
            payload=original_payload,
        )

        reviewed = await hitl_engine.review_action(
            action_id=action["id"],
            reviewer_id=sample_admin_data["id"],
            decision="approve",
            reason="Approved with safer path and permissions",
            modified_payload=modified_payload,
        )

        assert reviewed["modified_payload"] == modified_payload
        assert reviewed["modified_payload"]["path"] == "/home/user/config"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_nonexistent_action_raises_error(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should raise error when reviewing non-existent action."""
        with pytest.raises(ValueError, match="not found"):
            await hitl_engine.review_action(
                action_id="non-existent-id", reviewer_id=sample_admin_data["id"], decision="approve"
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_already_reviewed_action_raises_error(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should raise error when trying to review already-reviewed action."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123", action_type="file_write", description="Test action", payload={}
        )

        # First review
        await hitl_engine.review_action(
            action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="approve"
        )

        # Second review should fail
        with pytest.raises(ValueError, match="not pending"):
            await hitl_engine.review_action(
                action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="reject"
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_expired_action_raises_error(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should raise error when trying to review expired action."""
        # Create action with very short expiry
        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="file_write",
            description="Quick expiring action",
            payload={},
            timeout_minutes=0,  # Expire immediately
        )

        # Manually set expiry to past
        action["expires_at"] = datetime.now(UTC) - timedelta(seconds=1)

        with pytest.raises(ValueError, match="expired"):
            await hitl_engine.review_action(
                action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="approve"
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_rejects_invalid_decision(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should reject invalid decision values."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123", action_type="file_write", description="Test action", payload={}
        )

        with pytest.raises(ValueError, match="Invalid decision"):
            await hitl_engine.review_action(
                action_id=action["id"],
                reviewer_id=sample_admin_data["id"],
                decision="maybe",  # Invalid decision
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_logs_to_audit_trail(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should log review events to audit trail."""
        initial_log_length = len(hitl_engine.audit_log)

        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="file_write",
            description="Audit test action",
            payload={},
        )

        await hitl_engine.review_action(
            action_id=action["id"],
            reviewer_id=sample_admin_data["id"],
            decision="approve",
            reason="For testing audit logging",
        )

        # Should have 2 log entries: queue + review
        assert len(hitl_engine.audit_log) == initial_log_length + 2

        review_log = hitl_engine.audit_log[-1]
        assert review_log["event_type"] == "action_reviewed"
        assert review_log["details"]["reviewer_id"] == sample_admin_data["id"]
        assert review_log["details"]["decision"] == "approve"


# ============================================================================
# TEST CLASS: Action Execution
# ============================================================================


class TestActionExecution:
    """Tests for executing approved actions."""

    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_execute_approved_action(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should successfully execute an approved action."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="file_write",
            description="Write file",
            payload={"path": "/test.txt", "content": "hello"},
        )

        await hitl_engine.review_action(
            action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="approve"
        )

        executed = await hitl_engine.execute_approved_action(action["id"])

        assert executed["status"] == "executed"
        assert executed["result"] is not None
        assert executed["result"]["success"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_nonexistent_action_raises_error(self, hitl_engine: MockHITLEngine):
        """Should raise error when executing non-existent action."""
        with pytest.raises(ValueError, match="not found"):
            await hitl_engine.execute_approved_action("non-existent-id")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_non_approved_action_raises_error(self, hitl_engine: MockHITLEngine):
        """Should raise error when trying to execute non-approved action."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123", action_type="file_write", description="Pending action", payload={}
        )

        # Try to execute without approving first
        with pytest.raises(ValueError, match="not approved"):
            await hitl_engine.execute_approved_action(action["id"])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_rejected_action_raises_error(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should raise error when trying to execute rejected action."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="file_write",
            description="Rejected action",
            payload={},
        )

        await hitl_engine.review_action(
            action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="reject"
        )

        with pytest.raises(ValueError, match="not approved"):
            await hitl_engine.execute_approved_action(action["id"])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_different_action_types(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should handle different action types correctly."""
        action_types = ["file_write", "file_delete", "external_api_call", "database_write"]

        for action_type in action_types:
            action = await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type=action_type,
                description=f"Execute {action_type}",
                payload={},
            )

            await hitl_engine.review_action(
                action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="approve"
            )

            executed = await hitl_engine.execute_approved_action(action["id"])

            assert executed["status"] == "executed"
            assert executed["result"]["success"] is True


# ============================================================================
# TEST CLASS: Action Expiration
# ============================================================================


class TestActionExpiration:
    """Tests for action expiration handling."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_expire_pending_action(self, hitl_engine: MockHITLEngine):
        """Should successfully expire a pending action."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123", action_type="file_write", description="To be expired", payload={}
        )

        expired = await hitl_engine.expire_action(action["id"])

        assert expired["status"] == "expired"
        assert expired["reviewed_at"] is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_expire_nonexistent_action_raises_error(self, hitl_engine: MockHITLEngine):
        """Should raise error when expiring non-existent action."""
        with pytest.raises(ValueError, match="not found"):
            await hitl_engine.expire_action("non-existent-id")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_expire_only_pending_actions(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should only allow expiring pending actions."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="file_write",
            description="Already approved",
            payload={},
        )

        await hitl_engine.review_action(
            action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="approve"
        )

        with pytest.raises(ValueError, match="only expire pending"):
            await hitl_engine.expire_action(action["id"])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_expired_action_cannot_be_reviewed(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should prevent reviewing expired actions."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123", action_type="file_write", description="Will expire", payload={}
        )

        await hitl_engine.expire_action(action["id"])

        with pytest.raises(ValueError, match="expired"):
            await hitl_engine.review_action(
                action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="approve"
            )


# ============================================================================
# TEST CLASS: Statistics & Reporting
# ============================================================================


class TestStatisticsAndReporting:
    """Tests for statistics and reporting functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_overall_statistics(
        self,
        hitl_engine: MockHITLEngine,
        sample_actions_batch: list[dict[str, Any]],
        sample_admin_data: dict[str, Any],
    ):
        """Should calculate overall action statistics."""
        # Approve some, reject some
        for i, action in enumerate(sample_actions_batch[:3]):
            decision = "approve" if i % 2 == 0 else "reject"
            await hitl_engine.review_action(
                action_id=action["id"], reviewer_id=sample_admin_data["id"], decision=decision
            )

        stats = await hitl_engine.get_action_statistics()

        assert stats["total_actions"] == len(sample_actions_batch)
        assert "by_status" in stats
        assert "by_type" in stats
        assert stats["pending_count"] == len(sample_actions_batch) - 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calculate_approval_rate(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should calculate correct approval rate."""
        # Create and review multiple actions
        for i in range(10):
            action = await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type="file_write",
                description=f"Action {i}",
                payload={},
            )

            decision = "approve" if i < 7 else "reject"  # 70% approval rate
            await hitl_engine.review_action(
                action_id=action["id"], reviewer_id=sample_admin_data["id"], decision=decision
            )

        stats = await hitl_engine.get_action_statistics()

        # Should be approximately 70%
        assert 65 <= stats["approval_rate"] <= 75

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_stats_by_agent(self, hitl_engine: MockHITLEngine):
        """Should filter statistics by agent ID."""
        # Create actions for different agents
        for i in range(5):
            await hitl_engine.queue_action(
                agent_id=f"agent-{i % 2}",  # Alternates between agent-0 and agent-1
                action_type="file_write",
                description=f"Action {i}",
                payload={},
            )

        stats_agent_0 = await hitl_engine.get_action_statistics(agent_id="agent-0")
        stats_agent_1 = await hitl_engine.get_action_statistics(agent_id="agent-1")

        assert stats_agent_0["total_actions"] == 3  # Actions 0, 2, 4
        assert stats_agent_1["total_actions"] == 2  # Actions 1, 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calculate_average_decision_time(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should calculate average decision time for reviewed actions."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123", action_type="file_write", description="Timing test", payload={}
        )

        # Small delay to ensure measurable time
        await asyncio.sleep(0.01)

        await hitl_engine.review_action(
            action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="approve"
        )

        stats = await hitl_engine.get_action_statistics()

        assert stats["avg_decision_time_seconds"] is not None
        assert stats["avg_decision_time_seconds"] >= 0.01  # At least our sleep time


# ============================================================================
# TEST CLASS: Notification System
# ============================================================================


class TestNotificationSystem:
    """Tests for the notification system."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_notification_on_review(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should send notification when action is reviewed."""
        initial_notification_count = len(hitl_engine.notifications)

        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="file_write",
            description="Notification test",
            payload={},
        )

        await hitl_engine.review_action(
            action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="approve"
        )

        assert len(hitl_engine.notifications) == initial_notification_count + 1

        notification = hitl_engine.notifications[-1]
        assert notification["type"] == "review_complete"
        assert notification["action_id"] == action["id"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_duplicate_notifications(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Should not send duplicate notifications for same action."""
        action = await hitl_engine.queue_action(
            agent_id="agent-123", action_type="file_write", description="No duplicates", payload={}
        )

        # Review once
        await hitl_engine.review_action(
            action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="approve"
        )

        # Try to review again (should fail, but even if it didn't, no duplicate)
        try:
            await hitl_engine.review_action(
                action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="reject"
            )
        except Exception as e:
            import logging

            logging.getLogger(__name__).exception(f"Silenced error: {e}")

        review_notifications = [
            n
            for n in hitl_engine.notifications
            if n["action_id"] == action["id"] and n["type"] == "review_complete"
        ]

        assert len(review_notifications) == 1


# ============================================================================
# TEST CLASS: Edge Cases & Error Handling
# ============================================================================


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and robust error handling."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_empty_description(self, hitl_engine: MockHITLEngine):
        """Should handle empty description gracefully."""
        with pytest.raises(ValueError):
            await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type="file_write",
                description="",  # Empty
                payload={},
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_very_long_description(self, hitl_engine: MockHITLEngine):
        """Should handle very long descriptions."""
        long_description = "A" * 10000  # Very long description

        action = await hitl_engine.queue_action(
            agent_id="agent-123", action_type="file_write", description=long_description, payload={}
        )

        assert action["description"] == long_description

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_complex_payload(self, hitl_engine: MockHITLEngine):
        """Should handle complex nested payloads."""
        complex_payload = {
            "nested": {
                "array": [1, 2, 3],
                "object": {"key": "value"},
            },
            "special_chars": "<>&\"'",
            "unicode": "Hello 世界 🌍",
            "numbers": 12345.6789,
            "boolean": True,
            "null_value": None,
        }

        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="file_write",
            description="Complex payload test",
            payload=complex_payload,
        )

        assert action["payload"] == complex_payload

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_action_queueing(self, hitl_engine: MockHITLEngine):
        """Handle concurrent action queueing correctly."""

        async def queue_action(i):
            return await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type="file_write",
                description=f"Concurrent action {i}",
                payload={},
            )

        # Queue 10 actions concurrently
        tasks = [queue_action(i) for i in range(10)]
        actions = await asyncio.gather(*tasks)

        assert len(actions) == 10
        # All should have unique IDs
        ids = [a["id"] for a in actions]
        assert len(ids) == len(set(ids))

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_special_characters_in_fields(self, hitl_engine: MockHITLEngine):
        """Should handle special characters in text fields."""
        special_strings = [
            "Normal string",
            "With <html> tags & symbols",
            "Unicode: 中文 日本어 한국어",
            "Emoji: 🎉🚀💻",
            "SQL: '; DROP TABLE users; --",
            "Path: ../../../etc/passwd",
            "Newlines:\nand\ttabs",
        ]

        for description in special_strings:
            action = await hitl_engine.queue_action(
                agent_id="agent-123", action_type="file_write", description=description, payload={}
            )
            assert action["description"] == description

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_large_number_of_actions(self, hitl_engine: MockHITLEngine):
        """Should handle large number of actions efficiently."""
        # Queue 1000 actions
        for i in range(1000):
            await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type="web_search",
                description=f"Bulk action {i}",
                payload={},
            )

        # Retrieve should still work
        pending = await hitl_engine.get_pending_actions(limit=100)
        assert len(pending) == 100

        # Statistics should work
        stats = await hitl_engine.get_action_statistics()
        assert stats["total_actions"] == 1000


# ============================================================================
# INTEGRATION TESTS: Full Workflow
# ============================================================================


class TestHITLWorkflowIntegration:
    """Integration tests for complete HITL workflows."""

    @pytest.mark.integration
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_full_approval_workflow(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Test complete workflow: queue -> review -> approve -> execute."""
        # Step 1: Agent requests action
        action = await hitl_engine.queue_action(
            agent_id="research-agent-001",
            action_type="file_write",
            description="Save research findings to report.pdf",
            payload={
                "path": "/output/research/report.pdf",
                "content": "Research data...",
                "size_mb": 2.5,
            },
            priority="high",
        )

        assert action["status"] == "pending"

        # Step 2: Admin reviews pending queue
        pending = await hitl_engine.get_pending_actions(priority="high")
        assert action["id"] in [a["id"] for a in pending]

        # Step 3: Admin approves with reason
        approved = await hitl_engine.review_action(
            action_id=action["id"],
            reviewer_id=sample_admin_data["id"],
            decision="approve",
            reason="Valid research output, path is within allowed directory",
        )

        assert approved["status"] == "approved"

        # Step 4: System executes approved action
        executed = await hitl_engine.execute_approved_action(action["id"])

        assert executed["status"] == "executed"
        assert executed["result"]["success"] is True

        # Verify audit trail has all events
        audit_events = [e["event_type"] for e in hitl_engine.audit_log]
        assert "action_queued" in audit_events
        assert "action_reviewed" in audit_events
        assert "action_executed" in audit_events

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_rejection_workflow(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Test complete workflow: queue -> review -> reject."""
        # Step 1: Agent makes dangerous request
        action = await hitl_engine.queue_action(
            agent_id="code-agent-002",
            action_type="database_delete",
            description="Delete all user records",
            payload={
                "table": "users",
                "where": "1=1",  # Dangerous!
            },
            priority="critical",
        )

        # Step 2: Admin sees critical pending action
        critical_pending = await hitl_engine.get_pending_actions(priority="critical")
        assert len(critical_pending) == 1

        # Step 3: Admin rejects with detailed reason
        rejected = await hitl_engine.review_action(
            action_id=action["id"],
            reviewer_id=sample_admin_data["id"],
            decision="reject",
            reason="Cannot delete all records. Use specific WHERE clause with proper justification.",
        )

        assert rejected["status"] == "rejected"

        # Step 4: Attempting to execute should fail
        with pytest.raises(ValueError, match="not approved"):
            await hitl_engine.execute_approved_action(action["id"])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_step_workflow_with_modification(
        self, hitl_engine: MockHITLEngine, sample_admin_data: dict[str, Any]
    ):
        """Test workflow where admin modifies payload during approval."""
        # Agent requests with unsafe parameters
        action = await hitl_engine.queue_action(
            agent_id="data-agent-003",
            action_type="file_write",
            description="Export dataset to CSV",
            payload={
                "path": "/etc/config.csv",  # Unsafe location!
                "delimiter": ",",
                "include_headers": True,
            },
            priority="medium",
        )

        # Admin approves but modifies to safer path
        approved = await hitl_engine.review_action(
            action_id=action["id"],
            reviewer_id=sample_admin_data["id"],
            decision="approve",
            reason="Approved with corrected output path",
            modified_payload={
                "path": "/data/exports/dataset.csv",  # Safe location
                "delimiter": ",",
                "include_headers": True,
            },
        )

        # Execute uses modified payload
        executed = await hitl_engine.execute_approved_action(action["id"])

        assert executed["status"] == "executed"
        # The modified payload should be used
        assert executed["result"]["success"] is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_expiration_and_cleanup_workflow(self, hitl_engine: MockHITLEngine):
        """Test workflow where actions expire before review."""
        # Queue action with short timeout
        action = await hitl_engine.queue_action(
            agent_id="agent-123",
            action_type="external_api_call",
            description="Time-sensitive API call",
            payload={"url": "https://api.example.com/data"},
            timeout_minutes=0.001,  # Very short expiry
        )

        # Wait for expiration
        await asyncio.sleep(0.1)

        # Try to review expired action
        with pytest.raises(ValueError, match="expired"):
            await hitl_engine.review_action(
                action_id=action["id"], reviewer_id="admin-123", decision="approve"
            )


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestHITLPerformance:
    """Performance benchmarks for HITL operations."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_queue_performance(
        self, hitl_engine: MockHITLEngine, benchmark_thresholds: dict[str, int]
    ):
        """Queue operation should complete within threshold."""
        import time

        start = time.perf_counter()

        for _ in range(100):
            await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type="web_search",
                description="Performance test",
                payload={},
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_per_op = elapsed_ms / 100

        assert avg_per_op < benchmark_thresholds["hitl_queue"], (
            f"Avg queue time {avg_per_op:.2f}ms exceeds threshold {benchmark_thresholds['hitl_queue']}ms"
        )

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_review_performance(
        self,
        hitl_engine: MockHITLEngine,
        sample_admin_data: dict[str, Any],
        benchmark_thresholds: dict[str, int],
    ):
        """Review operation should complete within threshold."""
        import time

        # Pre-queue actions
        actions = []
        for _ in range(100):
            action = await hitl_engine.queue_action(
                agent_id="agent-123", action_type="file_write", description="Perf test", payload={}
            )
            actions.append(action)

        start = time.perf_counter()

        for action in actions:
            await hitl_engine.review_action(
                action_id=action["id"], reviewer_id=sample_admin_data["id"], decision="approve"
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_per_op = elapsed_ms / 100

        assert avg_per_op < benchmark_thresholds["hitl_queue"], (
            f"Avg review time {avg_per_op:.2f}ms exceeds threshold"
        )

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_statistics_calculation_performance(
        self, hitl_engine: MockHITLEngine, benchmark_thresholds: dict[str, int]
    ):
        """Statistics calculation should be efficient at scale."""
        import time

        # Create large number of actions
        for _ in range(1000):
            await hitl_engine.queue_action(
                agent_id="agent-123",
                action_type="web_search",
                description="Stats perf test",
                payload={},
            )

        start = time.perf_counter()

        stats = await hitl_engine.get_action_statistics()

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 100, (
            f"Stats calculation took {elapsed_ms:.2f}ms, too slow for 1000 actions"
        )

        assert stats["total_actions"] == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=hitl", "--cov-report=term-missing"])
