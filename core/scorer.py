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


def score_article(title: str, summary: str, category: str, config: str) -> tuple[int, str]:
    """Return (relevance_score 1-5, story_type) for an article."""
    try:
        rules_mod = importlib.import_module(f"configs.{config}.scoring_rules")
        score = rules_mod.score(title, summary, category)
    except Exception:
        score = 2

    story_type = classify_story_type(title, summary)
    return score, story_type
