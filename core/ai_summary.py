#!/usr/bin/env python3
"""
core/ai_summary.py — StoryLab AI Category Summaries
-----------------------------------------------------
Per-flywheel-category standing instructions ("what to look for") and
AI-generated summaries of that category's 5-star articles.

Storage follows the same pattern as scoring_criteria (core/scorer.py) and
feeds (core/aggregator.py): editable from the dashboard, not code.

STATUS: the actual outbound AI call is not built yet -- generate_summary()
stops at a clearly marked TODO once it confirms an API key is present.
Everything else (instructions storage, summary storage, gathering a
category's 5-star articles, formatting them into fact-bounded source
capsules) is real and works today. See ADD_API_KEY.md at the repo root
for what changes when the key is added.
"""

import os
import sqlite3
import importlib
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(REPO_ROOT, ".env")


def load_dotenv(path=ENV_PATH):
    """Tiny stdlib-only .env loader -- no new dependency for something
    this small. Reads KEY=VALUE lines, skips blanks/comments, never
    overwrites a variable already set in the real environment."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def has_api_key():
    load_dotenv()
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def ensure_ai_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ai_instructions (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            config             TEXT    NOT NULL,
            flywheel_group     TEXT    NOT NULL,
            instructions_text  TEXT,
            updated_date       TEXT,
            UNIQUE(config, flywheel_group)
        );

        CREATE TABLE IF NOT EXISTS ai_summaries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            config          TEXT    NOT NULL,
            flywheel_group  TEXT    NOT NULL,
            generated_at    TEXT    NOT NULL,
            article_ids     TEXT,
            summary_text    TEXT,
            rationale_text  TEXT
        );
    """)
    conn.commit()


def _valid_groups(config):
    try:
        config_meta = importlib.import_module(f"configs.{config}")
        category_groups = getattr(config_meta, "CATEGORY_GROUPS", {})
    except ImportError:
        category_groups = {}
    groups = []
    for g in category_groups.values():
        if g not in groups:
            groups.append(g)
    return groups


def get_instructions(conn, config):
    """Returns {group: text} for every flywheel group, "" if never set."""
    ensure_ai_tables(conn)
    rows = conn.execute(
        "SELECT flywheel_group, instructions_text FROM ai_instructions WHERE config = ?",
        (config,)
    ).fetchall()
    saved = {r[0]: (r[1] or "") for r in rows}
    return {g: saved.get(g, "") for g in _valid_groups(config)}


def save_instructions(conn, config, group, text):
    ensure_ai_tables(conn)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO ai_instructions (config, flywheel_group, instructions_text, updated_date)
        VALUES (?,?,?,?)
        ON CONFLICT(config, flywheel_group) DO UPDATE SET
            instructions_text = excluded.instructions_text,
            updated_date = excluded.updated_date
    """, (config, group, text, now))
    conn.commit()


def get_latest_summary(conn, config, group):
    """Most recent real (never mock) generation for this group, or None."""
    ensure_ai_tables(conn)
    row = conn.execute("""
        SELECT id, generated_at, article_ids, summary_text, rationale_text
        FROM ai_summaries
        WHERE config = ? AND flywheel_group = ?
        ORDER BY generated_at DESC LIMIT 1
    """, (config, group)).fetchone()
    if not row:
        return None
    return {
        "id": row[0], "generated_at": row[1], "article_ids": row[2],
        "summary_text": row[3], "rationale_text": row[4],
    }


def get_five_star_articles(conn, config, group):
    """All 5-star articles belonging to this flywheel group, regardless of
    curation status -- the AI should see every strong signal, not just
    ones you've already queued. Handles both legacy raw categories (via
    CATEGORY_GROUPS) and new feeds tagged directly with the group name."""
    try:
        config_meta = importlib.import_module(f"configs.{config}")
        category_groups = getattr(config_meta, "CATEGORY_GROUPS", {})
    except ImportError:
        category_groups = {}
    raw_categories = [c for c, g in category_groups.items() if g == group]
    if group not in raw_categories:
        raw_categories.append(group)

    placeholders = ",".join("?" for _ in raw_categories)
    rows = conn.execute(f"""
        SELECT id, title, source, url, summary, published_date, story_type
        FROM articles
        WHERE config = ? AND relevance_score = 5 AND category IN ({placeholders})
        ORDER BY published_date DESC
    """, (config, *raw_categories)).fetchall()
    return [
        {"id": r[0], "title": r[1], "source": r[2], "url": r[3],
         "summary": r[4], "published_date": r[5], "story_type": r[6]}
        for r in rows
    ]


def build_source_capsules(articles):
    """Same fact-bounded capsule format the Story Brief panel already uses
    (core/dashboard.html's generateBriefBtn handler), just built in Python
    so the future API call can reuse it directly."""
    blocks = []
    for i, a in enumerate(articles, 1):
        summary = a["summary"] or ""
        thin = len(summary.split()) < 25
        block = (
            f"SOURCE {i}:\n"
            f"Title: {a['title']}\n"
            f"Outlet: {a['source']}\n"
            f"Date: {a['published_date'] or 'unknown'}\n"
            f"URL: {a['url']}\n"
            f"Relevance: 5/5 — {a['story_type'] or ''}\n"
            f"RSS Summary: {summary or '(none)'}\n"
        )
        if thin:
            block += "Note: thin summary — derive signal from title only, do not fabricate specifics.\n"
        blocks.append(block)
    return "\n---\n".join(blocks)


def generate_summary(conn, config, group):
    """Entry point the 'Generate Summaries' button calls. Returns a dict
    the frontend can render directly. The only unbuilt piece is the actual
    outbound API call -- everything up to that point (gathering this
    category's 5-star articles, building fact-bounded source capsules) is
    real and runs today."""
    if not has_api_key():
        return {
            "ok": False,
            "error": "no_api_key",
            "message": "No API key configured yet. See ADD_API_KEY.md for how to add one.",
        }

    articles = get_five_star_articles(conn, config, group)
    if not articles:
        return {
            "ok": False,
            "error": "no_articles",
            "message": f"No 5-star articles in {group} yet — nothing to summarize.",
        }

    instructions = get_instructions(conn, config).get(group, "")
    source_capsules = build_source_capsules(articles)  # noqa: F841 -- ready for the real call below

    # TODO (added when the API key is wired up): send `instructions` +
    # `source_capsules` to the Anthropic API via urllib.request (stdlib,
    # same as the RSS fetcher), parse the response into summary_text /
    # rationale_text, INSERT a row into ai_summaries, and return
    # {"ok": True, "summary": {...same shape as get_latest_summary()...}}
    # -- summaries.html's applySummary() already expects exactly that shape.
    return {
        "ok": False,
        "error": "not_implemented",
        "message": (
            "API key detected, but the live AI call hasn't been built yet. "
            f"Found {len(articles)} 5-star article(s) ready to summarize once it is."
        ),
    }
