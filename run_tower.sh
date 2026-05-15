#!/bin/bash

# TOWER Unified Service Runner
# Launches API Hub (9042) and Kernel Node (9043) properly.

# Ensure we are in the workspace root
cd "$(dirname "$0")" || exit 1

# 0. Clean up stale processes
echo "[TOWER] Cleaning up stale processes on ports 9041, 9042, 9043..."
PORTS=(9041 9042 9043)
for port in "${PORTS[@]}"; do
    # Only target the process actually LISTENING on the port to avoid killing clients (like Chrome)
    pid=$(lsof -t -sTCP:LISTEN -i :$port)
    if [ -n "$pid" ]; then
        echo "        Killing listening process $pid on port $port"
        kill -9 $pid > /dev/null 2>&1
        sleep 0.2 # Give the OS a moment to release the socket
    fi
done

# 1. Sync Environment
echo "[TOWER] Syncing workspace environment..."
uv sync --quiet
echo "[TOWER] Syncing frontend environment..."
(cd tower_core/apps/frontend && npm install --silent)

# 2. Setup Logging
LOG_DIR="tower_core/logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
KERNEL_LOG="$LOG_DIR/kernel.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

echo "[TOWER] Logs redirected to $LOG_DIR"

# 3. Start API Hub (Port 9042)
echo "[TOWER] Starting API Hub on port 9042..."
# Use --package tower-api to ensure sub-package dependencies are available
TOWER_SERVICE=HUB uv run --package tower-api python tower_core/apps/api/main.py > "$BACKEND_LOG" 2>&1 &
API_PID=$!

# 4. Start Kernel Node (Port 9043)
echo "[TOWER] Starting Kernel Node on port 9043..."
# Start via uv package run (uv workspace linkage handles pathing)
uv run --package tower-kernel python tower_kernel/apps/k_server/main.py > "$KERNEL_LOG" 2>&1 &
KERNEL_PID=$!

# 5. Start Frontend UI (Port 9041)
echo "[TOWER] Starting Frontend UI on port 9041..."
(cd tower_core/apps/frontend && npm run dev > "../../logs/frontend.log" 2>&1) &
FRONTEND_PID=$!

echo "[TOWER] Services launched."
echo "        API PID: $API_PID"
echo "        Kernel PID: $KERNEL_PID"
echo "        UI PID: $FRONTEND_PID"
echo "        Run 'lsof -i :9041,9042,9043' to verify ports."

# Keep script alive just a moment to check for early failures
sleep 4

if ! ps -p $API_PID > /dev/null; then
  echo "[ERROR] API Hub failed to start. Check $BACKEND_LOG"
  exit 1
fi

if ! ps -p $KERNEL_PID > /dev/null; then
  echo "[ERROR] Kernel Node failed to start. Check $KERNEL_LOG"
  exit 1
fi

if ! ps -p $FRONTEND_PID > /dev/null; then
  echo "[ERROR] Frontend UI failed to start. Check $FRONTEND_LOG"
  exit 1
fi

echo "[TOWER] Services are running. UI accessible at http://localhost:9041"
lsof -i :9041,9042,9043 -sTCP:LISTEN
