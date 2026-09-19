from datetime import UTC, datetime
from typing import Any, Optional

from core.logging_config import logger
from database.tenant_db import TenantAwareFirestore

from .hitl_ledger import HITLAuditLedger


class HITLEngine:
    """
    Human-In-The-Loop Engine.
    Handles the suspension, approval, and rejection of skills/workflows that require human oversight.
    """

    def __init__(self, db: TenantAwareFirestore):
        # বাংলা (M17 P-C, fail-closed): আগে db-শূন্য/বিকৃত স্টোরে নীরবভাবে
        # নির্মিত হতো এবং প্রথম অপারেশনে AttributeError → নীরব []/ব্যর্থতা।
        # এখন স্টোর-চুক্তি স্পষ্ট: ব্যবহারযোগ্য `.client` ছাড়া HITLEngine গড়াই
        # নিষিদ্ধ — অনুপস্থিত স্টোর নির্মাণেই লাউড-ব্যর্থ হয়, ভান নেই।
        if db is None or getattr(db, "client", None) is None:
            raise RuntimeError(
                "HITLEngine requires a durable store exposing a usable `.client` "
                "— refusing to construct without one (fail-closed, M17 P-C)"
            )
        self.db = db
        self.collection_name = "pending_approvals"
        self.ledger = HITLAuditLedger(db=self.db)

    def suspend_for_approval(self, target_resource: str, payload: dict[str, Any]) -> str:
        """
        Suspend an action for human approval.
        Returns the ID of the pending approval record.
        """
        # Create a pending approval record
        record_id = target_resource
        now = datetime.now(UTC).isoformat()

        pending_record = {
            "id": record_id,
            "target_resource": target_resource,
            "payload": payload,
            "status": "pending_approval",
            "created_at": now,
            "updated_at": now,
        }

        try:
            self.db.client.collection(self.collection_name).document(record_id).set(pending_record)
            logger.info(f"?? [HITLEngine] Suspended '{target_resource}' for human approval.")
        except Exception as e:
            logger.error(f"?[HITLEngine] Failed to suspend '{target_resource}': {e}")
            raise RuntimeError(f"Failed to suspend action for HITL: {e}")

        # Log to ledger
        self.ledger.record_entry_sync(
            agent_id="system",
            action="suspend_for_approval",
            payload={"target_resource": target_resource, "record_id": record_id},
        )

        return record_id

    def get_pending_approvals(self) -> list[dict[str, Any]]:
        """
        Retrieve all pending approvals.

        বাংলা (M17 P-C): আগে স্টোর-ত্রুটিতে নীরবে [] ফেরত দিত — admin কিউ
        ফাঁকা দেখিয়ে ভান করত যে কিছুই অনুমোদনের অপেক্ষায় নেই। এখন ত্রুটি
        লাউড RuntimeError — রুট স্তরে 500 হয়ে স্পষ্ট হবে, কখনো ভান নয়।
        """
        try:
            ref = self.db.client.collection(self.collection_name)
            query = ref.where("status", "==", "pending_approval")
            docs = list(query.stream())
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"[HITLEngine] Failed to fetch pending approvals: {e}")
            raise RuntimeError(f"HITL queue is UNAVAILABLE (store read failed): {e}") from e

    def get_pending_approval(self, record_id: str) -> dict[str, Any] | None:
        """
        Retrieve a specific pending approval by ID.
        """
        try:
            doc = self.db.client.collection(self.collection_name).document(record_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"?[HITLEngine] Failed to fetch pending approval {record_id}: {e}")
            return None

    def approve(self, admin_user_id: str, record_id: str) -> dict[str, Any]:
        """
        Approve a pending action.
        """
        doc_ref = self.db.client.collection(self.collection_name).document(record_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise ValueError(f"Pending approval record {record_id} not found.")

        record = doc.to_dict()
        if record.get("status") != "pending_approval":
            raise ValueError(f"Record {record_id} is not in pending state.")

        # Update status
        now = datetime.now(UTC).isoformat()
        doc_ref.update({"status": "approved", "approved_by": admin_user_id, "updated_at": now})

        # Log to ledger
        self.ledger.record_entry_sync(
            agent_id=admin_user_id,
            action="skill_approved",
            payload={"target_resource": record.get("target_resource"), "record_id": record_id},
        )

        logger.info(f"? [HITLEngine] Admin {admin_user_id} approved '{record_id}'.")
        return record

    def reject(self, admin_user_id: str, record_id: str, reason: str = "") -> dict[str, Any]:
        """
        Reject a pending action.
        """
        doc_ref = self.db.client.collection(self.collection_name).document(record_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise ValueError(f"Pending approval record {record_id} not found.")

        record = doc.to_dict()
        if record.get("status") != "pending_approval":
            raise ValueError(f"Record {record_id} is not in pending state.")

        # Update status
        now = datetime.now(UTC).isoformat()
        doc_ref.update(
            {
                "status": "rejected",
                "rejected_by": admin_user_id,
                "rejection_reason": reason,
                "updated_at": now,
            }
        )

        # Log to ledger
        self.ledger.record_entry_sync(
            agent_id=admin_user_id,
            action="skill_rejected",
            payload={
                "target_resource": record.get("target_resource"),
                "record_id": record_id,
                "reason": reason,
            },
        )

        logger.warning(
            f"?? [HITLEngine] Admin {admin_user_id} rejected '{record_id}'. Reason: {reason}"
        )
        return record
