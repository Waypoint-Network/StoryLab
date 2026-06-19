"""
configs/travel_tech_ux/scoring_rules.py — Travel Tech BI Relevance Scoring
------------------------------------------------------------------------------
Relevance rubric for Waypoint's own product/platform team -- competitive
and capability intelligence, not AD/CMO pitching. Replaces the Crowd
Commerce rubric (configs/waypoint/scoring_rules.py, retired). The keyword
sets below carry over the category vocabulary already built and tested
in the standalone bi/ engine's scoring.py this session, reshaped into
StoryLab's 1-5 tier format.

Score  Signal
-----  ------
  5    A named competitor or platform shipping a concrete capability (AI
       agent booking, dynamic pricing, real-time personalization) with
       specific detail -- not just a trend piece about the category
  4    OTA/booking UX changes (checkout, conversion funnel), loyalty
       program design news, fan-loyalty tech adoption in sports
  3    General travel/hospitality industry research, sports-business news
       without a clear product/UX angle, general martech without a
       travel or fan-commerce application
  2    Adjacent industry with loose relevance; interesting but no clear
       product implication for Waypoint
  1    Generic marketing or business content with no travel, booking, or
       fan-commerce angle
"""

_SCORE_5_KEYWORDS = [
    "ai agent", "agentic ai", "generative ai booking", "conversational booking",
    "dynamic pricing", "real-time pricing", "personalization engine",
    "voice search booking", "headless commerce", "api-first booking",
    "launches ai", "ships ai", "rolls out ai",
]

_SCORE_4_KEYWORDS = [
    "checkout", "conversion rate", "abandoned cart", "cart abandonment",
    "booking flow", "search funnel", "onboarding flow", "drop-off",
    "extranet", "partner hub", "white label",
    "loyalty program", "loyalty tier", "points program", "loyalty platform",
    "rebooking", "retention", "lifetime value", "gamification",
    "fan engagement tech", "fan loyalty", "venue tech", "stadium tech",
    "nil commerce", "nil deal",
]

_SCORE_3_KEYWORDS = [
    "market size", "demand forecast", "travel forecast", "consumer survey",
    "benchmark report", "industry report", "travel spend", "booking trends",
    "hospitality", "tourism", "sports business", "sports marketing",
    "marketing technology", "martech", "marketing automation",
    "social commerce", "shoppable", "creator partnership", "affiliate link",
]

_SCORE_2_KEYWORDS = [
    "travel", "airline", "cruise", "resort", "hotel",
    "marketing", "advertising", "engagement", "loyalty",
    "sports", "athlete", "team", "fan",
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
