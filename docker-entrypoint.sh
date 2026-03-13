#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  Docker entrypoint: start server + dashboard side-by-side inside the container
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "[RDS] Starting API server on :${RDS_SERVER_PORT:-5000}"
rds-server &

echo "[RDS] Starting dashboard on :${RDS_DASHBOARD_PORT:-5001}"
rds-dashboard &

# Keep container alive and propagate signals
wait -n 2>/dev/null || wait
