#!/usr/bin/env python3
"""
SupremeAI — Kaggle 6-Node Master Pipeline Orchestrator
======================================================
Coordinates high-throughput offline batch processing, vector embeddings,
synthetic patch distillation, and self-healing test builds using
Kaggle's 180 GPU hours weekly pool.

Usage:
    python scripts/kaggle/pipeline_orchestrator.py --status
    python scripts/kaggle/pipeline_orchestrator.py --check-auth
    python scripts/kaggle/pipeline_orchestrator.py --stage vector_fabric --dry-run
    python scripts/kaggle/pipeline_orchestrator.py --stage brain_distillation
    python scripts/kaggle/pipeline_orchestrator.py --stage weekend_self_healer

বাংলা:
    কাগল ৬-নোড ক্লাস্টার মাস্টার অর্কেস্ট্রেটর স্ক্রিপ্ট।
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from account_pool_rotator import AccountPoolRotator
from kaggle_config import KaggleClusterConfig, load_cluster_config

SCRIPTS_DIR = Path(__file__).resolve().parent
NOTEBOOKS_DIR = SCRIPTS_DIR / "notebooks"
ARTIFACTS_DIR = SCRIPTS_DIR / "artifacts"


class KagglePipelineOrchestrator:
    def __init__(self):
        self.config = load_cluster_config()
        self.rotator = AccountPoolRotator(self.config)

    def print_status(self) -> None:
        status = self.rotator.get_cluster_status()
        print("\n=======================================================")
        print("    [*] SUPREME-KAGGLE 6-NODE CLUSTER STATUS DASHBOARD")
        print("=======================================================")
        print(f"Total Nodes Registered  : {status['total_accounts']} / 6")
        print(f"Weekly GPU Pool Quota   : {status['total_available_hours']:.1f} Hours")
        print(f"Used This Week          : {status['total_used_hours']:.1f} Hours")
        print(f"Remaining Available     : {status['remaining_hours']:.1f} Hours")
        print(f"Active Selected Node    : {status['active_node'] or 'None'}")
        print("-------------------------------------------------------")
        if not status["nodes"]:
            print("  [!] No Kaggle accounts detected in environment.")
            print("      Add KAGGLE_USER_1 & KAGGLE_KEY_1 ... KAGGLE_USER_6 to .env")
        else:
            for node_id, data in status["nodes"].items():
                health = "[OK]" if data["is_healthy"] else "[FAILED]"
                print(f"  [{node_id}] User: {data['username']:<16} | Used: {data['used_hours']:>4.1f}h / {data['max_hours']}h | {health}")
        print("=======================================================\n")

    def check_all_auth(self) -> None:
        print("\n[Auth Check] Testing API connectivity for all registered nodes...")
        if not self.config.accounts:
            print("  [!] No accounts configured. Set KAGGLE_USER_1/KAGGLE_KEY_1 in .env")
            return

        for acc in self.config.accounts:
            print(f"  - Testing {acc.account_id} ({acc.username})...", end=" ", flush=True)
            valid = self.rotator.test_account_auth(acc)
            if valid:
                print("[OK]")
                self.rotator.state["nodes"][acc.account_id]["is_healthy"] = True
            else:
                print("[FAILED] (Invalid credentials or network issue)")
                self.rotator.state["nodes"][acc.account_id]["is_healthy"] = False
        self.rotator._save_state()
        print("[Auth Check] Completed.\n")

    def prepare_kernel_metadata(self, stage: str, account_username: str) -> Path:
        """
        Creates a kernel-metadata.json required by Kaggle CLI.
        """
        stage_titles = {
            "vector_fabric": "supremeai-vector-fabric-engine",
            "brain_distillation": "supremeai-brain-distillation-forge",
            "weekend_self_healer": "supremeai-weekend-self-healer"
        }
        slug = stage_titles.get(stage, f"supremeai-{stage}")
        notebook_file = NOTEBOOKS_DIR / f"{stage}.ipynb"

        meta_dir = ARTIFACTS_DIR / stage
        meta_dir.mkdir(parents=True, exist_ok=True)
        meta_path = meta_dir / "kernel-metadata.json"

        meta_content = {
            "id": f"{account_username}/{slug}",
            "title": slug.replace("-", " ").title(),
            "code_file": str(notebook_file.resolve()),
            "language": "python",
            "kernel_type": "notebook",
            "is_private": "true",
            "enable_gpu": "true",
            "enable_tpu": "false",
            "enable_internet": "true",
            "dataset_sources": [],
            "competition_sources": [],
            "kernel_sources": []
        }

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_content, f, indent=2)

        return meta_path

    def run_stage(self, stage: str, dry_run: bool = False) -> bool:
        print(f"\n[Orchestrator] Initiating Stage: '{stage}'")
        
        # 1. Acquire next available healthy node
        node = self.rotator.get_next_available_node()
        if not node:
            print("[Orchestrator] Error: No healthy Kaggle node with available quota found.")
            return False

        print(f"[Orchestrator] Assigned Node: {node.account_id} (User: {node.username})")
        self.rotator.activate_account(node.account_id)

        # 2. Check notebook existence
        notebook_path = NOTEBOOKS_DIR / f"{stage}.ipynb"
        if not notebook_path.exists():
            print(f"[Orchestrator] Generating template notebook for stage: {stage}...")
            self._generate_template_notebook(stage, notebook_path)

        # 3. Generate Metadata
        meta_path = self.prepare_kernel_metadata(stage, node.username)
        print(f"[Orchestrator] Metadata prepared at: {meta_path}")

        if dry_run:
            print("[Orchestrator] DRY RUN: Validation successful. Skipping actual push to Kaggle.")
            return True

        # 4. Push Kernel via Kaggle API / CLI
        try:
            print(f"[Orchestrator] Pushing kernel '{stage}' to Kaggle Cloud...")
            cmd = ["kaggle", "kernels", "push", "-p", str(meta_path.parent)]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"[Orchestrator] Output: {res.stdout.strip()}")
            print(f"[+] Stage '{stage}' successfully launched on Kaggle GPU!")
            return True
        except FileNotFoundError:
            print("[Orchestrator] Error: 'kaggle' CLI not installed in current environment.")
            print("  Install with: pip install kaggle")
            return False
        except subprocess.CalledProcessError as e:
            print(f"[Orchestrator] Error pushing kernel: {e.stderr.strip()}")
            return False

    def _generate_template_notebook(self, stage: str, path: Path) -> None:
        """
        Creates template Jupyter Notebook for the given stage.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"# SupremeAI — {stage.replace('_', ' ').title()}\n",
                        "Automated GPU-accelerated batch pipeline."
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# ── Environment Setup ──\n",
                        "!nvidia-smi\n",
                        "!pip install -q supabase sentence-transformers torch\n",
                        "print('✅ GPU Environment Ready!')"
                    ]
                }
            ],
            "metadata": {
                "language_info": {"name": "python"}
            },
            "nbformat": 4,
            "nbformat_minor": 2
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(notebook_content, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="SupremeAI Kaggle 6-Node Pipeline Orchestrator")
    parser.add_argument("--status", action="store_true", help="Display cluster pool status")
    parser.add_argument("--check-auth", action="store_true", help="Verify credentials of all registered accounts")
    parser.add_argument("--stage", choices=["vector_fabric", "brain_distillation", "weekend_self_healer"], help="Execute specific pipeline stage")
    parser.add_argument("--dry-run", action="store_true", help="Validate workflow without pushing to Kaggle")

    args = parser.parse_args()
    orchestrator = KagglePipelineOrchestrator()

    if args.status or len(sys.argv) == 1:
        orchestrator.print_status()
    elif args.check_auth:
        orchestrator.check_all_auth()
    elif args.stage:
        orchestrator.run_stage(args.stage, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
