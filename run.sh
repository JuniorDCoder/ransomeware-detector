#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  Ransomware Detector — Start server + dashboard (Linux / macOS)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RESET="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
  echo -e "${YELLOW}⚠${RESET}  .venv not found — run install.sh first"
  exit 1
fi

source .venv/bin/activate

SERVER_HOST="${RDS_SERVER_HOST:-127.0.0.1}"
SERVER_PORT="${RDS_SERVER_PORT:-5000}"
DASH_HOST="${RDS_DASHBOARD_HOST:-127.0.0.1}"
DASH_PORT="${RDS_DASHBOARD_PORT:-5001}"

echo -e "\n${BOLD}Ransomware Detector — Starting${RESET}\n"
echo -e "  ${GREEN}Server${RESET}    → http://${SERVER_HOST}:${SERVER_PORT}"
echo -e "  ${GREEN}Dashboard${RESET} → http://${DASH_HOST}:${DASH_PORT}"
echo -e "\n  Press ${BOLD}Ctrl+C${RESET} to stop all processes\n"

# Start server in background
rds-server &
SERVER_PID=$!

# Brief pause so the server binds before dashboard starts
sleep 1

# Start dashboard in background
rds-dashboard &
DASH_PID=$!

# Open browser (best-effort)
DASHBOARD_URL="http://${DASH_HOST}:${DASH_PORT}"
if command -v xdg-open &>/dev/null; then
  sleep 2 && xdg-open "$DASHBOARD_URL" &
elif command -v open &>/dev/null; then
  sleep 2 && open "$DASHBOARD_URL" &
fi

# Wait and clean up on Ctrl+C
cleanup() {
  echo -e "\n${YELLOW}Stopping...${RESET}"
  kill "$SERVER_PID" "$DASH_PID" 2>/dev/null || true
  wait "$SERVER_PID" "$DASH_PID" 2>/dev/null || true
  echo "Stopped."
}
trap cleanup INT TERM

wait "$SERVER_PID" "$DASH_PID"
