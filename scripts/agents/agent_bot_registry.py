"""SupremeAI Agent Branch <-> GitHub Bot Registry & Token Dispatcher.

Implements AGENTS.md rules:
- 1 Branch = 1 Persistent Agent Workspace
- 1 Branch = 1 Assigned GitHub App Bot
- Independent 5,000 req/hr rate limits per workspace slot
"""

import os
import time
import jwt
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Canonical Mapping: Branch Slot -> GitHub App Bot Identity
#
# AUDIT-FIX (P0): আগে এই registry-তে মাত্র ৬টি slot ছিল (agent-1, 2, 3, 5, 6, 8),
# কিন্তু docs/master_docs/AGENT_SLOT_REGISTRY.yaml (canonical charter) ১১টি slot
# define করে। এছাড়া agent-8-এর রোল দুই file-এ ভিন্ন ছিল — Python বলছিল "Platform
# & External Integrations", YAML বলছিল "PR Verifier" (platform এখন agent-11)।
# এই registry এখন YAML-এর সাথে পুরোপুরি sync করা।
AGENT_SLOT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "agent-1": {
        "bot_name": "supremeai-planner",
        "role": "Planner & Full Codebase Auditor",
        "env_prefix": "GITHUB_APP",
        "description": "Owns comprehensive architectural audits, gap identification, implementation planning, backlog issue creation",
        "primary_branch": "agent-1-planner",
    },
    "agent-2": {
        "bot_name": "supremeai-pr-helper",
        "role": "PR Gate & Diagnostics Verifier",
        "env_prefix": "AGENT_PR_HELPER",
        "description": "Evaluates PR delta, regression risk, performs beneficial squash merges",
        "primary_branch": "agent-2-pr-helper",
    },
    "agent-3": {
        "bot_name": "supremeai-coder-1",
        "role": "Primary Code Implementer",
        "env_prefix": "AGENT_CODER_1",
        "description": "Claims assigned issues, performs local issue-scoped audit, writes production code and unit tests",
        "primary_branch": "agent-3-coder-1",
    },
    "agent-5": {
        "bot_name": "supremeai-ci-action",
        "role": "CI/CD & Workflow Specialist",
        "env_prefix": "AGENT_CI_ACTION",
        "description": "Owns .github/workflows/*, git pre-push hooks, auto-sync engines, artifact regeneration",
        "primary_branch": "agent-5-ci-action",
    },
    "agent-6": {
        "bot_name": "supremeai-coder-2",
        "role": "Parallel Code Implementer",
        "env_prefix": "AGENT_CODER_2",
        "description": "Handles parallel features, independent bug resolution without cross-branch contention",
        "primary_branch": "agent-6-coder-2",
    },
    # AUDIT-FIX: agent-8 এখন YAML অনুসারে PR verifier — আগে ভুলে platform role দেওয়া হয়েছিল।
    "agent-8": {
        "bot_name": "supremeai-pr-verifier",
        "role": "PR Verifier & Code Quality",
        "env_prefix": "AGENT_PR_VERIFIER",
        "description": "PR helper bot decision check + code quality. Fixes wrong merges. Preserves beneficial changes + removes regressions",
        "primary_branch": "agent-8-pr-verifier",
    },
    # AUDIT-FIX: agent-9 — observability standby (active=false per YAML)। token
    # minting path থাকলেও ডিফল্টে কল হবে না, যাতে inactive slot-এর জন্য env না
    # থাকলেও startup-এ crash না করে।
    "agent-9": {
        "bot_name": "supremeai-observer",
        "role": "Observability & Metrics Standby",
        "env_prefix": "AGENT_OBSERVER",
        "description": "Standby — observability + metrics dashboards (activatable on demand)",
        "primary_branch": "agent-9-observer",
        "active": False,
    },
    "agent-10": {
        "bot_name": "supremeai-super-orchestrator",
        "role": "Super Orchestrator & Fallback",
        "env_prefix": "AGENT_SUPER",
        "description": "Orchestrator + fallback. Assigns alternatives if agent inactive. Does any role if needed",
        "primary_branch": "agent-10-super",
    },
    # AUDIT-FIX: agent-11 — এখানে এসেছে platform role (আগে agent-8 এ ভুল ছিল)।
    "agent-11": {
        "bot_name": "supremeai-platform-agent",
        "role": "Platform & External Integrations",
        "env_prefix": "AGENT_PLATFORM",
        "description": "Owns ALL connected 3rd-party platforms end-to-end (Render, Upstash, MCP tower, Infisical, Cloudflare, Supabase, Kaggle, AI providers)",
        "primary_branch": "agent-11-longrun",
    },
    "agent-12": {
        "bot_name": "supremeai-ci-fixer",
        "role": "CI Fixer & Log Watcher",
        "env_prefix": "AGENT_CI_FIXER",
        "description": "Watches CI/Actions logs on failure (handoff:log-fix), diagnoses, fixes, re-verifies. Creates issues on repeated failures",
        "primary_branch": "agent-12-ci-fixer",
    },
    "agent-13": {
        "bot_name": "supremeai-browser-tester",
        "role": "Post-Merge Browser Tester",
        "env_prefix": "AGENT_BROWSER_TESTER",
        "description": "Post-merge browser testing (handoff:browser-test). Split from agent-12 — browser test and CI fix are two different agents' jobs",
        "primary_branch": "agent-13-browser-tester",
    },
}

