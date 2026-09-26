#!/usr/bin/env python3
"""scripts/git/push_as_agent.py — Push the current branch as a GitHub App bot.

চলার ধাপ (flow):
  1. vault.env থেকে Infisical universal-auth credentials পড়ে।
  2. Infisical-এ client_id + client_secret দিয়ে access token নেয়।
  3. Access token দিয়ে prod env থেকে GitHub App credentials fetch করে
     (AGENT_<PREFIX>_APP_ID, _INSTALLATION_ID, _PRIVATE_KEY, _NAME)।
  4. agent_bot_registry.get_agent_github_token(slot) দিয়ে GitHub installation
     access token mint করে (১ ঘণ্টা valid, ৫ মিনিট আগে cache expire)।
  5. সেই token দিয়ে git push https://x-access-token:TOKEN@github.com/owner/repo
     করে — commit author automatically bot-এর identity হবে।

SECURITY:
  - vault.env কখনো commit হয় না (.gitignore-এ আছে)।
  - Token গুলো stdout-এ লেখা হয় না — শুধু length ও last-4-char দেখানো যায়।
  - Push শেষে token cache মেমরিতে থাকে কিন্তু কখনো disk-এ লেখা হয় না।

USAGE:
  python3 scripts/git/push_as_agent.py                 # default slot agent-3
  python3 scripts/git/push_as_agent.py --slot agent-5 # CI/CD slot
  python3 scripts/git/push_as_agent.py --dry-run       # mint token, don't push
  python3 scripts/git/push_as_agent.py --remote origin # override remote name
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

# Make scripts/ importable so we can use agent_bot_registry
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))
# agent_bot_registry.py বসে scripts/agents/ এ — সেটাও path-এ যোগ করি।
sys.path.insert(0, str(SCRIPTS_DIR / "agents"))

# Constants
VAULT_ENV_PATH = SCRIPTS_DIR.parent / "vault.env"
INFISICAL_API_BASE = "https://app.infisical.com"
INFISICAL_TOKEN_TTL_FALLBACK = 3600  # 1 hour (server default)


def log(stage: str, msg: str) -> None:
    print(f"[{stage}] {msg}", file=sys.stderr, flush=True)


def load_vault_env(path: Path) -> dict[str, str]:
    """vault.env ফাইল থেকে KEY=VALUE পড়ে dict ফেরত দেয়।"""
    if not path.exists():
        raise FileNotFoundError(
            f"vault.env পাওয়া যায়নি: {path}\n"
            "এই ফাইলে Infisical universal-auth credentials রাখুন "
            "(INFISICAL_CLIENT_ID, INFISICAL_CLIENT_SECRET, ইত্যাদি)।"
        )

    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        # Strip surrounding quotes
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            val = val[1:-1]
        env[key] = val
    return env


def infisical_login(client_id: str, client_secret: str) -> str:
    """Infisical universal-auth দিয়ে access token ফেরত দেয়।"""
    resp = requests.post(
        f"{INFISICAL_API_BASE}/api/v1/auth/universal-auth/login",
        data={"clientId": client_id, "clientSecret": client_secret},
        timeout=20,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Infisical universal-auth failed: HTTP {resp.status_code} "
            f"— {resp.text[:300]}"
        )
    token = resp.json().get("accessToken")
    if not token:
        raise RuntimeError("Infisical returned no accessToken")
    return token


def infisical_list_secrets(
    access_token: str, project_id: str, environment: str, secret_path: str = "/"
) -> list[dict[str, Any]]:
    """Infisical prod env থেকে সব secrets fetch করে (include_imports=true সহ)।"""
    resp = requests.get(
        f"{INFISICAL_API_BASE}/api/v3/secrets/raw",
        params={
            "workspaceId": project_id,
            "environment": environment,
            "secretPath": secret_path,
            "include_imports": "true",
        },
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Infisical list secrets failed: HTTP {resp.status_code} — {resp.text[:300]}"
        )
    return resp.json().get("secrets", []) or []


def fetch_agent_credentials(
    vault: dict[str, str], slot: str
) -> dict[str, str]:
    """Infisical থেকে নির্দিষ্ট agent slot-এর GitHub App credentials আনে।

    slot → env_prefix mapping আমরা agent_bot_registry.py থেকে reuse করছি।
    """
    from agent_bot_registry import AGENT_SLOT_REGISTRY  # noqa: PLC0415

    slot_cfg = AGENT_SLOT_REGISTRY.get(slot)
    if not slot_cfg:
        raise ValueError(
            f"Unknown slot: {slot}. Valid: {sorted(AGENT_SLOT_REGISTRY.keys())}"
        )

    env_prefix = slot_cfg["env_prefix"]
    bot_name = slot_cfg.get("bot_name", slot)

    log("vault", f"Authenticating with Infisical universal-auth...")
    access_token = infisical_login(
        client_id=vault["INFISICAL_CLIENT_ID"],
        client_secret=vault["INFISICAL_CLIENT_SECRET"],
    )
    log("vault", "✓ access token acquired")

    log("vault", f"Fetching prod secrets (project={vault['INFISICAL_PROJECT_ID'][:8]}...)...")
    secrets = infisical_list_secrets(
        access_token=access_token,
        project_id=vault["INFISICAL_PROJECT_ID"],
        environment=vault.get("INFISICAL_ENV", "prod"),
    )
    log("vault", f"✓ fetched {len(secrets)} secrets")

    # Build a lookup dict
    secret_map: dict[str, str] = {
        s.get("secretKey", ""): s.get("secretValue", "") or "" for s in secrets
    }

    # Expected keys: AGENT_<PREFIX>_APP_ID, _INSTALLATION_ID, _PRIVATE_KEY
    app_id = secret_map.get(f"{env_prefix}_APP_ID")
    installation_id = secret_map.get(f"{env_prefix}_INSTALLATION_ID")
    private_key = secret_map.get(f"{env_prefix}_PRIVATE_KEY")
    bot_name_from_secret = secret_map.get(f"{env_prefix}_NAME") or bot_name

    missing = []
    if not app_id:
        missing.append(f"{env_prefix}_APP_ID")
    if not installation_id:
        missing.append(f"{env_prefix}_INSTALLATION_ID")
    if not private_key:
        missing.append(f"{env_prefix}_PRIVATE_KEY")

    if missing:
        # Show what's actually in Infisical that matches — diagnostic help
        available = sorted(
            k for k in secret_map if k.startswith(env_prefix) or "GITHUB_APP" in k
        )
        raise RuntimeError(
            f"Missing required Infisical secrets for slot {slot} "
            f"(env_prefix={env_prefix}): {missing}\n"
            f"Available {env_prefix}_* / GITHUB_APP_* keys: {available}"
        )

    return {
        "slot": slot,
        "env_prefix": env_prefix,
        "bot_name": bot_name_from_secret,
        "app_id": app_id,
        "installation_id": installation_id,
        "private_key": private_key,
    }


def mint_github_installation_token(creds: dict[str, str]) -> str:
    """agent_bot_registry.py-এর logic reuse করে GitHub installation token mint করে।

    আমরা env var inject করে তারপর agent_bot_registry.get_agent_github_token(slot)
    call করছি — এতে token caching (৫ মিনিট আগে expire) স্বয়ংক্রিয়ভাবে পাব।
    """
    os.environ[f"{creds['env_prefix']}_APP_ID"] = creds["app_id"]
    os.environ[f"{creds['env_prefix']}_INSTALLATION_ID"] = creds["installation_id"]
    os.environ[f"{creds['env_prefix']}_PRIVATE_KEY"] = creds["private_key"]

    from agent_bot_registry import get_agent_github_token  # noqa: PLC0415

    log("github", f"Minting installation token for {creds['bot_name']}...")
    token = get_agent_github_token(creds["slot"])
    if not token:
        raise RuntimeError("get_agent_github_token returned empty token")
    log("github", f"✓ installation token minted (len={len(token)})")
    return token


def get_current_branch() -> str:
    out = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=SCRIPTS_DIR.parent,
        text=True,
    ).strip()
    return out


def get_remote_url(remote: str) -> str:
    try:
        out = subprocess.check_output(
            ["git", "remote", "get-url", remote],
            cwd=SCRIPTS_DIR.parent,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return out
    except subprocess.CalledProcessError:
        return ""


def parse_repo_owner_name(remote_url: str) -> tuple[str, str]:
    """git remote URL থেকে owner/repo বের করে।

    Supports:
      - https://github.com/owner/repo.git
      - git@github.com:owner/repo.git
      - ssh://git@github.com/owner/repo.git
    """
    if not remote_url:
        raise RuntimeError("No git remote configured")

    # Strip credentials if embedded (https://user:pass@host/...)
    if remote_url.startswith("https://") or remote_url.startswith("http://"):
        parsed = urlparse(remote_url)
        path = parsed.path.lstrip("/")
    elif remote_url.startswith("git@"):
        # git@github.com:owner/repo.git
        _, _, path = remote_url.partition(":")
    elif remote_url.startswith("ssh://"):
        parsed = urlparse(remote_url)
        path = parsed.path.lstrip("/")
    else:
        path = remote_url

    # Strip trailing .git
    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) < 2:
        raise RuntimeError(f"Could not parse owner/repo from remote: {remote_url}")
    return parts[-2], parts[-1]


def push_branch(
    token: str,
    repo_owner: str,
    repo_name: str,
    branch: str,
    dry_run: bool = False,
) -> tuple[bool, str]:
    """HTTPS + x-access-token দিয়ে current branch push করে।

    প্রতিটি push আলাদা subprocess হিসেবে — token কখনো shell history-তে যায় না।
    """
    # এক বারের জন্য remote URL set করি (token-সহ) — push শেষে আবার পরিষ্কার করব।
    # কিন্তু credentials helper use না করে একটাই push command চালাই — সবচেয়ে নিরাপদ।
    url_with_token = f"https://x-access-token:{token}@github.com/{repo_owner}/{repo_name}.git"

    cmd = ["git", "push", url_with_token, f"HEAD:refs/heads/{branch}"]
    log("git", f"Pushing HEAD → refs/heads/{branch} on {repo_owner}/{repo_name}...")

    if dry_run:
        log("git", f"[DRY-RUN] would run: git push <token-redacted> HEAD:refs/heads/{branch}")
        return True, "dry-run ok"

    try:
        result = subprocess.run(
            cmd,
            cwd=SCRIPTS_DIR.parent,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return False, "git push timed out after 120s"

    # Token কখনো stderr/stdout-এ লিখা যাবে না — যদি থাকে সেটা mask করি।
    masked_out = _mask_token(result.stdout, token)
    masked_err = _mask_token(result.stderr, token)

    if result.returncode == 0:
        log("git", "✓ push succeeded")
        return True, masked_out or "(no output)"
    log("git", f"✗ push failed (exit={result.returncode})")
    return False, masked_err or masked_out or "(no output)"


def _mask_token(text: str, token: str) -> str:
    """যদি token stdout/stderr-এ লিক করে সেটা mask করে।"""
    if not token or not text:
        return text
    masked = "x-access-token:" + "*" * max(0, len(token) - 4) + token[-4:]
    return text.replace(token, masked).replace(token[:-4], "*" * max(0, len(token) - 4))


def main() -> int:
    parser = argparse.ArgumentParser(description="Push current branch as a GitHub App bot")
    parser.add_argument(
        "--slot",
        default=os.environ.get("AGENT_SLOT", "agent-3"),
        help="Agent slot (default: agent-3, env: AGENT_SLOT)",
    )
    parser.add_argument("--remote", default="origin", help="git remote name (default: origin)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Authenticate + mint token but do not push",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="Override repo (owner/name). Otherwise inferred from remote.",
    )
    args = parser.parse_args()

    # Step 1: load vault.env
    log("vault", f"Loading credentials from {VAULT_ENV_PATH}...")
    vault = load_vault_env(VAULT_ENV_PATH)

    required_vault_keys = (
        "INFISICAL_CLIENT_ID",
        "INFISICAL_CLIENT_SECRET",
        "INFISICAL_PROJECT_ID",
    )
    missing_vault = [k for k in required_vault_keys if not vault.get(k)]
    if missing_vault:
        log("vault", f"✗ vault.env missing: {missing_vault}")
        return 2
    log("vault", "✓ vault.env loaded")

    # Step 2-3: fetch GitHub App creds from Infisical
    try:
        creds = fetch_agent_credentials(vault, args.slot)
    except Exception as exc:
        log("vault", f"✗ {exc}")
        return 3

    log("vault", f"✓ slot={creds['slot']} bot={creds['bot_name']} app_id={creds['app_id']}")

    # Step 4: mint GitHub installation token
    try:
        token = mint_github_installation_token(creds)
    except Exception as exc:
        log("github", f"✗ token mint failed: {exc}")
        return 4

    # Step 5: determine repo + branch
    if args.repo:
        owner, name = args.repo.split("/", 1)
    else:
        remote_url = get_remote_url(args.remote)
        if not remote_url:
            # Try vault.env's GITHUB_REPOSITORY as fallback
            repo_str = vault.get("GITHUB_REPOSITORY")
            if not repo_str:
                log("git", f"✗ no git remote '{args.remote}' and no GITHUB_REPOSITORY in vault.env")
                return 5
            owner, name = repo_str.split("/", 1)
        else:
            owner, name = parse_repo_owner_name(remote_url)

    branch = get_current_branch()
    log("git", f"Current branch: {branch}, target repo: {owner}/{name}")

    # Step 6: push
    ok, msg = push_branch(
        token=token,
        repo_owner=owner,
        repo_name=name,
        branch=branch,
        dry_run=args.dry_run,
    )
    print(msg, file=sys.stderr)
    return 0 if ok else 6


if __name__ == "__main__":
    sys.exit(main())
