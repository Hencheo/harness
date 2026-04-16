#!/bin/bash
# Script to launch the Harness Cockpit in the correct environment
PROJECT_DIR="/home/hencheo/.gemini/antigravity/scratch/harness"
cd "$PROJECT_DIR"

# 1. Ensure Daemon is running
if ! ps aux | grep -v grep | grep "harness_daemon.py" > /dev/null
then
    echo "[LAUNCH] Starting Harness Daemon in background..."
    uv run python harness_daemon.py > harness_daemon.log 2>&1 &
    sleep 2
fi

# 2. Start Cockpit UI
echo "[LAUNCH] Starting Cockpit UI..."
uv run python harness_cli.py
