#!/usr/bin/env python3
"""
core/ai_summary.py — StoryLab AI Category Summaries
-----------------------------------------------------
Per-flywheel-category standing instructions ("what to look for"), legacy
AI-summary scaffolding, and saved source-only Flywheel Intelligence Briefs.

Storage follows the same pattern as scoring_criteria (core/scorer.py) and
feeds (core/aggregator.py): editable from the dashboard, not code.

STATUS: the actual outbound AI call is not built yet -- generate_summary()
stops at a clearly marked TODO once it confirms an API key is present. The
source-only generate_flywheel_brief() workflow is real: it saves a dated,
fact-bounded brief from current five-star source articles without an AI or
network call. See ADD_API_KEY.md for the separate future AI path.
"""

import os
import sqlite3
import importlib
import json
from datetime import datetime, timezone

BRIEF_ARTICLE_MAX_AGE_DAYS = 90

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
    return bool(os.environ.get("OPENAI_API_KEY"))


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

        CREATE TABLE IF NOT EXISTS flywheel_briefs (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            config              TEXT    NOT NULL,
            flywheel_group      TEXT    NOT NULL,
            generated_at        TEXT    NOT NULL,
            source_article_ids  TEXT    NOT NULL,
            freshness_date      TEXT,
            what_changed        TEXT    NOT NULL,
            why_it_matters      TEXT    NOT NULL,
            suggested_next_step TEXT    NOT NULL,
            supporting_material TEXT    NOT NULL,
            new_source_article_ids TEXT NOT NULL DEFAULT '[]',
            review_status       TEXT    NOT NULL DEFAULT 'draft',
            reviewed_at         TEXT,
            helm_publish_status TEXT    NOT NULL DEFAULT 'not_published',
            helm_published_at   TEXT,
            helm_last_attempt_at TEXT,
            helm_last_error     TEXT,
            helm_payload_version INTEGER NOT NULL DEFAULT 1
        );
    """)
    _ensure_column(conn, "flywheel_briefs", "new_source_article_ids", "TEXT NOT NULL DEFAULT '[]'")
    _ensure_column(conn, "flywheel_briefs", "review_status", "TEXT NOT NULL DEFAULT 'draft'")
    _ensure_column(conn, "flywheel_briefs", "reviewed_at", "TEXT")
    _ensure_column(conn, "flywheel_briefs", "helm_publish_status", "TEXT NOT NULL DEFAULT 'not_published'")
    _ensure_column(conn, "flywheel_briefs", "helm_published_at", "TEXT")
    _ensure_column(conn, "flywheel_briefs", "helm_last_attempt_at", "TEXT")
    _ensure_column(conn, "flywheel_briefs", "helm_last_error", "TEXT")
    _ensure_column(conn, "flywheel_briefs", "helm_payload_version", "INTEGER NOT NULL DEFAULT 1")
    conn.commit()


def _ensure_column(conn, table, column, definition):
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


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


def get_brief_groups(config):
    """Return the configured flywheel groups with display metadata.

    Config metadata is optional so the shared engine still works for the
    other StoryLab contexts. Fan Atlas supplies durable labels and slugs.
    """
    try:
        config_meta = importlib.import_module(f"configs.{config}")
        definitions = getattr(config_meta, "FLYWHEEL_BRIEFS", {})
    except ImportError:
        definitions = {}
    return [
        {"name": group, **definitions.get(group, {})}
        for group in _valid_groups(config)
    ]


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


def get_latest_flywheel_brief(conn, config, group):
    """Return the newest source-only brief for a flywheel group, if any."""
    ensure_ai_tables(conn)
    row = conn.execute("""
        SELECT id, generated_at, source_article_ids, freshness_date,
               what_changed, why_it_matters, suggested_next_step,
               supporting_material, new_source_article_ids, review_status,
               reviewed_at, helm_publish_status, helm_published_at,
               helm_last_attempt_at, helm_last_error, helm_payload_version
        FROM flywheel_briefs
        WHERE config = ? AND flywheel_group = ?
        ORDER BY generated_at DESC, id DESC LIMIT 1
    """, (config, group)).fetchone()
    if not row:
        return None
    return {
        "id": row[0], "generated_at": row[1],
        "source_article_ids": json.loads(row[2]), "freshness_date": row[3],
        "what_changed": row[4], "why_it_matters": row[5],
        "suggested_next_step": row[6], "supporting_material": json.loads(row[7]),
        "new_source_article_ids": json.loads(row[8] or "[]"),
        "review_status": row[9] or "draft", "reviewed_at": row[10],
        "helm_publish_status": row[11] or "not_published", "helm_published_at": row[12],
        "helm_last_attempt_at": row[13], "helm_last_error": row[14],
        "helm_payload_version": row[15] or 1,
    }


def get_five_star_articles(conn, config, group):
    """All 5-star articles belonging to this flywheel group, regardless of
    curation status. Brief generation reviews every strong signal, not just
    ones already queued. Handles both legacy raw categories (via
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
        SELECT id, title, source, url, summary, published_date, fetched_date, story_type, category
        FROM articles
        WHERE config = ? AND relevance_score = 5 AND category IN ({placeholders})
        ORDER BY published_date DESC
    """, (config, *raw_categories)).fetchall()
    all_articles = [
        {"id": r[0], "title": r[1], "source": r[2], "url": r[3],
         "summary": r[4], "published_date": r[5], "fetched_date": r[6],
         "story_type": r[7], "category": r[8]}
        for r in rows
    ]
    cutoff = datetime.now(timezone.utc).timestamp() - (BRIEF_ARTICLE_MAX_AGE_DAYS * 86400)
    def is_current(article):
        value = article.get("published_date") or article.get("fetched_date")
        if not value:
            return False
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() >= cutoff
        except ValueError:
            return False
    return [article for article in all_articles if is_current(article)]


def get_previously_briefed_article_ids(conn, config, group):
    """Every source already included in a prior brief for this flywheel.

    Comparison is intentionally against full history rather than only the last
    brief, so a persistent five-star source cannot recur in every daily brief.
    """
    ensure_ai_tables(conn)
    ids = set()
    rows = conn.execute("""
        SELECT source_article_ids FROM flywheel_briefs
        WHERE config = ? AND flywheel_group = ?
    """, (config, group)).fetchall()
    for row in rows:
        try:
            ids.update(json.loads(row[0] or "[]"))
        except (TypeError, json.JSONDecodeError):
            continue
    return ids


def get_flywheel_brief(conn, config, group):
    """Return the durable, fact-bounded brief workspace for one group.

    A saved AI summary is optional. The source articles are always returned
    so an operator can review the actual evidence before a summary exists.
    """
    groups = {item["name"]: item for item in get_brief_groups(config)}
    if group not in groups:
        return None
    return {
        "group": groups[group],
        "instructions": get_instructions(conn, config).get(group, ""),
        "generated_brief": get_latest_flywheel_brief(conn, config, group),
        "articles": get_five_star_articles(conn, config, group),
    }


def _freshness_date(articles):
    dates = [a.get("published_date") or a.get("fetched_date") for a in articles]
    return max((value for value in dates if value), default=None)


def generate_flywheel_brief(conn, config, group):
    """Create and save a concise, source-only intelligence brief.

    This intentionally makes no AI or network call. It reports what the
    curated source set contains, preserves exact stored supporting material,
    and frames a group-specific question instead of inventing a conclusion.
    """
    groups = {item["name"]: item for item in get_brief_groups(config)}
    if group not in groups:
        return {"ok": False, "error": "unknown_group", "message": "Unknown flywheel group."}
    previous = get_latest_flywheel_brief(conn, config, group)
    current_articles = get_five_star_articles(conn, config, group)
    if not current_articles:
        return {
            "ok": False, "error": "no_articles",
            "message": f"No current five-star articles in {group} from the last {BRIEF_ARTICLE_MAX_AGE_DAYS} days.",
        }

    previously_briefed_ids = get_previously_briefed_article_ids(conn, config, group)
    articles = [article for article in current_articles if article["id"] not in previously_briefed_ids]
    if not articles:
        return {
            "ok": False, "error": "no_new_articles",
            "message": f"No new five-star material in {group} since the last brief. No summary was generated.",
        }

    metadata = groups[group]
    freshness = _freshness_date(articles)
    source_ids = [article["id"] for article in articles]
    new_source_ids = source_ids[:]
    supporting_material = [
        {
            "article_id": article["id"], "title": article["title"],
            "source": article["source"], "url": article["url"],
            "published_date": article["published_date"],
            "exact_rss_summary": article["summary"] or "",
        }
        for article in articles
    ]
    latest = articles[:5]
    changed_lines = [
        f"{article['title']} ({article['source']}, {(article['published_date'] or article['fetched_date'] or 'date unavailable')[:10]})"
        for article in latest
    ]
    new_label = "all current sources on this first brief" if previous is None else f"{len(new_source_ids)} new since the previous brief"
    suffix = "" if len(articles) <= len(latest) else f" The evidence section retains all {len(articles)} new five-star sources."
    what_changed = (
        f"{len(articles)} five-star source{' is' if len(articles) == 1 else 's are'} currently in {group}; {new_label}. "
        f"Most recent signals: " + "; ".join(changed_lines) + "." + suffix
    )
    why_it_matters = (
        f"These sources were scored into the {group} flywheel group. "
        f"{metadata.get('description', 'Review the source material before drawing a conclusion.')} "
        "This is a review cue based on the curated source set, not a claim that the described practice will work for Fan Atlas."
    )
    suggested_next_step = metadata.get(
        "suggested_question",
        "Which source detail is concrete enough to validate before deciding whether to act?",
    )
    generated_at = datetime.now(timezone.utc).isoformat()
    ensure_ai_tables(conn)
    conn.execute("""
        INSERT INTO flywheel_briefs
          (config, flywheel_group, generated_at, source_article_ids, freshness_date,
           what_changed, why_it_matters, suggested_next_step, supporting_material,
           new_source_article_ids, review_status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        config, group, generated_at, json.dumps(source_ids), freshness,
        what_changed, why_it_matters, suggested_next_step,
        json.dumps(supporting_material), json.dumps(new_source_ids), "draft",
    ))
    conn.commit()
    return {"ok": True, "brief": get_latest_flywheel_brief(conn, config, group)}


def update_flywheel_brief_status(conn, config, brief_id, status):
    """Apply the human review state to a saved brief."""
    if status not in {"draft", "reviewed", "approved"}:
        return {"ok": False, "message": "Status must be draft, reviewed, or approved."}
    ensure_ai_tables(conn)
    reviewed_at = datetime.now(timezone.utc).isoformat() if status != "draft" else None
    cursor = conn.execute("""
        UPDATE flywheel_briefs SET review_status = ?, reviewed_at = ?
        WHERE id = ? AND config = ?
    """, (status, reviewed_at, brief_id, config))
    conn.commit()
    if not cursor.rowcount:
        return {"ok": False, "message": "Brief not found."}
    row = conn.execute("SELECT flywheel_group FROM flywheel_briefs WHERE id = ?", (brief_id,)).fetchone()
    return {"ok": True, "brief": get_latest_flywheel_brief(conn, config, row[0])}


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
    # `source_capsules` to the OpenAI API via urllib.request (stdlib,
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
