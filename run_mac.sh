#!/bin/bash
# StoryLab — Mac launcher
# Usage: bash run_mac.sh [waypoint|longitude]

CONFIG="${1:-waypoint}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  StoryLab — $CONFIG"
echo "  Fetching feeds…"
python3 "$SCRIPT_DIR/core/aggregator.py" --config "$CONFIG"

echo ""
echo "  Starting dashboard…"
python3 "$SCRIPT_DIR/core/server.py" --config "$CONFIG"
