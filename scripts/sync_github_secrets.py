import os
import subprocess
import re
from dotenv import load_dotenv

load_dotenv('.env')

valid_key_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_.-]*$')

env_vars = {}
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if valid_key_pattern.match(k):
            env_vars[k] = v

print(f"Found {len(env_vars)} valid keys in .env. Updating GitHub Secrets...")

env = os.environ.copy()
env.pop('GITHUB_TOKEN', None)  # Ensure gh CLI uses logged-in keyring auth

success = 0
failed = 0

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

for k, v in env_vars.items():
    if not v:
        continue
    p = subprocess.run(
        ['gh', 'secret', 'set', k, '-b', v, '--repo', 'paykaribazaronline/supremeai'],
        capture_output=True,
        text=True,
        env=env
    )
    if p.returncode == 0:
        success += 1
        print(f"[OK] Set GitHub Secret: {k}", flush=True)
    else:
        failed += 1
        print(f"[FAIL] Failed to set {k}: {p.stderr.strip()}", flush=True)

print(f"\nDone! Updated {success} secrets ({failed} failed).", flush=True)
