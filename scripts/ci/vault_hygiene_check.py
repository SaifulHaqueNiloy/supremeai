#!/usr/bin/env python3
"""Vault Hygiene Check — nightly probe of all Infisical keys used in workflows.

# বাংলা মন্তব্য: এই স্ক্রিপ্ট প্রতি রাতে Infisical vault-এর সব key probe করে।
# কোনো key মৃত (401/403) হলে P1-high issue auto-file করে।
# ROOT-CAUSE FIX (#2895): dead vault keys cause silent fallbacks —
# SELF_HEAL_PAT expired, LaunchDarkly key 401 — কেউ জানত না যে গেট ভুল কাজ করছে।

Usage:
    python scripts/ci/vault_hygiene_check.py [--dry-run]
    python scripts/ci/vault_hygiene_check.py --json report.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from typing import Any

# Key → API probe config (endpoint, expected status, auth header format)
# বাংলা: প্রতিটি key-এর জন্য কোন API কল করে validate করা যায়।
KEY_PROBES = {
    "GITHUB_TOKEN": {
        "url": "https://api.github.com/user",
        "header": "Authorization",
        "format": "token {value}",
        "expect": 200,
    },
    "SELF_HEALING": {
        "url": "https://api.github.com/user",
        "header": "Authorization",
        "format": "token {value}",
        "expect": 200,
    },
    "LAUNCHDARKLY_API_KEY": {
        "url": "https://app.launchdarkly.com/api/v2/flags/default",
        "header": "Authorization",
        "format": "{value}",
        "expect": 200,
    },
    "CLOUDFLARE_API_TOKEN": {
        "url": "https://api.cloudflare.com/client/v4/user/tokens/verify",
        "header": "Authorization",
        "format": "Bearer {value}",
        "expect": 200,
    },
    "RENDER_API_KEY": {
        "url": "https://api.render.com/v1/services",
        "header": "Authorization",
        "format": "Bearer {value}",
        "expect": 200,
    },
    "SUPABASE_ACCESS_TOKEN": {
        "url": "https://api.supabase.com/v1/projects",
        "header": "Authorization",
        "format": "Bearer {value}",
        "expect": 200,
    },
    "STRIPE_API_KEY": {
        "url": "https://api.stripe.com/v1/balance",
        "header": "Authorization",
        "format": "Bearer {value}",
        "expect": 200,
    },
    "TELEGRAM_BOT_TOKEN": {
        "url": "https://api.telegram.org/bot{value}/getMe",
        "header": None,
        "format": None,
        "expect": 200,
    },
    "GROQ_API_KEY": {
        "url": "https://api.groq.com/openai/v1/models",
        "header": "Authorization",
        "format": "Bearer {value}",
        "expect": 200,
    },
    "OPENAI_API_KEY": {
        "url": "https://api.openai.com/v1/models",
        "header": "Authorization",
        "format": "Bearer {value}",
        "expect": 200,
    },
    "GEMINI_API_KEY": {
        "url": "https://generativelanguage.googleapis.com/v1/models?key={value}",
        "header": None,
        "format": None,
        "expect": 200,
    },
}


def probe_key(key_name: str, value: str, config: dict) -> dict:
    """Probe a single vault key against its API endpoint."""
    url = config["url"].replace("{value}", value)
    headers = {}
    if config.get("header"):
        headers[config["header"]] = config["format"].format(value=value)
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.getcode()
            return {"key": key_name, "status": status, "healthy": status == config["expect"]}
    except urllib.error.HTTPError as e:
        return {"key": key_name, "status": e.code, "healthy": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"key": key_name, "status": 0, "healthy": False, "error": str(e)[:200]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Vault hygiene check")
    parser.add_argument("--dry-run", action="store_true", help="Don't file issues")
    parser.add_argument("--json", type=str, help="Write JSON report to file")
    args = parser.parse_args()

    # Fetch secrets from Infisical
    import urllib.parse
    API = "https://app.infisical.com"
    client_id = os.environ.get("INFISICAL_CLIENT_ID", "")
    client_secret = os.environ.get("INFISICAL_CLIENT_SECRET", "")
    project_id = os.environ.get("INFISICAL_PROJECT_ID", "")

    if not client_id or not client_secret:
        print("ERROR: INFISICAL_CLIENT_ID/SECRET not set", file=sys.stderr)
        return 1

    # Auth
    login_body = json.dumps({"clientId": client_id, "clientSecret": client_secret}).encode()
    login_req = urllib.request.Request(
        f"{API}/api/v1/auth/universal-auth/login",
        data=login_body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(login_req, timeout=30) as r:
        access_token = json.load(r)["accessToken"]

    # Fetch secrets
    query = urllib.parse.urlencode({"workspaceId": project_id, "environment": "prod", "secretPath": "/"})
    secrets_req = urllib.request.Request(
        f"{API}/api/v3/secrets/raw?{query}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    with urllib.request.urlopen(secrets_req, timeout=30) as r:
        secrets = {s["secretKey"]: s["secretValue"] for s in json.load(r).get("secrets", [])}

    print(f"Vault has {len(secrets)} secrets. Probing {len(KEY_PROBES)} configured keys...")

    results = []
    dead_keys = []
    for key_name, config in KEY_PROBES.items():
        value = secrets.get(key_name)
        if not value:
            results.append({"key": key_name, "status": "missing", "healthy": False, "error": "not in vault"})
            print(f"  ⚠️  {key_name}: MISSING from vault")
            continue
        result = probe_key(key_name, value, config)
        results.append(result)
        if result["healthy"]:
            print(f"  ✅ {key_name}: healthy ({result['status']})")
        else:
            print(f"  ❌ {key_name}: DEAD ({result.get('error', result.get('status'))})")
            dead_keys.append(result)

    healthy_count = sum(1 for r in results if r["healthy"])
    dead_count = len(dead_keys)
    print(f"\nSummary: {healthy_count} healthy, {dead_count} dead, {len(results) - healthy_count - dead_count} missing")

    # File issues for dead keys (unless --dry-run)
    if dead_keys and not args.dry_run:
        gh_token = os.environ.get("GITHUB_TOKEN", "")
        repo = os.environ.get("GH_REPO", "SaifulHaqueNiloy/supremeai")
        for dead in dead_keys:
            issue_body = {
                "title": f"[vault-hygiene] P1 — vault key '{dead['key']}' is DEAD ({dead.get('error', dead.get('status'))})",
                "body": f"## 🔴 Dead Vault Key Detected\n\n**Key:** `{dead['key']}`\n**Status:** {dead.get('error', dead.get('status'))}\n**Probe URL:** {KEY_PROBES[dead['key']]['url'][:80]}\n\n### Remediation\n1. Rotate/renew the key at the provider\n2. Update the value in Infisical vault\n3. Re-run `python scripts/ci/vault_hygiene_check.py --dry-run` to verify\n\n*Auto-filed by vault_hygiene_check.py (#2895)*",
                "labels": ["P1-high", "area:infrastructure", "type:security"],
            }
            try:
                req = urllib.request.Request(
                    f"https://api.github.com/repos/{repo}/issues",
                    data=json.dumps(issue_body).encode(),
                    headers={"Authorization": f"token {gh_token}", "Accept": "application/vnd.github+json",
                             "X-GitHub-Api-Version": "2022-11-28"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=15) as r:
                    issue = json.load(r)
                    print(f"  Filed issue #{issue['number']} for {dead['key']}")
            except Exception as e:
                print(f"  Could not file issue for {dead['key']}: {e}", file=sys.stderr)

    # Write JSON report
    if args.json:
        with open(args.json, "w") as f:
            json.dump({"results": results, "healthy": healthy_count, "dead": dead_count}, f, indent=2)
        print(f"Report written to {args.json}")

    return 1 if dead_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
