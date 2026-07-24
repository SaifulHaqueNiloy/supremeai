"""P2P Resource Broker for SupremeAI 2.0.

বাংলা: P2P কম্পিউট রিসোর্স শেয়ারিং, নোড ম্যাচমেকিং এবং ডিস্ট্রিবিউটেড প্রসেসিং ইন্টিগ্রেশন।
"""

import logging
import time
from typing import Any, Dict, List, Optional

from backend.p2p.credit_system import credit_system

logger = logging.getLogger("supremeai.p2p.resource_broker")


class P2PResourceBroker:
    """Brokers compute requests between resource providers and consumers."""

    def __init__(self):
        self._active_nodes: Dict[str, Dict[str, Any]] = {}

    def register_node(
        self,
        node_id: str,
        owner_id: str,
        capabilities: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Register a peer node capable of providing compute resources.

        বাংলা: নতুন P2P কম্পিউট প্রোভাইডার নোড রেজিস্টার করে।
        """
        node_info = {
            "node_id": node_id,
            "owner_id": owner_id,
            "capabilities": capabilities,
            "registered_at": time.time(),
            "last_heartbeat": time.time(),
            "status": "idle",
        }
        self._active_nodes[node_id] = node_info
        logger.info(f"P2P Node registered: {node_id} (owner: {owner_id})")
        return node_info

    def find_best_node(self, required_capability: str, min_credits: float = 1.0) -> Optional[Dict[str, Any]]:
        """Find an idle node matching the capability requirements.

        বাংলা: চাওয়া কম্পিউট ক্ষমতার উপর ভিত্তি করে সেরা উপযুক্ত নোড খুঁজে বের করে।
        """
        now = time.time()
        for node_id, node in self._active_nodes.items():
            # Filter stale heartbeats (> 60s)
            if now - node["last_heartbeat"] > 60:
                continue
            if node["status"] == "idle" and node["capabilities"].get(required_capability, False):
                return node
        return None

    def allocate_task(self, consumer_id: str, required_capability: str, cost: float) -> Dict[str, Any]:
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
            "cost": cost,
        }

    def release_node(self, node_id: str):
        """Release a node back to idle status."""
        if node_id in self._active_nodes:
            self._active_nodes[node_id]["status"] = "idle"


resource_broker = P2PResourceBroker()
