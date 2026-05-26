"""
configs/waypoint/scoring_rules.py — Waypoint Relevance Scoring (Crowd Commerce)
---------------------------------------------------------------------------------
Relevance rubric for the AD marketing director audience at P4 universities.

Score  Signal
-----  ------
  5    Fan revenue programs with real numbers; travel behavior data; peer AD case
       studies; NIL commerce; loyalty technology adoption in college sports
  4    Athletic department revenue strategy; fan engagement tech; conference or
       school-specific data; NACDA/NACMA sourced
  3    General hospitality or travel industry news; sports business without specific
       AD angle; marketing technology without college sports application
  2    Adjacent industry with loose relevance; interesting but no clear AD implication
  1    Generic marketing, general business, or travel content with no college sports angle
"""

# Keywords tuned to the AD marketing director / Crowd Commerce audience.
# Checked against title + summary (lowercased). First matching tier wins.

_SCORE_5_KEYWORDS = [
    "fan revenue", "travel booking", "travel behavior", "booking revenue",
    "away game travel", "away-game travel", "fan travel",
    "nil commerce", "nil deal", "nil revenue",
    "loyalty technology", "loyalty platform", "loyalty program", "fan loyalty",
    "athletic department revenue", "ad revenue", "season ticket revenue",
    "peer athletic", "case study", "real numbers", "real data",
    "college fan", "college athletics marketing", "nacma",
    "ticket revenue", "seat upgrade", "premium seating",
]

_SCORE_4_KEYWORDS = [
    "athletic department", "athletics department",
    "fan engagement", "fan experience",
    "nacda", "nacma",
    "college athletics", "collegiate athletics",
    "conference", "power four", "power five", "p4 ",
    "university revenue", "university partnership",
    "nil ", "name image likeness",
    "sports sponsorship", "sponsorship revenue",
    "stadium tech", "arena tech", "venue tech",
    "ticketing platform", "ticketing technology",
    "crm ", "marketing automation",
]

_SCORE_3_KEYWORDS = [
    "hospitality", "hotel", "travel industry", "tourism",
    "sports business", "sports marketing", "sports media",
    "marketing technology", "martech", "marketing platform",
    "email marketing", "social media marketing",
    "content marketing", "brand strategy",
    "sports tech", "sporttechie",
]

_SCORE_2_KEYWORDS = [
    "marketing", "digital marketing", "advertising",
    "audience", "engagement", "loyalty",
    "travel", "airline", "cruise", "resort",
    "sports", "athlete", "team",
]


def score(title: str, summary: str, category: str) -> int:
    text = (title + " " + (summary or "")).lower()

    if any(kw in text for kw in _SCORE_5_KEYWORDS):
        return 5
    if any(kw in text for kw in _SCORE_4_KEYWORDS):
        return 4
    if any(kw in text for kw in _SCORE_3_KEYWORDS):
        return 3
    if any(kw in text for kw in _SCORE_2_KEYWORDS):
        return 2
    return 1
