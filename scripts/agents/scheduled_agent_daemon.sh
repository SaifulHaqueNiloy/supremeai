#!/usr/bin/env bash
# Continuous Agent Daemon — runs run_scheduled_agent.sh back-to-back.
#
# বাংলা পরিচিতি:
# এই daemon background-এ চলে। প্রতিটি task শেষ হওয়ার পর (clean exit per
# AGENTS.md Rule 5) পরবর্তী task অবিলম্বে শুরু হয় — sleep নেই।
#
# AGENTS.md Rule 5 (Graceful Exit) অনুযায়ী:
#   "কাজ শেষ হাতেই লোকাল এনভায়রনমেন্ট ক্লিন করে স্ক্রিপ্টকে task_completed
#    সিগন্যাল দিয়ে সেন্ট্রাল লুপে ফেরা।"
#
# Continuous flow:
#   Task শুরু → কাজ → verify → PR → CI → merge → clean exit
#   → পরবর্তী task অবিলম্বে শুরু (no sleep)
#
# যদি কোনো task না থাকে (fleet idle), তখন short wait (5 min) → retry
# যাতে busy-loop-এ CPU নষ্ট না হয়।
#
# Usage:
#   nohup bash scripts/agents/scheduled_agent_daemon.sh \\
#     > /tmp/scheduled_agent_daemon.log 2>&1 &
#
# Stop:
#   pkill -f scheduled_agent_daemon.sh
#
# Check status:
#   tail -50 /tmp/scheduled_agent_daemon.log

IDLE_WAIT_SECONDS=300  # 5 min wait when no task available (fleet idle)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$SCRIPT_DIR/run_scheduled_agent.sh"

echo "🚀 Continuous Agent Daemon started at $(date +%T)"
echo "   Mode: continuous (no sleep between tasks)"
echo "   Idle wait: ${IDLE_WAIT_SECONDS}s (only when no task available)"
echo "   Runner: $RUNNER"
echo "   PID: $$"
echo ""

# Continuous loop — task শেষ হলে পরবর্তী অবিলম্বে শুরু
while true; do
    echo "=========================================="
    echo "🔄 New task cycle at $(date +%T)"
    echo "=========================================="

    # Run the scheduled agent script (1 full task: claim → work → PR → merge → exit)
    bash "$RUNNER" 2>&1

    # Check if agent loop completed with work or was idle
    # বাংলা মন্তব্য: run_scheduled_agent.sh-এর output দেখে নির্ধারণ করা হয়
    # কোনো task হয়েছে কিনা। "Fleet healthy" বা "No task available" হলে idle।
    LAST_LOG=$(tail -5 /tmp/scheduled_agent_daemon.log 2>/dev/null || echo "")

    if echo "$LAST_LOG" | grep -qE "Fleet healthy|No task available|No open issues|All clear"; then
        echo ""
        echo "💤 Fleet idle — no task available. Waiting ${IDLE_WAIT_SECONDS}s before retry..."
        echo ""
        sleep "$IDLE_WAIT_SECONDS"
    else
        echo ""
        echo "✅ Task completed — immediately starting next task (per AGENTS.md Rule 5)"
        echo ""
        # No sleep — immediate next iteration (continuous execution)
    fi
done