_TOKEN_CACHE: Dict[str, Dict[str, Any]] = {}


def get_agent_config(slot: str) -> Optional[Dict[str, Any]]:
    """Return configuration details for a given agent slot or descriptive branch name."""
    if slot in AGENT_SLOT_REGISTRY:
        return AGENT_SLOT_REGISTRY[slot]
    for s, cfg in AGENT_SLOT_REGISTRY.items():
        if cfg.get("primary_branch") == slot or slot.startswith(f"{s}-"):
            return cfg
    return None


def get_agent_github_token(slot: str) -> str:
    """Generate or retrieve a cached GitHub Installation Access Token for a specific agent slot.
    
    Tokens are valid for 1 hour and cached until 5 minutes before expiration.
    """
    config = get_agent_config(slot)
    if not config:
        raise ValueError(f"Unknown agent slot: {slot}. Valid slots: {list(AGENT_SLOT_REGISTRY.keys())}")

    now = int(time.time())
    cached = _TOKEN_CACHE.get(slot)
    if cached and cached.get("expires_at", 0) > now + 300:
        return cached["token"]

    prefix = config["env_prefix"]
    app_id = os.getenv(f"{prefix}_APP_ID") or os.getenv("GITHUB_APP_ID")
    inst_id = os.getenv(f"{prefix}_INSTALLATION_ID") or os.getenv("GITHUB_APP_INSTALLATION_ID")
    key_path = os.getenv(f"{prefix}_PRIVATE_KEY_PATH") or os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")

    if not app_id or not inst_id:
        raise RuntimeError(f"Missing {prefix}_APP_ID or {prefix}_INSTALLATION_ID in environment")

    # Read private key from file or env
    private_key = None
    if key_path:
        full_key_path = os.path.join(BASE_DIR, key_path) if not os.path.isabs(key_path) else key_path
        if os.path.exists(full_key_path):
            with open(full_key_path, "r", encoding="utf-8") as f:
                private_key = f.read()

    if not private_key:
        private_key = os.getenv(f"{prefix}_PRIVATE_KEY") or os.getenv("GITHUB_APP_PRIVATE_KEY")

    if not private_key:
        raise RuntimeError(f"Private key for agent {slot} ({config['bot_name']}) could not be located.")

    # 1. Create JWT
    payload = {
        "iat": now - 60,
        "exp": now + 600,
        "iss": str(app_id),
    }
    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")

    # 2. Request installation access token
    headers = {
        "Authorization": f"Bearer {encoded_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    res = requests.post(
        f"https://api.github.com/app/installations/{inst_id}/access_tokens",
        headers=headers,
        timeout=15,
    )
    if res.status_code not in [200, 201]:
        raise RuntimeError(f"Failed to generate GitHub token for {slot}: {res.status_code} - {res.text}")

    data = res.json()
    token = data["token"]
    
    # Expiry is typically 3600 seconds from now
    expires_at = now + 3500
    _TOKEN_CACHE[slot] = {
        "token": token,
        "expires_at": expires_at,
        "bot_name": config["bot_name"],
    }
    return token


if __name__ == "__main__":
    print("=" * 65)
    print(" SupremeAI Branch <-> Bot Mapping & Live Token Verification")
    print("=" * 65)
    
    for slot, cfg in AGENT_SLOT_REGISTRY.items():
        try:
            tok = get_agent_github_token(slot)
            # Test token
            r = requests.get("https://api.github.com/rate_limit", headers={"Authorization": f"Bearer {tok}"})
            core = r.json().get("resources", {}).get("core", {})
            print(f"[{slot}] -> {cfg['bot_name']:<30} | Token: OK | RateLimit: {core.get('remaining')}/{core.get('limit')}")
        except Exception as e:
            print(f"[{slot}] -> {cfg['bot_name']:<30} | Error: {e}")
