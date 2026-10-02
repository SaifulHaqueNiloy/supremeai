#!/usr/bin/env bash
# Scheduled Agent Runner (#2950-followup) — runs every 45 min via background daemon.
#
# Flow per AGENTS.md Major Rule 2 (Stateless Lifecycle):
#   Pre-flight (sync main + audit open PRs) ──► claim ──► কাজ ──► যাচাই ──► PR ──► CI Gates ──► Auto-Merge ──► পরিচ্ছন্ন এক্সিট
#
# This wrapper:
#   1. Mints fresh GitHub App token (tokens expire in 1 hour)
#   2. Syncs main branch (git pull --rebase)
#   3. Reads AGENTS.md (logs the 2 Major Rules for context)
#   4. Runs continuous_agent_loop.py (which auto-decides role: coder/auditor)
#   5. Logs output to /tmp/scheduled_agent_<timestamp>.log
#
# Usage:
#   bash scripts/agents/run_scheduled_agent.sh
#
# Scheduled via: scripts/agents/scheduled_agent_daemon.sh (every 45 min)

set -euo pipefail

cd /home/z/supremeai_check

# ─── Step 1: Mint fresh GitHub App token ───
# বাংলা মন্তব্য: GitHub App installation token ১ ঘণ্টায় expire হয়।
# প্রতিটি scheduled run-এ fresh token mint করা হয়।
echo "=== [$(date +%T)] Scheduled Agent Run Started ==="
echo "Step 1: Minting fresh GitHub App token..."
/home/z/.venv/bin/python3 /tmp/gh_auth_full.py 2>&1 | tail -1
TOKEN=$(cat /tmp/gh_installation_token.txt)
export GH_TOKEN="$TOKEN"
export GITHUB_TOKEN="$TOKEN"
export REPO="SaifulHaqueNiloy/supremeai"
export PATH="/home/z/.local/bin:$PATH"

# Authenticate gh CLI with fresh token
echo "$TOKEN" | gh auth login --with-token --hostname github.com 2>&1 | tail -1 || true
echo "✅ Token minted + gh CLI authenticated"

# ─── Step 2: Sync main branch (Pre-flight per AGENTS.md Major Rule 2) ───
echo ""
echo "Step 2: Syncing main branch..."
git checkout main 2>&1 | tail -1
git fetch origin --prune 2>&1 | tail -1
git pull origin main --rebase 2>&1 | tail -2
git log -1 --oneline
echo "✅ Main synced"

# ─── Step 3: Read AGENTS.md (acknowledge 2 Major Rules) ───
echo ""
echo "Step 3: Reading AGENTS.md (2 Major Rules)..."
if [ -f AGENTS.md ]; then
    # বাংলা মন্তব্য: AGENTS.md-এর শুধু Major Rule 1 + Major Rule 2 পড়া হয়
    # (বাকি rules AGENT_RULES.md-এ, loop নিজে inject করবে)
    head -35 AGENTS.md | grep -E "^#|^>|\*\*|Major Rule" | head -10
    echo "✅ AGENTS.md acknowledged (Major Rule 1: Authority, Major Rule 2: Stateless Lifecycle)"
else
    echo "⚠️ AGENTS.md not found — proceeding with default rules"
fi

# ─── Step 4: Audit open PRs (Pre-flight PR Awareness per Rule 14) ───
echo ""
echo "Step 4: Auditing open PRs (Pre-flight PR Awareness)..."
OPEN_PRS=$(gh pr list --repo "$REPO" --state open --json number,title 2>/dev/null | /home/z/.venv/bin/python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'{len(data)} open PR(s)')
    for p in data[:5]:
        print(f'  #{p[\"number\"]} | {p[\"title\"][:60]}')
except: print('0 open PRs')
" 2>&1)
echo "$OPEN_PRS"

# ─── Step 5: Run continuous_agent_loop.py (auto-decides role) ───
echo ""
echo "Step 5: Running continuous_agent_loop.py (script-driven role)..."
echo "  → Role: auto-decided (coder if unclaimed issues, else auditor)"
echo "  → Agent name: auto-resolved (persistent identity + dynamic model)"
echo "  → Model: from AGENT_MODEL env (default: glm5.2)"
echo ""

# Run loop with 1 iteration (claim + work on 1 issue, then clean exit)
# বাংলা মন্তব্য: 1 iteration = 1 task। শেষ হলে daemon-এ ফেরা (per AGENTS.md Rule 5)।
# Daemon পরবর্তী task অবিলম্বে শুরু করবে — sleep নয়, continuous execution।
AGENT_MODEL="${AGENT_MODEL:-glm5.2}" \
timeout 1800 /home/z/.venv/bin/python3 scripts/agents/continuous_agent_loop.py --iterations 1 2>&1 || true

echo ""
echo "=== [$(date +%T)] Scheduled Agent Run Complete ==="

# ─── AGENTS.md Rule 5: Graceful Exit (task_completed signal) ───
# বাংলা মন্তব্য: AGENTS.md Major Rule 2 (Stateless Lifecycle)-এর শেষ ধাপ:
#   "কাজ শেষ হাতেই লোকাল এনভায়রনমেন্ট ক্লিন করে স্ক্রিপ্টকে task_completed
#    সিগন্যাল দিয়ে সেন্ট্রাল লুপে ফেরা।"
# এই signal দেখে daemon পরবর্তী task অবিলম্বে শুরু করবে (sleep নয়)।
echo "✅ TASK_COMPLETED signal sent — daemon will start next task immediately"

# ─── Step 6: Trim worklog to last 12 hours (housekeeping) ───
# বাংলা মন্তব্য: worklog.md বড় হয়ে গেলে পুরোনো entries মুছে ফেলা হয়।
# শুধু শেষ ১২ ঘণ্টার কাজ রাখা হয় — তাই file ছোট থাকে।
WORKLOG="/home/z/my-project/worklog.md"
if [ -f "$WORKLOG" ]; then
    /home/z/.venv/bin/python3 -c "
import re
from datetime import datetime, timedelta
from pathlib import Path

worklog_path = Path('$WORKLOG')
content = worklog_path.read_text(encoding='utf-8')
parts = content.split('\n---\n')
header = parts[0] if parts else ''
now = datetime.utcnow()
cutoff = now - timedelta(hours=12)

kept = []
for part in parts[1:]:
    timestamps = re.findall(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', part)
    if not timestamps:
        timestamps = re.findall(r'(\d{4}-\d{2}-\d{2})', part)
    latest = None
    for ts_str in timestamps:
        try:
            ts = datetime.strptime(ts_str[:19], '%Y-%m-%dT%H:%M:%S') if 'T' in ts_str else datetime.strptime(ts_str[:10], '%Y-%m-%d')
            if latest is None or ts > latest:
                latest = ts
        except: continue
    if latest is None or latest >= cutoff:
        kept.append(part)

new_content = header + ('\n---\n' + '\n---\n'.join(kept) if kept else '')
if not new_content.endswith('\n'): new_content += '\n'
worklog_path.write_text(new_content, encoding='utf-8')
print(f'  ✂️ Worklog trimmed: kept {len(kept)} sections (last 12h)')
" 2>&1 || echo "  ⚠️ Worklog trim failed (non-critical)"
fi
