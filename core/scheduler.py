#!/usr/bin/env python3
"""
core/scheduler.py — StoryLab Scheduled Fetching
--------------------------------------------------
Optional in-process timer that triggers core.aggregator.run() on an
interval, so you don't have to remember to click "Fetch now." Off by
default. Only runs while core/server.py is actively running -- there's
no background service in this app, so "every day" means "every day the
dashboard happens to be running," not a guaranteed always-on schedule.
See the README note in core/server.py's main() for the Task Scheduler
alternative if you need true always-on reliability.

fetch_lock is shared between this thread and the manual "Fetch now"
button (server.py's /api/fetch-now) so a scheduled and a manual fetch
can never run at the same time and collide over the SQLite file.
"""

import time
import threading
import importlib
from datetime import datetime, timezone, timedelta

POLL_SECONDS = 60  # how often the background thread checks whether a fetch is due

fetch_lock = threading.Lock()

_UNIT_SECONDS = {"hours": 3600, "days": 86400, "weeks": 604800}


def ensure_schedule_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fetch_schedule (
            config          TEXT    PRIMARY KEY,
            enabled         INTEGER NOT NULL DEFAULT 0,
            interval_value  INTEGER NOT NULL DEFAULT 1,
            interval_unit   TEXT    NOT NULL DEFAULT 'days',
            last_run        TEXT
        )
    """)
    conn.commit()


def get_schedule(conn, config):
    ensure_schedule_table(conn)
    row = conn.execute(
        "SELECT enabled, interval_value, interval_unit, last_run FROM fetch_schedule WHERE config = ?",
        (config,)
    ).fetchone()
    if not row:
        return {"enabled": False, "interval_value": 1, "interval_unit": "days", "last_run": None}
    return {
        "enabled": bool(row[0]),
        "interval_value": row[1],
        "interval_unit": row[2],
        "last_run": row[3],
    }


def save_schedule(conn, config, enabled, interval_value, interval_unit):
    ensure_schedule_table(conn)
    conn.execute("""
        INSERT INTO fetch_schedule (config, enabled, interval_value, interval_unit)
        VALUES (?,?,?,?)
        ON CONFLICT(config) DO UPDATE SET
            enabled = excluded.enabled,
            interval_value = excluded.interval_value,
            interval_unit = excluded.interval_unit
    """, (config, int(bool(enabled)), interval_value, interval_unit))
    conn.commit()


def _mark_ran(conn, config):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("UPDATE fetch_schedule SET last_run = ? WHERE config = ?", (now, config))
    conn.commit()


def _is_due(schedule):
    if not schedule["enabled"]:
        return False
    if not schedule["last_run"]:
        return True  # never run automatically before -- due immediately
    try:
        last = datetime.fromisoformat(schedule["last_run"])
    except ValueError:
        return True
    seconds = schedule["interval_value"] * _UNIT_SECONDS.get(schedule["interval_unit"], 86400)
    return datetime.now(timezone.utc) >= last + timedelta(seconds=seconds)


def run_scheduler_loop(db_path, config):
    """Target function for the background daemon thread started in
    server.py's main(). Never raises -- a bad fetch (network error, etc.)
    is already handled inside aggregator.run()/fetch_one_feed, and this
    loop itself is wrapped defensively so one bad cycle can't kill
    scheduled fetching for the rest of the session."""
    import sqlite3
    from core.aggregator import run as run_aggregator

    while True:
        try:
            conn = sqlite3.connect(db_path)
            schedule = get_schedule(conn, config)
            if _is_due(schedule):
                conn.close()
                with fetch_lock:
                    run_aggregator(config=config)
                conn = sqlite3.connect(db_path)
                _mark_ran(conn, config)
            conn.close()
        except Exception as e:
            print(f"  [scheduler] error: {e}")
        time.sleep(POLL_SECONDS)
