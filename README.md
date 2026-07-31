# StoryLab

## Running it

**Mac:** `bash run_mac.sh [travel_tech_ux|fan_atlas_insiders|longitude]`

**Windows:** double-click `run_windows.bat`, or run `run_windows.ps1` / `run_windows.bat [travel_tech_ux|fan_atlas_insiders|longitude]` from a terminal. Requires Python 3 on PATH (`python` or `py`).

Both launchers fetch feeds via `core/aggregator.py`, then start the dashboard via `core/server.py` at http://localhost:8765.