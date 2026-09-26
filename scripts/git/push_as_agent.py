"""scripts/git/push_as_agent.py — Push current branch as a GitHub App bot.

Flow:
  1. vault.env → Infisical universal-auth → access token
  2. Fetch AGENT_<PREFIX>_* secrets from prod env
  3. agent_bot_registry.get_agent_github_token(slot) → mint installation token
  4. git push https://x-access-token:TOKEN@github.com/owner/repo HEAD:refs/heads/<branch>

SECURITY:
  - vault.env is gitignored (chmod 600). Never commit.
  - Token never written to disk; stdout/stderr masked before logging.
"""
from __future__ import annotations
import os, sys, time, jwt, requests, subprocess
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR / "agents"))
VAULT_ENV_PATH = SCRIPTS_DIR.parent / "vault.env"
INFISICAL_API_BASE = "https://app.infisical.com"


def log(stage, msg): print(f"[{stage}] {msg}", file=sys.stderr, flush=True)


def load_vault(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"vault.env not found: {path}")
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, _, v = line.partition("=")
        v = v.strip().strip('"').strip("'")
        env[k.strip()] = v
    return env


def fetch_creds(vault: dict[str, str], slot: str) -> dict[str, str]:
    from agent_bot_registry import AGENT_SLOT_REGISTRY
    cfg = AGENT_SLOT_REGISTRY.get(slot)
    if not cfg:
        raise ValueError(f"Unknown slot: {slot}. Valid: {sorted(AGENT_SLOT_REGISTRY.keys())}")
    env_prefix = cfg["env_prefix"]
    log("vault", "Authenticating with Infisical universal-auth...")
    r = requests.post(f"{INFISICAL_API_BASE}/api/v1/auth/universal-auth/login",
        data={"clientId": vault["INFISICAL_CLIENT_ID"], "clientSecret": vault["INFISICAL_CLIENT_SECRET"]}, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"Infisical login failed: HTTP {r.status_code}")
    access_token = r.json()["accessToken"]
    log("vault", "✓ access token acquired")
    log("vault", f"Fetching prod secrets (project={vault['INFISICAL_PROJECT_ID'][:8]}...)...")
    r = requests.get(f"{INFISICAL_API_BASE}/api/v3/secrets/raw",
        params={"workspaceId": vault["INFISICAL_PROJECT_ID"], "environment": vault.get("INFISICAL_ENV", "prod"),
                "secretPath": "/", "include_imports": "true"},
        headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Infisical fetch failed: HTTP {r.status_code}")
    secrets = {s["secretKey"]: s.get("secretValue", "") or "" for s in r.json()["secrets"]}
    log("vault", f"✓ fetched {len(secrets)} secrets")
    app_id = secrets.get(f"{env_prefix}_APP_ID") or secrets.get("GITHUB_APP_ID")
    inst_id = secrets.get(f"{env_prefix}_INSTALLATION_ID") or secrets.get("GITHUB_APP_INSTALLATION_ID")
    pem = secrets.get(f"{env_prefix}_PRIVATE_KEY") or secrets.get("GITHUB_APP_PRIVATE_KEY")
    missing = [k for k, v in [("app_id", app_id), ("inst_id", inst_id), ("pem", pem)] if not v]
    if missing:
        raise RuntimeError(f"Missing GitHub App creds for slot {slot} (env_prefix={env_prefix}): {missing}")
    return {"slot": slot, "env_prefix": env_prefix, "bot_name": cfg.get("bot_name", slot),
            "app_id": app_id, "installation_id": inst_id, "private_key": pem}


def mint_token(creds: dict[str, str]) -> str:
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 600, "iss": creds["app_id"]}
    jwt_token = jwt.encode(payload, creds["private_key"], algorithm="RS256")
    log("github", f"Minting installation token for {creds['bot_name']}...")
    r = requests.post(f"https://api.github.com/app/installations/{creds['installation_id']}/access_tokens",
        headers={"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"}, timeout=15)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Token mint failed: HTTP {r.status_code} — {r.text[:200]}")
    token = r.json()["token"]
    log("github", f"✓ installation token minted (len={len(token)})")
    return token


def _mask(text: str, token: str) -> str:
    if not token or not text: return text
    return text.replace(token, "x-access-token:" + "*" * max(0, len(token) - 4) + token[-4:])


def push(token: str, repo_owner: str, repo_name: str, branch: str, dry_run: bool = False) -> tuple[bool, str]:
    url = f"https://x-access-token:{token}@github.com/{repo_owner}/{repo_name}.git"
    cmd = ["git", "push", url, f"HEAD:refs/heads/{branch}"]
    log("git", f"Pushing HEAD → refs/heads/{branch} on {repo_owner}/{repo_name}...")
    if dry_run:
        log("git", f"[DRY-RUN] would push HEAD:refs/heads/{branch}")
        return True, "dry-run ok"
    try:
        result = subprocess.run(cmd, cwd=SCRIPTS_DIR.parent, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return False, "git push timed out after 120s"
    masked_out = _mask(result.stdout, token)
    masked_err = _mask(result.stderr, token)
    if result.returncode == 0:
        log("git", "✓ push succeeded")
        return True, masked_out or "(no output)"
    log("git", f"✗ push failed (exit={result.returncode})")
    return False, masked_err or masked_out or "(no output)"


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Push current branch as a GitHub App bot")
    parser.add_argument("--slot", default=os.environ.get("AGENT_SLOT", "agent-3"))
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo", default=None)
    args = parser.parse_args()

    vault = load_vault(VAULT_ENV_PATH)
    creds = fetch_creds(vault, args.slot)
    token = mint_token(creds)

    if args.repo:
        owner, name = args.repo.split("/", 1)
    else:
        try:
            url = subprocess.check_output(["git", "remote", "get-url", args.remote],
                cwd=SCRIPTS_DIR.parent, text=True, stderr=subprocess.DEVNULL).strip()
        except subprocess.CalledProcessError:
            repo_str = vault.get("GITHUB_REPOSITORY")
            if not repo_str:
                log("git", f"✗ no git remote '{args.remote}' and no GITHUB_REPOSITORY in vault.env")
                return 5
            owner, name = repo_str.split("/", 1)
        else:
            if "github.com/" in url: path = url.split("github.com/", 1)[1]
            elif "github.com:" in url: path = url.split("github.com:", 1)[1]
            else: path = url
            if path.endswith(".git"): path = path[:-4]
            parts = path.split("/")
            owner, name = parts[-2], parts[-1]

    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=SCRIPTS_DIR.parent, text=True).strip()
    log("git", f"Current branch: {branch}, target: {owner}/{name}")

    ok, msg = push(token, owner, name, branch, dry_run=args.dry_run)
    print(msg, file=sys.stderr)
    return 0 if ok else 6


if __name__ == "__main__":
    sys.exit(main())
