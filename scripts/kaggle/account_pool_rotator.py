#!/usr/bin/env python3
"""
SupremeAI — Kaggle Account Pool Rotator & Load Balancer
======================================================
Manages active credentials, tracks weekly quota usage across the 6 nodes,
and performs seamless failover and handoff between Kaggle accounts.

বাংলা:
    কাগল মাল্টি-অ্যাকাউন্ট লোড ব্যালেন্সার এবং কোটা রোটেটর।
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests
from kaggle_config import KaggleAccountConfig, KaggleClusterConfig, load_cluster_config

STATE_FILE = Path(__file__).resolve().parent / "artifacts" / "cluster_state.json"


class AccountPoolRotator:
    def __init__(self, config: Optional[KaggleClusterConfig] = None):
        self.config = config or load_cluster_config()
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Check if weekly reset is needed (every Sunday 00:00 UTC)
                    last_reset = data.get("last_reset_utc")
                    if last_reset:
                        dt = datetime.fromisoformat(last_reset)
                        if datetime.utcnow() - dt > timedelta(days=7):
                            return self._create_initial_state()
                    
                    # Sync any newly added accounts into state
                    modified = False
                    for acc in self.config.accounts:
                        if acc.account_id not in data.get("nodes", {}):
                            data.setdefault("nodes", {})[acc.account_id] = {
                                "username": acc.username or acc.account_id,
                                "used_hours": 0.0,
                                "max_hours": acc.max_weekly_hours,
                                "is_healthy": True,
                                "last_used_utc": None
                            }
                            modified = True
                    if modified:
                        self._save_state(data)
                    return data
            except Exception as e:
                print(f"[Rotator] Warning: could not parse state file ({e}), resetting.")
        return self._create_initial_state()

    def _create_initial_state(self) -> Dict:
        state = {
            "last_reset_utc": datetime.utcnow().isoformat(),
            "nodes": {},
            "active_node_id": None
        }
        for acc in self.config.accounts:
            state["nodes"][acc.account_id] = {
                "username": acc.username,
                "used_hours": 0.0,
                "max_hours": acc.max_weekly_hours,
                "is_healthy": True,
                "last_used_utc": None
            }
        self._save_state(state)
        return state

    def _save_state(self, state: Optional[Dict] = None) -> None:
        state = state or self.state
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def test_account_auth(self, account: KaggleAccountConfig) -> bool:
        """
        Verify that the given Kaggle account API credentials are valid.
        Supports both modern Bearer API Tokens and legacy Basic Auth (username/key).
        """
        url = "https://www.kaggle.com/api/v1/datasets/list"
        try:
            if account.api_token:
                headers = {"Authorization": f"Bearer {account.api_token}"}
                res = requests.get(url, headers=headers, timeout=10)
            else:
                res = requests.get(url, auth=(account.username, account.key), timeout=10)
            return res.status_code == 200
        except Exception:
            return False

    def activate_account(self, account_id: str) -> bool:
        """
        Sets process environment variables to use the specified account credentials.
        """
        target_acc = next((a for a in self.config.accounts if a.account_id == account_id), None)
        if not target_acc:
            print(f"[Rotator] Error: Account {account_id} not found.")
            return False

        home_kaggle = Path.home() / ".kaggle"
        home_kaggle.mkdir(parents=True, exist_ok=True)

        if target_acc.api_token:
            os.environ["KAGGLE_API_TOKEN"] = target_acc.api_token
            token_file = home_kaggle / "access_token"
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(target_acc.api_token.strip())
        elif target_acc.username and target_acc.key:
            os.environ["KAGGLE_USERNAME"] = target_acc.username
            os.environ["KAGGLE_KEY"] = target_acc.key
            kaggle_json = home_kaggle / "kaggle.json"
            with open(kaggle_json, "w", encoding="utf-8") as f:
                json.dump({"username": target_acc.username, "key": target_acc.key}, f)
        
        self.state["active_node_id"] = account_id
        self._save_state()
        display_name = target_acc.username or target_acc.account_id
        print(f"[Rotator] Successfully activated node: {account_id} ({display_name})")
        return True

    def get_next_available_node(self) -> Optional[KaggleAccountConfig]:
        """
        Selects the next healthy account with remaining weekly GPU quota.
        """
        for acc in self.config.accounts:
            node_state = self.state["nodes"].get(acc.account_id, {})
            used = node_state.get("used_hours", 0.0)
            max_h = node_state.get("max_hours", 30.0)
            is_healthy = node_state.get("is_healthy", True)
            
            if is_healthy and (used < max_h):
                return acc
        return None

    def record_usage(self, account_id: str, hours: float) -> None:
        if account_id in self.state["nodes"]:
            self.state["nodes"][account_id]["used_hours"] += round(hours, 2)
            self.state["nodes"][account_id]["last_used_utc"] = datetime.utcnow().isoformat()
            self._save_state()

    def get_cluster_status(self) -> Dict:
        total_used = sum(n.get("used_hours", 0.0) for n in self.state["nodes"].values())
        total_max = sum(n.get("max_hours", 30.0) for n in self.state["nodes"].values())
        return {
            "total_accounts": len(self.config.accounts),
            "total_available_hours": total_max,
            "total_used_hours": total_used,
            "remaining_hours": total_max - total_used,
            "active_node": self.state.get("active_node_id"),
            "nodes": self.state["nodes"]
        }


if __name__ == "__main__":
    rotator = AccountPoolRotator()
    status = rotator.get_cluster_status()
    print("=== SupremeAI Kaggle 6-Node Cluster Status ===")
    print(f"Total Accounts: {status['total_accounts']}")
    print(f"Weekly GPU Pool: {status['total_used_hours']:.1f}h / {status['total_available_hours']:.1f}h")
    print(f"Remaining: {status['remaining_hours']:.1f}h")
    print(f"Active Node: {status['active_node']}")
    print("---------------------------------------------")
    for node_id, data in status["nodes"].items():
        print(f"  [{node_id}] User: {data['username']} | Used: {data['used_hours']}h/{data['max_hours']}h | Healthy: {data['is_healthy']}")
