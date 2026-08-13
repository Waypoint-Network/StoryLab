# StoryLab

## Running it

**Mac:** `bash run_mac.sh [travel_tech_ux|fan_atlas_insiders|longitude]`

**Windows:** double-click `run_windows.bat`, or run `run_windows.ps1` / `run_windows.bat [travel_tech_ux|fan_atlas_insiders|longitude]` from a terminal. Requires Python 3 on PATH (`python` or `py`).

Both launchers fetch feeds via `core/aggregator.py`, then start the dashboard via `core/server.py` at http://localhost:8765.

## Helm publishing (local Strategy Lab -> The Helm)

Open `http://localhost:8765/helm` to prepare source articles as reviewed signals. Signals retain their original source evidence locally and publish only after an operator marks them **approved**. Copy `.env.example` to `.env` and set `HELM_STRATEGY_ENDPOINT` and `HELM_STRATEGY_API_KEY`; `.env` is ignored by Git. The Helm endpoint receives one or more idempotent signals, each identified by its stable local `external_id`.
