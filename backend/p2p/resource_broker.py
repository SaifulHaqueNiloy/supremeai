"""P2P Resource Broker for SupremeAI 2.0.

বাংলা: P2P কম্পিউট রিসোর্স শেয়ারিং, নোড ম্যাচমেকিং, জিরো-ট্রাস্ট স্যান্ডবক্সিং এবং ক্রিপ্টোগ্রাফিক প্রুফ ভ্যালিডেশন।
"""

import logging
import time
from typing import Any

from core.microvm_sandbox import run_in_sandbox
from backend.p2p.credit_system import credit_system

logger = logging.getLogger("supremeai.p2p.resource_broker")


class P2PResourceBroker:
    """Brokers compute requests between resource providers and consumers inside isolated Sandboxes."""

    def __init__(self):
        self._active_nodes: dict[str, dict[str, Any]] = {}

    def register_node(
        self,
        node_id: str,
        owner_id: str,
        capabilities: dict[str, Any],
        public_key_pem: str | None = None,
    ) -> dict[str, Any]:
        """Register a peer node capable of providing compute resources inside Zero-Trust Sandbox.

        বাংলা: নতুন P2P কম্পিউট প্রোভাইডার নোড রেজিস্টার করার সময় পাবলিসিটি কি ও স্যান্ডবক্স ক্যাপাবিলিটি সংগৃহীত হয়।
        """
        node_info = {
            "node_id": node_id,
            "owner_id": owner_id,
            "capabilities": capabilities,
            "public_key": public_key_pem,
            "registered_at": time.time(),
            "last_heartbeat": time.time(),
            "status": "idle",
            "sandboxed": True,
        }
        self._active_nodes[node_id] = node_info
        logger.info(f"P2P Zero-Trust Node registered: {node_id} (owner: {owner_id}, sandbox=True)")
        return node_info

    def find_best_node(self, required_capability: str, min_credits: float = 1.0) -> dict[str, Any] | None:
        """Find an idle node matching the capability requirements.

        বাংলা: চাওয়া কম্পিউট ক্ষমতার উপর ভিত্তি করে স্যান্ডবক্সড সেরা নোড খুঁজে বের করে।
        """
        now = time.time()
        for node_id, node in self._active_nodes.items():
            # Filter stale heartbeats (> 60s)
            if now - node["last_heartbeat"] > 60:
                continue
            if node["status"] == "idle" and node["capabilities"].get(required_capability, False):
                return node
        return None

    async def execute_sandboxed_task(self, task_code: str, node_id: str) -> dict[str, Any]:
        """
        Execute incoming untrusted peer code strictly inside MicroVM / Container Sandbox.
        বাংলা মন্তব্য: জিরো-ট্রাস্ট সিকিউরিটির জন্য P2P নোডের নির্দেশ সরাসরি লোকাল সার্ভারে না চালিয়ে মাইক্রোভিএম স্যান্ডবক্সে এক্সিকিউট করা হয়।
        """
        logger.info(f"Executing P2P Task inside Zero-Trust MicroVM Sandbox for node {node_id}")
        result = await run_in_sandbox(task_code, timeout_seconds=30.0)
        return result

    def allocate_task(self, consumer_id: str, required_capability: str, cost: float) -> dict[str, Any]:
        """Match and allocate a task to a provider node, deducting credits.

        বাংলা: টাস্ক বরাদ্দ করে এবং ক্রেডিট লেজার অ্যাডজাস্ট করে।
        """
        consumer_balance = credit_system.get_balance(consumer_id)
        if consumer_balance < cost:
            return {"status": "error", "message": f"Insufficient credits ({consumer_balance} < {cost})"}

        node = self.find_best_node(required_capability)
        if not node:
            return {"status": "error", "message": "No available P2P provider nodes matching requirements"}

        # Transfer credits via credit_system ledger
        credit_system.deduct_credits(consumer_id, cost)
        credit_system.add_credits(node["owner_id"], cost)

        node["status"] = "busy"
        return {
            "status": "allocated",
            "node_id": node["node_id"],
            "provider_id": node["owner_id"],
            "sandboxed": True,
            "cost": cost,
        }

    def release_node(self, node_id: str):
        """Release a node back to idle status."""
        if node_id in self._active_nodes:
            self._active_nodes[node_id]["status"] = "idle"


resource_broker = P2PResourceBroker()
