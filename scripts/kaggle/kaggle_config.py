#!/usr/bin/env python3
"""
SupremeAI — Kaggle 6-Node Cluster Configuration Module
======================================================
Manages environment variables, Kaggle API credential schemas, quotas,
GPU hardware targets (Nvidia T4 x2 / TPU v3-8), and external storage sinks.

বাংলা:
    সুপ্রিমএআই কাগল ৬-নোড ক্লাস্টার কনফিগারেশন মডিউল।
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load local environment if available
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")


@dataclass
class KaggleAccountConfig:
    account_id: str
    username: Optional[str] = None
    key: Optional[str] = None
    api_token: Optional[str] = None
    max_weekly_hours: float = 30.0
    used_weekly_hours: float = 0.0
    is_active: bool = True


@dataclass
class KaggleClusterConfig:
    # 6-Node pool configuration
    accounts: List[KaggleAccountConfig] = field(default_factory=list)
    
    # Defaults
    default_accelerator: str = "nvidiaTeslaT4"  # 'nvidiaTeslaT4' (Dual T4) or 'tpuV38'
    enable_gpu: bool = True
    enable_internet: bool = True
    max_session_hours: float = 12.0
    
    # Destination endpoints
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_service_key: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    cloudflare_kv_namespace_id: Optional[str] = os.getenv("CLOUDFLARE_KV_NAMESPACE_ID")
    cloudflare_api_token: Optional[str] = os.getenv("CLOUDFLARE_API_TOKEN")
    cloudflare_account_id: Optional[str] = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    
    # Working directories
    notebooks_dir: Path = Path(__file__).resolve().parent / "notebooks"
    artifacts_dir: Path = Path(__file__).resolve().parent / "artifacts"


def load_cluster_config() -> KaggleClusterConfig:
    """
    Load Kaggle account credentials from environment variables.
    Supports:
    - Modern Bearer Tokens: KAGGLE_API_TOKEN, KAGGLE_API_TOKEN_1 .. 6
    - Legacy Username/Key: KAGGLE_USERNAME, KAGGLE_USER_1/KAGGLE_KEY_1 .. 6
    """
    config = KaggleClusterConfig()
    
    # Check multi-account variables (1 to 6)
    found_accounts = 0
    for i in range(1, 7):
        api_token = os.getenv(f"KAGGLE_API_TOKEN_{i}")
        username = os.getenv(f"KAGGLE_USER_{i}") or os.getenv(f"KAGGLE_USERNAME_{i}")
        key = os.getenv(f"KAGGLE_KEY_{i}")
        
        if api_token:
            config.accounts.append(
                KaggleAccountConfig(
                    account_id=f"node_{i}",
                    api_token=api_token.strip(),
                    username=username.strip() if username else f"user_{i}"
                )
            )
            found_accounts += 1
        elif username and key:
            config.accounts.append(
                KaggleAccountConfig(
                    account_id=f"node_{i}",
                    username=username.strip(),
                    key=key.strip()
                )
            )
            found_accounts += 1

    # Fallback to single account if no numbered accounts found
    if found_accounts == 0:
        single_token = os.getenv("KAGGLE_API_TOKEN")
        default_user = os.getenv("KAGGLE_USERNAME")
        default_key = os.getenv("KAGGLE_KEY")
        if single_token:
            config.accounts.append(
                KaggleAccountConfig(
                    account_id="node_1",
                    api_token=single_token.strip(),
                    username=default_user.strip() if default_user else "user_1"
                )
            )
        elif default_user and default_key:
            config.accounts.append(
                KaggleAccountConfig(
                    account_id="node_1",
                    username=default_user.strip(),
                    key=default_key.strip()
                )
            )
            
    # Ensure directories exist
    config.notebooks_dir.mkdir(parents=True, exist_ok=True)
    config.artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    return config


if __name__ == "__main__":
    cfg = load_cluster_config()
    print(f"[Kaggle Config] Loaded {len(cfg.accounts)} account(s) into cluster pool.")
    for acc in cfg.accounts:
        print(f"  - Account: {acc.account_id} | User: {acc.username} | Max Weekly: {acc.max_weekly_hours}h")
