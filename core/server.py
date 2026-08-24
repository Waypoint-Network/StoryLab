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
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

# Windows consoles default to a legacy codepage that can't encode the
# — character this script prints — force UTF-8 output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

DB_PATH        = os.path.join(REPO_ROOT, "curation.db")
HTML_PATH      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
CRITERIA_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "criteria.html")
FEEDS_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feeds.html")
SUMMARIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "summaries.html")
BRIEF_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brief.html")
SIGNALS_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signals.html")
FEED_HEALTH_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feed_health.html")
HELM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "helm.html")

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

        if path in ("/criteria", "/scoring-criteria"):
            self.send_html(CRITERIA_PATH)
            return

        if path == "/feeds":
            self.send_html(FEEDS_PATH)
            return

        if path == "/feed-health":
            self.send_html(FEED_HEALTH_PATH)
            return

        if path == "/signals":
            self.send_html(SIGNALS_PATH)
            return

        if path == "/helm":
            self.send_html(HELM_PATH)
            return

        if path in ("/summaries", "/briefs"):
            self.send_html(SUMMARIES_PATH)
            return

        if path.startswith("/briefs/"):
            self.send_html(BRIEF_PATH)
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

        if path == "/api/scoring-criteria":
            from core.scorer import seed_scoring_criteria_if_empty
            conn = get_conn()
            seed_scoring_criteria_if_empty(conn, _config)
            rows = conn.execute("""
                SELECT id, flywheel_group, score_level, keyword FROM scoring_criteria
                WHERE config = ? ORDER BY flywheel_group, score_level DESC, keyword
            """, (_config,)).fetchall()
            conn.close()
            try:
                config_meta = importlib.import_module(f"configs.{_config}")
                category_groups = getattr(config_meta, "CATEGORY_GROUPS", {})
            except ImportError:
                category_groups = {}
            groups = []
            for g in category_groups.values():
                if g not in groups:
                    groups.append(g)
            self.send_json({"groups": groups, "criteria": [dict(r) for r in rows]})
            return

        if path == "/api/feeds":
            from core.aggregator import seed_feeds_if_empty
            conn = get_conn()
            seed_feeds_if_empty(conn, _config)
            rows = conn.execute("""
                SELECT id, label, url, category, added_date FROM feeds
                WHERE config = ? ORDER BY category, label
            """, (_config,)).fetchall()
            conn.close()
            try:
                config_meta = importlib.import_module(f"configs.{_config}")
                category_groups = getattr(config_meta, "CATEGORY_GROUPS", {})
            except ImportError:
                category_groups = {}
            groups = []
            for g in category_groups.values():
                if g not in groups:
                    groups.append(g)
            self.send_json({
                "groups": groups,
                "category_groups": category_groups,
                "feeds": [dict(r) for r in rows],
            })
            return

        if path == "/api/fetch-schedule":
            from core.scheduler import get_schedule
            conn = get_conn()
            schedule = get_schedule(conn, _config)
            conn.close()
            self.send_json(schedule)
            return

        if path == "/api/ai-instructions":
            from core.ai_summary import get_instructions
            conn = get_conn()
            instructions = get_instructions(conn, _config)
            conn.close()
            self.send_json({"instructions": instructions})
            return

        if path == "/api/ai-summary":
            from core.ai_summary import get_latest_summary
            group = params.get("group", [""])[0]
            cadence = params.get("cadence", ["daily"])[0]
            if not group:
                self.send_json({"error": "group required"}, 400)
                return
            conn = get_conn()
            summary = get_latest_summary(conn, _config, group, cadence)
            conn.close()
            self.send_json({"summary": summary})
            return

        if path == "/api/feed-health":
            from core.aggregator import seed_feeds_if_empty
            conn = get_conn()
            seed_feeds_if_empty(conn, _config)
            feeds = conn.execute("""
                SELECT id, label, url, category FROM feeds
                WHERE config = ? ORDER BY category, label
            """, (_config,)).fetchall()
            health = []
            for feed in feeds:
                log = conn.execute("""
                    SELECT run_at, items_added, error FROM fetch_log
                    WHERE config = ? AND source = ? ORDER BY run_at DESC, id DESC LIMIT 1
                """, (_config, feed["label"])).fetchone()
                if log is None:
                    state = "never_checked"
                elif log["error"]:
                    state = "failing"
                else:
                    state = "healthy"
                health.append({**dict(feed), "state": state,
                               "last_checked": log["run_at"] if log else None,
                               "items_added": log["items_added"] if log else None,
                               "error": log["error"] if log else None})
            conn.close()
            self.send_json({"feeds": health})
            return

        if path == "/api/signal-directory":
            conn = get_conn()
            ensure_article_tags_table(conn)
            rows = conn.execute("""
                SELECT id, source, category, title, url, summary, published_date,
                       relevance_score, story_type
                FROM articles WHERE config = ?
                ORDER BY relevance_score DESC, published_date DESC LIMIT 500
            """, (_config,)).fetchall()
            tags = conn.execute("""
                SELECT article_tags.id, article_tags.article_id, article_tags.tag
                FROM article_tags JOIN articles ON articles.id = article_tags.article_id
                WHERE articles.config = ? ORDER BY article_tags.tag COLLATE NOCASE
            """, (_config,)).fetchall()
            conn.close()
            self.send_json({"articles": [dict(row) for row in rows],
                            "tags": [dict(row) for row in tags]})
            return

        if path == "/api/flywheel-briefs":
            from core.ai_summary import get_brief_groups, get_latest_flywheel_brief, get_five_star_articles
            conn = get_conn()
            briefs = []
            for group in get_brief_groups(_config):
                name = group["name"]
                briefs.append({
                    **group,
                    "article_count": len(get_five_star_articles(conn, _config, name)),
                    "generated_brief": get_latest_flywheel_brief(conn, _config, name),
                })
            conn.close()
            self.send_json({"briefs": briefs})
            return

        if path == "/api/flywheel-brief":
            from core.ai_summary import get_flywheel_brief
            group = params.get("group", [""])[0]
            if not group:
                self.send_json({"error": "group required"}, 400)
                return
            conn = get_conn()
            brief = get_flywheel_brief(conn, _config, group)
            conn.close()
            if brief is None:
                self.send_json({"error": "unknown flywheel group"}, 404)
                return
            self.send_json({"brief": brief})
            return

        if path == "/api/helm-signals":
            from core.helm import list_article_candidates, list_signals
            conn = get_conn()
            self.send_json({"candidates": list_article_candidates(conn, _config), "signals": list_signals(conn, _config)})
            conn.close()
            return

        if path == "/api/helm-connection-diagnostics":
            from core.helm import connection_diagnostics
            self.send_json(connection_diagnostics())
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

        if parsed.path == "/api/scoring-criteria":
            group   = (body.get("flywheel_group") or "").strip()
            level   = body.get("score_level")
            keyword = (body.get("keyword") or "").strip().lower()
            if not group or level not in (2, 3, 4, 5) or not keyword:
                self.send_json({"error": "flywheel_group, score_level (2-5), and keyword required"}, 400)
                return
            from core.scorer import ensure_scoring_criteria_table
            conn = get_conn()
            ensure_scoring_criteria_table(conn)
            conn.execute("""
                INSERT OR IGNORE INTO scoring_criteria (config, flywheel_group, score_level, keyword)
                VALUES (?,?,?,?)
            """, (_config, group, level, keyword))
            conn.commit()
            conn.close()
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/scoring-criteria/delete":
            crit_id = body.get("id")
            if not crit_id:
                self.send_json({"error": "id required"}, 400)
                return
            conn = get_conn()
            conn.execute("DELETE FROM scoring_criteria WHERE id = ? AND config = ?", (crit_id, _config))
            conn.commit()
            conn.close()
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/feeds":
            label    = (body.get("label") or "").strip()
            url      = (body.get("url") or "").strip()
            category = (body.get("category") or "").strip()
            if not label or not url or not category:
                self.send_json({"error": "label, url, and category required"}, 400)
                return
            try:
                config_meta = importlib.import_module(f"configs.{_config}")
                category_groups = getattr(config_meta, "CATEGORY_GROUPS", {})
            except ImportError:
                category_groups = {}
            valid_groups = set(category_groups.values())
            if valid_groups and category not in valid_groups:
                self.send_json({"error": f"category must be one of: {', '.join(valid_groups)}"}, 400)
                return

            from core.aggregator import ensure_feeds_table, fetch_one_feed
            conn = get_conn()
            ensure_feeds_table(conn)
            existing = conn.execute(
                "SELECT id FROM feeds WHERE config = ? AND url = ?", (_config, url)
            ).fetchone()
            if existing:
                conn.close()
                self.send_json({"error": "This feed URL is already added."}, 400)
                return

            result = fetch_one_feed(conn, label, url, category, _config)
            if not result["ok"]:
                conn.close()
                self.send_json({"error": f"Couldn't verify this feed: {result['error']}"}, 400)
                return

            conn.execute(
                "INSERT INTO feeds (config, label, url, category, added_date) VALUES (?,?,?,?,?)",
                (_config, label, url, category, datetime.now(timezone.utc).isoformat())
            )
            conn.commit()
            conn.close()
            self.send_json({"ok": True, "fetched": result["fetched"], "added": result["added"]})
            return

        if parsed.path == "/api/feeds/delete":
            feed_id = body.get("id")
            if not feed_id:
                self.send_json({"error": "id required"}, 400)
                return
            conn = get_conn()
            conn.execute("DELETE FROM feeds WHERE id = ? AND config = ?", (feed_id, _config))
            conn.commit()
            conn.close()
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/fetch-now":
            from core.aggregator import run as run_aggregator
            from core.scheduler import fetch_lock
            with fetch_lock:
                stats = run_aggregator(config=_config)
            self.send_json({"ok": True, **stats})
            return

        if parsed.path == "/api/fetch-schedule":
            enabled        = body.get("enabled")
            interval_value = body.get("interval_value")
            interval_unit  = (body.get("interval_unit") or "").strip()
            if enabled is None or not interval_value or interval_unit not in ("hours", "days", "weeks"):
                self.send_json({"error": "enabled, interval_value, and interval_unit (hours/days/weeks) required"}, 400)
                return
            from core.scheduler import save_schedule
            conn = get_conn()
            save_schedule(conn, _config, enabled, int(interval_value), interval_unit)
            conn.close()
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/ai-instructions":
            group = (body.get("flywheel_group") or "").strip()
            text  = body.get("text", "")
            if not group:
                self.send_json({"error": "flywheel_group required"}, 400)
                return
            from core.ai_summary import save_instructions
            conn = get_conn()
            save_instructions(conn, _config, group, text)
            conn.close()
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/generate-summary":
            group = (body.get("flywheel_group") or "").strip()
            cadence = (body.get("cadence") or "daily").strip()
            if not group:
                self.send_json({"error": "flywheel_group required"}, 400)
                return
            from core.ai_summary import generate_summary
            conn = get_conn()
            result = generate_summary(conn, _config, group, cadence)
            conn.close()
            self.send_json(result, 200 if result.get("ok") else 400)
            return

        if parsed.path == "/api/generate-flywheel-brief":
            group = (body.get("flywheel_group") or "").strip()
            if not group:
                self.send_json({"error": "flywheel_group required"}, 400)
                return
            from core.ai_summary import generate_flywheel_brief
            conn = get_conn()
            result = generate_flywheel_brief(conn, _config, group)
            conn.close()
            self.send_json(result, 200 if result.get("ok") else 400)
            return

        if parsed.path == "/api/flywheel-brief-status":
            brief_id = body.get("brief_id")
            status = (body.get("status") or "").strip()
            if not brief_id or not status:
                self.send_json({"error": "brief_id and status required"}, 400)
                return
            from core.ai_summary import update_flywheel_brief_status
            conn = get_conn()
            result = update_flywheel_brief_status(conn, _config, brief_id, status)
            conn.close()
            self.send_json(result, 200 if result.get("ok") else 400)
            return

        if parsed.path == "/api/article-tags":
            article_id = body.get("article_id")
            tag = (body.get("tag") or "").strip()
            if not article_id or not tag or len(tag) > 100:
                self.send_json({"error": "article_id and a tag of 100 characters or fewer are required"}, 400)
                return
            conn = get_conn()
            ensure_article_tags_table(conn)
            article = conn.execute("SELECT id FROM articles WHERE id = ? AND config = ?", (article_id, _config)).fetchone()
            if not article:
                conn.close(); self.send_json({"error": "article not found"}, 404); return
            conn.execute("INSERT OR IGNORE INTO article_tags (article_id, tag) VALUES (?,?)", (article_id, tag))
            conn.commit(); conn.close()
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/article-tags/delete":
            tag_id = body.get("id")
            if not tag_id:
                self.send_json({"error": "id required"}, 400)
                return
            conn = get_conn()
            ensure_article_tags_table(conn)
            conn.execute("""DELETE FROM article_tags WHERE id = ? AND article_id IN
                         (SELECT id FROM articles WHERE config = ?)""", (tag_id, _config))
            conn.commit(); conn.close()
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/rescore":
            from core.scorer import score_article
            conn = get_conn()
            rows = conn.execute(
                "SELECT id, title, summary, category, relevance_score FROM articles WHERE config = ?",
                (_config,)
            ).fetchall()
            changed = 0
            for r in rows:
                new_score, _ = score_article(r["title"], r["summary"] or "", r["category"], _config, conn)
                if new_score != r["relevance_score"]:
                    conn.execute("UPDATE articles SET relevance_score = ? WHERE id = ?", (new_score, r["id"]))
                    changed += 1
            conn.commit()
            conn.close()
            self.send_json({"ok": True, "rescored": len(rows), "changed": changed})
            return

        if parsed.path == "/api/helm-signals":
            from core.helm import create_signal_from_article
            conn = get_conn()
            result = create_signal_from_article(conn, _config, body.get("article_id"))
            conn.close()
            self.send_json(result, 200 if result.get("ok") else 400)
            return

        if parsed.path == "/api/helm-brief":
            from core.helm import prepare_signals_from_approved_brief
            conn = get_conn()
            result = prepare_signals_from_approved_brief(conn, _config, body.get("brief_id"))
            conn.close()
            self.send_json(result, 200 if result.get("ok") else 400)
            return

        if parsed.path == "/api/publish-helm-brief":
            from core.helm import publish_approved_brief
            conn = get_conn()
            result = publish_approved_brief(conn, _config, body.get("brief_id"))
            conn.close()
            self.send_json(result, 200 if result.get("ok") else 400)
            return

        if parsed.path.startswith("/api/helm-signals/"):
            try:
                signal_id = int(parsed.path.rsplit("/", 1)[1])
            except ValueError:
                self.send_json({"error": "invalid signal id"}, 400)
                return
            from core.helm import save_signal
            conn = get_conn()
            result = save_signal(conn, _config, signal_id, body)
            conn.close()
            self.send_json(result, 200 if result.get("ok") else 400)
            return

        if parsed.path == "/api/helm-publish":
            from core.helm import publish_signals
            conn = get_conn()
            result = publish_signals(conn, _config, body.get("signal_ids", []))
            conn.close()
            self.send_json(result, 200 if result.get("ok") else 400)
            return

        self.send_response(404)
        self.end_headers()


