#!/usr/bin/env bash
# Scheduled Agent Daemon — runs run_scheduled_agent.sh every 45 minutes.
#
# বাংলা পরিচিতি:
# এই daemon background-এ চলে, প্রতি 45-min-এ run_scheduled_agent.sh call করে।
# Cron service না থাকায় sleep loop দিয়ে implement করা হয়েছে।
#
# Usage:
#   nohup bash scripts/agents/scheduled_agent_daemon.sh > /tmp/scheduled_agent_daemon.log 2>&1 &
#
# Stop:
#   pkill -f scheduled_agent_daemon.sh
#
# Check status:
#   tail -50 /tmp/scheduled_agent_daemon.log

INTERVAL_SECONDS=2700  # 45 minutes
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$SCRIPT_DIR/run_scheduled_agent.sh"

echo "🚀 Scheduled Agent Daemon started at $(date +%T)"
echo "   Interval: ${INTERVAL_SECONDS}s (45 min)"
echo "   Runner: $RUNNER"
echo "   PID: $$"
echo ""

# Loop forever
while true; do
    echo "=========================================="
    echo "🔄 Cycle at $(date +%T)"
    echo "=========================================="

    # Run the scheduled agent script
    bash "$RUNNER" 2>&1

    echo ""
    echo "💤 Sleeping ${INTERVAL_SECONDS}s (45 min) until next cycle..."
    echo ""
    sleep "$INTERVAL_SECONDS"
done
