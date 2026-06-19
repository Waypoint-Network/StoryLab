#!/bin/bash
# StoryLab — Mac launcher
# Usage: bash run_mac.sh [travel_tech_ux|fan_atlas_insiders|longitude]

CONFIG="${1:-travel_tech_ux}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  StoryLab — $CONFIG"
echo "  Fetching feeds…"
python3 "$SCRIPT_DIR/core/aggregator.py" --config "$CONFIG"

echo ""
echo "  Starting dashboard…"
python3 "$SCRIPT_DIR/core/server.py" --config "$CONFIG"
