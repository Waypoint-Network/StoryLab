#!/usr/bin/env python3
"""
core/scorer.py — StoryLab Article Scorer
-----------------------------------------
Scores articles at ingest on two dimensions:
  - relevance_score (1–5): how directly this serves the intended person-role
  - story_type: what kind of story this is

Scoring rules live in configs/{config}/scoring_rules.py.
"""

import importlib
import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

# Story type keyword sets — checked in priority order
_STORY_TYPE_KEYWORDS = [
    ("interview",    ["says", "according to", "q&a", "interview", "talks with", "speaks with",
                      "shares insight", "ceo", "director", "founder", "president", "vp of"]),
    ("case-study",   ["how ", "case study", "case-study", "program launch", "university launched",
                      "department rolled out", "implemented", "piloted", "results show",
                      "increased revenue", "drove bookings", "generated"]),
    ("tool-or-data", ["platform", "software", "tool", "app launch", "technology", "ai-powered",
                      "machine learning", "analytics platform", "dataset", "database", "product launch",
                      "new feature", "integration", "api"]),
    ("trend-signal", ["trend", "survey", "report finds", "study finds", "data shows", "growth",
                      "decline", "increase", "decrease", "rise", "fall", "%", "million",
                      "billion", "research", "index", "benchmark"]),
    ("opinion",      ["opinion", "commentary", "analysis:", "why ", "argues", "makes the case",
                      "perspective", "viewpoint", "the problem with", "rethinking", "unpopular"]),
]

_STORY_TYPE_DEFAULT = "trend-signal"


def classify_story_type(title: str, summary: str) -> str:
    text = (title + " " + (summary or "")).lower()
    for story_type, keywords in _STORY_TYPE_KEYWORDS:
        if any(kw in text for kw in keywords):
            return story_type
    return _STORY_TYPE_DEFAULT


def ensure_scoring_criteria_table(conn):
    """Editable scoring criteria live here instead of in Python source, so
    the dashboard's Scoring Criteria panel can add/remove them without
    touching code. Only used by configs that define CATEGORY_GROUPS
    (currently fan_atlas_insiders) -- other configs keep scoring entirely
    in their scoring_rules.py, untouched."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scoring_criteria (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            config          TEXT    NOT NULL,
            flywheel_group  TEXT    NOT NULL,
            score_level     INTEGER NOT NULL,
            keyword         TEXT    NOT NULL,
            UNIQUE(config, flywheel_group, score_level, keyword)
        )
    """)
    conn.commit()


def seed_scoring_criteria_if_empty(conn, config):
    """One-time population from configs/{config}/scoring_rules.py's
    SEED_CRITERIA, only if the table has no rows yet for this config.
    After that, the DB is the source of truth -- this never overwrites
    rows a user has already added or removed."""
    ensure_scoring_criteria_table(conn)
    existing = conn.execute(
        "SELECT COUNT(*) FROM scoring_criteria WHERE config = ?", (config,)
    ).fetchone()[0]
    if existing:
        return
    try:
        rules_mod = importlib.import_module(f"configs.{config}.scoring_rules")
        seed = getattr(rules_mod, "SEED_CRITERIA", [])
    except ImportError:
        seed = []
    if not seed:
        return
    conn.executemany(
        "INSERT OR IGNORE INTO scoring_criteria (config, flywheel_group, score_level, keyword) VALUES (?,?,?,?)",
        [(config, group, level, keyword) for group, level, keyword in seed],
    )
    conn.commit()


def _score_from_criteria(conn, title, summary, category, config, category_groups):
    """Look up the article's flywheel group from its raw category, then
    check that group's editable criteria highest score first. Returns
    None if the category isn't mapped to any group (caller should fall
    back to the config's scoring_rules.score())."""
    group = category_groups.get(category)
    if not group and category in category_groups.values():
        # Feeds added directly through the Feeds panel are tagged with the
        # flywheel group name itself (e.g. "Mobilizer"), not one of the
        # legacy raw category keys -- treat that as already being the group.
        group = category
    if not group:
        return None
    text = (title + " " + (summary or "")).lower()
    rows = conn.execute("""
        SELECT score_level, keyword FROM scoring_criteria
        WHERE config = ? AND flywheel_group = ?
        ORDER BY score_level DESC
    """, (config, group)).fetchall()
    for level, keyword in rows:
        if keyword.lower() in text:
            return level
    return 1


def score_article(title: str, summary: str, category: str, config: str, conn=None) -> tuple[int, str]:
    """Return (relevance_score 1-5, story_type) for an article.

    If the config defines CATEGORY_GROUPS and a DB connection is passed,
    scoring uses the editable scoring_criteria table, scoped to the
    article's flywheel group. Otherwise falls back to the config's
    scoring_rules.score() (its original flat keyword ladder)."""
    story_type = classify_story_type(title, summary)

    try:
        config_meta = importlib.import_module(f"configs.{config}")
        category_groups = getattr(config_meta, "CATEGORY_GROUPS", None)
    except ImportError:
        category_groups = None

    if category_groups and conn is not None:
        seed_scoring_criteria_if_empty(conn, config)
        score = _score_from_criteria(conn, title, summary, category, config, category_groups)
        if score is not None:
            return score, story_type

    try:
        rules_mod = importlib.import_module(f"configs.{config}.scoring_rules")
        score = rules_mod.score(title, summary, category)
    except Exception:
        score = 2

    return score, story_type
