#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  Ransomware Detector — Linux / macOS installer
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

log()   { echo -e "${GREEN}✔${RESET}  $*"; }
warn()  { echo -e "${YELLOW}⚠${RESET}  $*"; }
error() { echo -e "${RED}✗${RESET}  $*"; exit 1; }

echo -e "\n${BOLD}Ransomware Detector — Installer${RESET}\n"

# ── 1. Locate Python 3.9+ ────────────────────────────────────────────────────
PYTHON=""
for candidate in python3 python3.12 python3.11 python3.10 python3.9; do
  if command -v "$candidate" &>/dev/null; then
    version=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    major="${version%%.*}"
    minor="${version#*.}"
    if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
      PYTHON="$candidate"
      break
    fi
  fi
done
[ -z "$PYTHON" ] && error "Python 3.9+ not found. Please install it from https://python.org"
log "Using $PYTHON ($version)"

# ── 2. Virtual environment ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
  "$PYTHON" -m venv .venv
  log "Created virtual environment (.venv)"
else
  log "Virtual environment already exists (.venv)"
fi

source .venv/bin/activate

# ── 3. Upgrade pip ────────────────────────────────────────────────────────────
pip install --quiet --upgrade pip
log "pip upgraded"

# ── 4. Install runtime dependencies (fast) ───────────────────────────────────
pip install --quiet -r requirements.runtime.txt
log "Runtime dependencies installed"

# ── 5. Install the package (entry points only, no heavy extras) ──────────────
pip install --quiet --no-deps -e .
log "Package installed (rds-server, rds-agent, rds-dashboard commands ready)"

# Optional: pass --full to also install ML / cloud / Telegram extras
if [[ "${1:-}" == "--full" ]]; then
  warn "Installing full dependencies (this may take several minutes)…"
  pip install --quiet -e ".[full]"
  log "Full dependencies installed"
fi

# ── 5. Copy default config ───────────────────────────────────────────────────
if [ ! -f "config.json" ]; then
  cp config.example.json config.json
  log "Created config.json from config.example.json — edit as needed"
else
  warn "config.json already exists — not overwritten"
fi

echo -e "\n${BOLD}${GREEN}Installation complete!${RESET}\n"
echo -e "  Start the app:   ${BOLD}bash run.sh${RESET}"
echo -e "  Or individually:"
echo -e "    Server:         ${BOLD}rds-server${RESET}    (port 5000)"
echo -e "    Dashboard:      ${BOLD}rds-dashboard${RESET} (port 5001)"
echo -e "    Agent:          ${BOLD}rds-agent --config config.json${RESET}"
echo ""