def ensure_article_tags_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            UNIQUE(article_id, tag)
        )
    """)
    conn.commit()


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

    from core.scorer import seed_scoring_criteria_if_empty
    from core.aggregator import seed_feeds_if_empty
    from core.ai_summary import ensure_ai_tables
    from core.scheduler import ensure_schedule_table
    seed_conn = sqlite3.connect(DB_PATH)
    seed_scoring_criteria_if_empty(seed_conn, _config)
    seed_feeds_if_empty(seed_conn, _config)
    ensure_ai_tables(seed_conn)
    from core.helm import ensure_helm_tables
    ensure_helm_tables(seed_conn)
    ensure_schedule_table(seed_conn)
    seed_conn.close()

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

    # Scheduled fetching (set from the /feeds page) only runs while this
    # process is alive -- there's no background service in this app. For
    # true always-on scheduling regardless of whether the dashboard is
    # open, wire `python core/aggregator.py --config <name>` into your
    # OS's own scheduler instead (Windows Task Scheduler / macOS cron)
    # and leave the in-app schedule below turned off.
    from core.scheduler import run_scheduler_loop
    threading.Thread(target=run_scheduler_loop, args=(DB_PATH, _config), daemon=True).start()

    server = ThreadingHTTPServer(("localhost", args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")


if __name__ == "__main__":
    main()
