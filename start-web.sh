#!/bin/bash
# RulePilot Web Console Launcher (macOS / Linux)
cd "$(dirname "$0")"

echo "========================================================"
echo "  RulePilot v3.2.0 - Local Routing Rule & DNS Manager"
echo "========================================================"
echo ""

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python 3 not found. Please install Python 3 first."
    read -p "Press Enter to exit..."
    exit 1
fi

$PYTHON_CMD rule_pilot.py ui
