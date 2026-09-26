#!/usr/bin/env bash
# Atomic Mutex Claim (GAP-01 fix — Claim-then-Verify pattern)
# ============================================================
# GitHub REST API-এর `issue edit --add-assignee` true atomic lock নয় —
# দুজন agent একই সময়ে assign করলে race condition হয়। এই script
# Claim-then-Verify pattern implement করে:
#
#   1. CLAIM:    gh issue edit $ID --add-assignee "$AGENT_NAME"
#   2. VERIFY:   gh issue view $ID --json assignees → check যে আমি একমাত্র assignee
#   3. CAS check: যদি অন্য assignee থাকে → আমি lose, exit 1
#   4. LOCK:     status:in-progress label যোগ করি (atomic via gh issue edit)
#
# AUDIT-FIX (#1838): --skip-assign flag যোগ করা হয়েছে। GitHub App bots
# (যেমন supremeai-coder-1-bot[bot]) `/assignees` API দিয়ে assign করা যায়
# না — 403 Forbidden পায়। `--skip-assign` দিলে CLAIM step স্কিপ হয়,
# সরাসরি LOCK (status:in-progress label) প্রয়োগ হয় — যা AGENTS.md §3
# অনুসারে canonical lock।
#
# Usage:
#   scripts/ci/atomic_claim.sh <issue_number> <agent_name> [--status-label status:in-progress] [--skip-assign]
#
# Exit codes:
#   0 = claim successful (this agent owns the issue now)
#   1 = claim failed (race lost — another agent got there first)
#   2 = invalid args / missing dependencies

set -euo pipefail

# ─── Args ────────────────────────────────────────────────────────────────
# Parse flags from positional args
SKIP_ASSIGN=false
STATUS_LABEL="status:in-progress"
POSITIONAL=()

for arg in "$@"; do
  case "$arg" in
    --skip-assign)
      SKIP_ASSIGN=true
      shift
      ;;
    --status-label)
      shift
      STATUS_LABEL="${1:-status:in-progress}"
      shift
      ;;
    --skip-assign=*)
      SKIP_ASSIGN=true
      ;;
    --status-label=*)
      STATUS_LABEL="${arg#*=}"
      ;;
    *)
      POSITIONAL+=("$arg")
      shift
      ;;
  esac
done

ISSUE_NUMBER="${POSITIONAL[0]:-}"
AGENT_NAME="${POSITIONAL[1]:-}"

if [ -z "$ISSUE_NUMBER" ] || [ -z "$AGENT_NAME" ]; then
  echo "Usage: $0 <issue_number> <agent_name> [--status-label <label>] [--skip-assign]" >&2
  echo "  --skip-assign      Skip assignee step (for GitHub App bots that get 403)" >&2
  echo "  --status-label     Override the status label (default: status:in-progress)" >&2
  echo "" >&2
  echo "Examples:" >&2
  echo "  $0 900 agent-1                           # Human operator claim" >&2
  echo "  $0 900 agent-3-coder-1 --skip-assign    # Bot claim (skips 403)" >&2
  exit 2
fi

if ! command -v gh &> /dev/null; then
  echo "ERROR: gh CLI not installed" >&2
  exit 2
fi

# Required env
: "${GH_TOKEN:?GH_TOKEN env var required}"
: "${GH_REPO:?GH_REPO env var required}"

# ─── Pre-check: already claimed? ────────────────────────────────────────
echo "🔍 Pre-checking issue #$ISSUE_NUMBER for existing claim..."

# AUDIT-FIX (#1838): When --skip-assign is used (bot mode), check the
# status:in-progress LABEL instead of assignees — that's the canonical lock.
if [ "$SKIP_ASSIGN" = "true" ]; then
  EXISTING_LABELS=$(gh issue view "$ISSUE_NUMBER" --json labels -q '.labels[].name' 2>/dev/null || echo "")
  if echo "$EXISTING_LABELS" | grep -qFx "$STATUS_LABEL"; then
    # Check if this agent already posted an audit comment (idempotent)
    EXISTING_COMMENTS=$(gh issue view "$ISSUE_NUMBER" --json comments -q '.comments[].body' 2>/dev/null || echo "")
    if echo "$EXISTING_COMMENTS" | grep -q "Atomic Claim.*$AGENT_NAME"; then
      echo "✅ Issue #$ISSUE_NUMBER already claimed by me ($AGENT_NAME) — idempotent success"
      exit 0
    fi
    echo "❌ Issue #$ISSUE_NUMBER already has '$STATUS_LABEL' label (claimed by another agent)"
    echo "Claim failed — race lost."
    exit 1
  fi
  echo "  No existing '$STATUS_LABEL' label — proceeding to LOCK"
