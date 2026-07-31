#!/usr/bin/env python3
"""
core/server.py — StoryLab Curation Dashboard
---------------------------------------------
Starts a local web server with the review dashboard.

Usage:
    python core/server.py --config travel_tech_ux
    python core/server.py --config fan_atlas_insiders
    python core/server.py --config longitude
    python core/server.py --config travel_tech_ux --port 9000
    python core/server.py --config travel_tech_ux --no-open
"""

import sqlite3
import json
import os
import argparse
import importlib
import webbrowser
import threading
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

# Windows consoles default to a legacy codepage that can't encode the
# — character this script prints — force UTF-8 output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

DB_PATH   = os.path.join(REPO_ROOT, "curation.db")
HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")

_config = "travel_tech_ux"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, path):
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        params = parse_qs(parsed.query)

        if path in ("/", "/dashboard"):
            self.send_html(HTML_PATH)
            return

        if path == "/api/articles":
            conn = get_conn()
            status_filter    = params.get("status",    ["all"])[0]
            category_filter  = params.get("category",  ["all"])[0]
            days_filter      = int(params.get("days",  [14])[0])
            min_relevance    = int(params.get("min_relevance", [0])[0])

            query = """
                SELECT id, source, category, title, url, summary,
                       published_date, status, relevance_score, story_type, issue_tag, notes
                FROM articles
                WHERE config = ?
            """
            args = [_config]

            if status_filter != "all":
                query += " AND status = ?"
                args.append(status_filter)
            if category_filter != "all":
                query += " AND category = ?"
                args.append(category_filter)
            if days_filter > 0:
                query += " AND (published_date IS NULL OR published_date >= datetime('now', ?))"
                args.append(f"-{days_filter} days")
            if min_relevance > 0:
                query += " AND relevance_score >= ?"
                args.append(min_relevance)

            query += " ORDER BY relevance_score DESC, published_date DESC NULLS LAST LIMIT 500"

            rows = conn.execute(query, args).fetchall()
            conn.close()
            self.send_json([dict(r) for r in rows])
            return

        if path == "/api/stats":
            conn = get_conn()
            stats = {}
            for row in conn.execute(
                "SELECT status, COUNT(*) as n FROM articles WHERE config = ? GROUP BY status",
                (_config,)
            ):
                stats[row["status"]] = row["n"]
            stats["total"] = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE config = ?", (_config,)
            ).fetchone()[0]
            last_fetch = conn.execute(
                "SELECT MAX(run_at) FROM fetch_log WHERE config = ?", (_config,)
            ).fetchone()[0]
            stats["last_fetch"] = last_fetch
            stats["config"] = _config
            try:
                config_meta = importlib.import_module(f"configs.{_config}")
                stats["display_name"] = getattr(config_meta, "DISPLAY_NAME", _config.capitalize())
                stats["closing_line"] = getattr(config_meta, "CLOSING_LINE", "")
                stats["category_groups"] = getattr(config_meta, "CATEGORY_GROUPS", {})
            except ImportError:
                stats["display_name"] = _config.capitalize()
                stats["closing_line"] = ""
                stats["category_groups"] = {}
            # Dynamic category list
            cats = conn.execute(
                "SELECT DISTINCT category FROM articles WHERE config = ? ORDER BY category",
                (_config,)
            ).fetchall()
            stats["categories"] = [r[0] for r in cats]
            conn.close()
            self.send_json(stats)
            return

        if path == "/api/export":
            conn = get_conn()
            rows = conn.execute("""
                SELECT id, source, category, title, url, summary,
                       published_date, issue_tag, notes, relevance_score, story_type
                FROM articles WHERE status = 'in_queue' AND config = ?
                ORDER BY relevance_score DESC, category, published_date DESC
            """, (_config,)).fetchall()
            conn.close()
            self.send_json([dict(r) for r in rows])
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body   = json.loads(self.rfile.read(length)) if length else {}

        if parsed.path == "/api/update":
            article_id = body.get("id")
            new_status  = body.get("status")
            issue_tag   = body.get("issue_tag")
            notes       = body.get("notes")
            if not article_id or not new_status:
                self.send_json({"error": "id and status required"}, 400)
                return
            conn = get_conn()
            conn.execute("""
                UPDATE articles
                SET status = ?, issue_tag = COALESCE(?, issue_tag), notes = COALESCE(?, notes)
                WHERE id = ?
            """, (new_status, issue_tag, notes, article_id))
            conn.commit()
            conn.close()
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/bulk-update":
            ids = body.get("ids", [])
            new_status = body.get("status")
            if not ids or not new_status:
                self.send_json({"error": "ids and status required"}, 400)
                return
            conn = get_conn()
            conn.executemany("UPDATE articles SET status = ? WHERE id = ?",
                             [(new_status, i) for i in ids])
            conn.commit()
            conn.close()
            self.send_json({"ok": True, "updated": len(ids)})
            return

        self.send_response(404)
        self.end_headers()


def main():
    global _config
    parser = argparse.ArgumentParser()
    parser.add_argument("--config",  default="travel_tech_ux",
                         choices=["travel_tech_ux", "fan_atlas_insiders", "longitude"])
    parser.add_argument("--port",    type=int, default=8765)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    _config = args.config

    if not os.path.exists(DB_PATH):
        from core.aggregator import init_db
        conn = sqlite3.connect(DB_PATH)
        init_db(conn)
        conn.close()
        print(f"  Created new database. Run aggregator.py --config {_config} to populate it.")

    try:
        config_meta = importlib.import_module(f"configs.{_config}")
        display_name = getattr(config_meta, "DISPLAY_NAME", _config.capitalize())
    except ImportError:
        display_name = _config.capitalize()

    url = f"http://localhost:{args.port}"
    print(f"\n  StoryLab Dashboard — {display_name}")
    print(f"  Open: {url}")
    print(f"  Stop: Ctrl+C\n")

    if not args.no_open:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    server = HTTPServer(("localhost", args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")


if __name__ == "__main__":
    main()
