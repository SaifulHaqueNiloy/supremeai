import time
from typing import Any

from fastapi import BackgroundTasks

from core.logging_config import logger
from core.security.cryptographic_ledger import CryptographicLedger
from database.tenant_db import TenantAwareFirestore


class HITLAuditLedger(CryptographicLedger):
    """
    Persistent Cryptographic Ledger for HITL approvals.
    Extends the in-memory CryptographicLedger to persist blocks in Firestore.
    """

    def __init__(self, db: TenantAwareFirestore):
        super().__init__()
        self.db = db
        self.collection_name = "hitl_audit_ledger"
        self._initialize_from_db()

    def _initialize_from_db(self):
        """
        Load the last hash from the database to continue the chain.
        """
        try:
            # Get the latest block by index descending
            ref = self.db.client.collection(self.collection_name)
            query = ref.order_by("index", direction="DESCENDING").limit(1)
            docs = list(query.stream())

            if docs:
                latest_block = docs[0].to_dict()
                self.last_hash = latest_block.get("hash", self.genesis_hash)
                # Note: We don't need to load the entire chain into memory just to append.
                # The length is needed for index calculation. We can just use the latest block index.
                self._current_index = latest_block.get("index", 0)
            else:
                self._current_index = 0
                self.last_hash = self.genesis_hash
        except Exception as e:
            logger.error(f"[HITLAuditLedger] Failed to initialize from DB: {e}")
            self._current_index = 0

    def record_entry_sync(
        self, agent_id: str, action: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Override to persist the block to Firestore after generating it.
        """
        timestamp = time.time()
        current_hash = self._compute_hash(self.last_hash, timestamp, agent_id, payload)

        self._current_index += 1
        block = {
            "index": self._current_index,
            "previous_hash": self.last_hash,
            "timestamp": timestamp,
            "agent_id": agent_id,
            "action": action,
            "payload": payload,
            "hash": current_hash,
        }

        self.last_hash = current_hash

        # Save to DB
        try:
            doc_ref = self.db.client.collection(self.collection_name).document(current_hash)
            doc_ref.set(block)
            logger.info(
                f"[HITLAuditLedger] Saved entry #{block['index']} to Firestore. Hash: {current_hash[:12]}..."
            )
        except Exception as e:
            logger.error(f"[HITLAuditLedger] Failed to save entry to Firestore: {e}")

        return block