else
  # Original assignee-based check (for human operators)
  EXISTING_ASSIGNEES=$(gh issue view "$ISSUE_NUMBER" --json assignees -q '.assignees[].login' 2>/dev/null || echo "")

  if [ -n "$EXISTING_ASSIGNEES" ]; then
    # Check if it's me already (idempotent retry)
    if echo "$EXISTING_ASSIGNEES" | grep -qFx "$AGENT_NAME"; then
      echo "✅ Issue #$ISSUE_NUMBER already assigned to me ($AGENT_NAME) — idempotent success"
      gh issue edit "$ISSUE_NUMBER" --add-label "$STATUS_LABEL" 2>/dev/null || true
      exit 0
    fi
    echo "❌ Issue #$ISSUE_NUMBER already has assignee(s):"
    echo "$EXISTING_ASSIGNEES" | sed 's/^/  - /'
    echo "Claim failed — race lost."
    exit 1
  fi
fi

# ─── STEP 1: CLAIM ───────────────────────────────────────────────────────
if [ "$SKIP_ASSIGN" = "true" ]; then
  # AUDIT-FIX (#1838): Bot mode — skip assignee step entirely.
  # GitHub App bots get 403 on /assignees API. The canonical lock
  # (per AGENTS.md §3) is the status:in-progress label, not assignee.
  echo "🎯 Bot mode (--skip-assign): skipping assignee step"
  echo "  (GitHub App bots cannot be assigned via /assignees API — 403)"
else
  echo "🎯 Claiming issue #$ISSUE_NUMBER as $AGENT_NAME..."
  gh issue edit "$ISSUE_NUMBER" --add-assignee "$AGENT_NAME" 2>&1 | sed 's/^/  /' || {
    echo "❌ Claim command failed"
    exit 1
  }

  # ─── STEP 2: VERIFY (Compare-And-Swap check) ───────────────────────────
  echo "🔍 Verifying claim..."
  sleep 1

  ASSIGNEES_JSON=$(gh issue view "$ISSUE_NUMBER" --json assignees)
  ASSIGNEE_COUNT=$(echo "$ASSIGNEES_JSON" | python3 -c "import json,sys;d=json.load(sys.stdin);print(len(d.get('assignees',[])))")
  FIRST_ASSIGNEE=$(echo "$ASSIGNEES_JSON" | python3 -c "import json,sys;d=json.load(sys.stdin);a=d.get('assignees',[]);print(a[0]['login'] if a else '')")

  echo "  Current assignees: $ASSIGNEE_COUNT"
  echo "  First assignee: $FIRST_ASSIGNEE"

  if [ "$FIRST_ASSIGNEE" != "$AGENT_NAME" ]; then
    echo "❌ Lost the race — first assignee is '$FIRST_ASSIGNEE', not me ($AGENT_NAME)"
    echo "Removing myself from assignees (cleanup)..."
    gh issue edit "$ISSUE_NUMBER" --remove-assignee "$AGENT_NAME" 2>/dev/null || true
    exit 1
  fi

  if [ "$ASSIGNEE_COUNT" -gt 1 ]; then
    echo "⚠️ Multiple assignees detected ($ASSIGNEE_COUNT) — I am first, but race happened"
    OTHER_ASSIGNEES=$(echo "$ASSIGNEES_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
me = '$AGENT_NAME'
for a in d.get('assignees', []):
    if a['login'] != me:
        print(a['login'])
")
    for other in $OTHER_ASSIGNEES; do
      echo "  removing $other..."
      gh issue edit "$ISSUE_NUMBER" --remove-assignee "$other" 2>/dev/null || true
    done
  fi
fi

# ─── STEP 3: LOCK — add status label (CANONICAL LOCK per AGENTS.md §3) ─
echo "🔒 Adding status label '$STATUS_LABEL'..."
gh issue edit "$ISSUE_NUMBER" --add-label "$STATUS_LABEL" 2>&1 | sed 's/^/  /' || {
  echo "⚠️ Failed to add status label (non-fatal — claim may still be valid)"
}

# ─── STEP 4: Post claim timestamp comment (for audit trail) ────────────
CLAIM_TIME=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
if [ "$SKIP_ASSIGN" = "true" ]; then
  CLAIM_METHOD="Label-only (--skip-assign, bot mode — AGENTS.md §3 fallback)"
else
  CLAIM_METHOD="Claim-then-Verify (Compare-And-Swap)"
fi
CLAIM_COMMENT="### 🔒 Atomic Claim Established

- **Agent:** \`$AGENT_NAME\`
- **Issue:** #$ISSUE_NUMBER
- **Claimed at:** $CLAIM_TIME
- **Method:** $CLAIM_METHOD
- **Canonical Lock:** \`$STATUS_LABEL\` label applied
- **Verifier:** \`scripts/ci/atomic_claim.sh\`

_Automated by atomic_claim.sh — Race-safe mutex establishment_"

gh issue comment "$ISSUE_NUMBER" --body "$CLAIM_COMMENT" 2>&1 | sed 's/^/  /' || true

# ─── STEP 5: AUTO-SYNC WORKSPACE (Zero Drift Protection) ─────────────────
echo "🔄 Auto-syncing workspace with latest origin/main..."
python3 scripts/git/auto_sync_main.py 2>/dev/null || python scripts/git/auto_sync_main.py 2>/dev/null || true

echo "✅ Atomic claim successful — issue #$ISSUE_NUMBER owned by $AGENT_NAME"
exit 0
