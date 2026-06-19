#!/usr/bin/env python3
"""
core/brief_generator.py — StoryLab Story Brief Generator
----------------------------------------------------------
Queries top high-relevance articles from the past 7 days and outputs a
structured markdown Story Brief for the operator to review and route.

Usage:
    python core/brief_generator.py --config travel_tech_ux
    python core/brief_generator.py --config travel_tech_ux --days 14
    python core/brief_generator.py --config travel_tech_ux --min-score 3
    python core/brief_generator.py --config travel_tech_ux --out output/briefs/brief_2026-05-26.md
"""

import sqlite3
import argparse
import importlib
import sys
import os
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
DB_PATH = os.path.join(REPO_ROOT, "curation.db")

STORY_TYPE_LABELS = {
    "trend-signal": "Trend Signal",
    "case-study":   "Case Study",
    "tool-or-data": "Tool / Data",
    "interview":    "Interview",
    "opinion":      "Opinion",
}

FORMAT_RECOMMENDATIONS = {
    "trend-signal": ["text", "infographic", "short video"],
    "case-study":   ["text", "podcast", "long video"],
    "tool-or-data": ["tool-or-database", "text", "infographic"],
    "interview":    ["podcast", "text", "short video"],
    "opinion":      ["text", "meme", "short video"],
}


def generate_brief(config="travel_tech_ux", days=7, min_score=4, out_path=None):
    roles_mod = importlib.import_module(f"configs.{config}.person_roles")
    PERSON_ROLES = roles_mod.PERSON_ROLES

    config_meta = importlib.import_module(f"configs.{config}")
    display_name = getattr(config_meta, "DISPLAY_NAME", config.capitalize())
    closing_line = getattr(config_meta, "CLOSING_LINE", None)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, source, category, title, url, summary,
               published_date, relevance_score, story_type
        FROM articles
        WHERE config = ?
          AND status IN ('new', 'saved', 'in_queue')
          AND relevance_score >= ?
          AND (published_date IS NULL OR published_date >= datetime('now', ?))
        ORDER BY relevance_score DESC, published_date DESC
        LIMIT 10
    """, (config, min_score, f"-{days} days")).fetchall()
    conn.close()

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %d, %Y")

    lines = [
        f"# StoryLab — Weekly Story Brief",
        f"**Config:** {display_name}  ",
        f"**Generated:** {date_str}  ",
        f"**Articles:** {len(rows)} (score ≥{min_score}, past {days} days)  ",
        "",
        "---",
        "",
        "## FACT BOUNDARY (NON-NEGOTIABLE)",
        "",
        "Only assert specifics present in the RSS summary below.",
        "Do not fabricate statistics, quotes, or program details.",
        "Label hypotheses with 'likely' or 'may'.",
        f"Do not pitch {display_name} explicitly — persuasion is implicit through credibility.",
        "",
        "---",
        "",
        "## Person Roles",
        "",
    ]

    for role in PERSON_ROLES:
        lines.append(f"- **{role['name']}** — {role['description']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Source Capsules")
    lines.append("")

    for i, row in enumerate(rows, 1):
        score_stars = "★" * (row["relevance_score"] or 0) + "☆" * (5 - (row["relevance_score"] or 0))
        story_label = STORY_TYPE_LABELS.get(row["story_type"], row["story_type"] or "–")
        fmt_recs = FORMAT_RECOMMENDATIONS.get(row["story_type"], ["text"])
        thin = not row["summary"] or len((row["summary"] or "").split()) < 25

        lines += [
            f"### SOURCE {i}: {row['title']}",
            "",
            f"- **Outlet:** {row['source']}",
            f"- **Category:** {row['category']}",
            f"- **Date:** {(row['published_date'] or '')[:10]}",
            f"- **Relevance:** {score_stars} ({row['relevance_score']}/5)",
            f"- **Story type:** {story_label}",
            f"- **Recommended formats:** {' / '.join(fmt_recs)}",
            f"- **URL:** {row['url']}",
            f"- **RSS Summary:** {row['summary'] or '(none)'}",
        ]
        if thin:
            lines.append("- **Note:** Thin summary — derive signal from title only, do not fabricate specifics.")
        lines += [
            "",
            "**Fill in before routing:**",
            "- Signal: [what shifted or was confirmed]",
            "- Meaning: [why this matters to the intended person-role]",
            "- Mechanism: [how it changes behavior or outcomes]",
            "- Action: [what the operator or reader should do]",
            "- Measurement: [what to track]",
            "",
        ]

    lines += [
        "---",
        "",
        "## Story Brief Fields",
        "",
        "Complete these fields after reviewing the source capsules above.",
        "",
        "- **Story type:** [trend-signal / case-study / tool-or-data / interview / opinion]",
        "- **Intended person-role:** [name from Person Roles above]",
        "- **Recommended formats (ranked):** [text / meme / infographic / tool-or-database / audio / podcast / short video / long video / game]",
        "- **Calendar moment / trigger:** [current season moment or evergreen]",
        "- **Suggested angle / hook:** [one sentence — the hill to die on]",
    ]

    if closing_line:
        lines.append(closing_line)
    else:
        lines.append("- **Closing line:** [define CLOSING_LINE in this config's __init__.py]")

    lines += [
        "",
        "---",
        f"*StoryLab brief generated {date_str}*",
    ]

    brief = "\n".join(lines)

    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            f.write(brief)
        print(f"Brief written to: {out_path}")
    else:
        print(brief)

    return brief


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StoryLab Story Brief Generator")
    parser.add_argument("--config",    default="travel_tech_ux",
                         choices=["travel_tech_ux", "fan_atlas_insiders", "longitude"])
    parser.add_argument("--days",      type=int, default=7)
    parser.add_argument("--min-score", type=int, default=4)
    parser.add_argument("--out",       default="", help="Output file path (default: stdout)")
    args = parser.parse_args()

    out = args.out
    if not out:
        today = datetime.now().strftime("%Y-%m-%d")
        out = os.path.join(REPO_ROOT, "output", "briefs", f"brief_{args.config}_{today}.md")

    generate_brief(config=args.config, days=args.days, min_score=args.min_score, out_path=out)
