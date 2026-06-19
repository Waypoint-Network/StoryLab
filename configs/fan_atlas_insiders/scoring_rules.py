"""
configs/fan_atlas_insiders/scoring_rules.py — Fan Atlas Insiders Relevance Scoring
--------------------------------------------------------------------------------------
Relevance rubric for Loyalty Lab's Insider training audience -- the six
influencer categories (outside individuals, outside platformers, outside
celebrities, inside athletes/NIL, inside official reps, inside corporate
sponsor/donor management), not AD/CMO pitching. Keyword sets carry over
the vocabulary already built and tested in the standalone bi/ engine's
scoring.py this session.

Score  Signal
-----  ------
  5    A concrete, named NIL deal or creator/community case study with
       real numbers or outcome -- not just commentary on the trend
  4    Influencer marketing mechanics (disclosure, engagement rate, brand
       deal structure), community-organizing technique, fandom psychology
       with a specific mechanism
  3    General creator-economy or social-commerce trend coverage without
       a clear Insider-craft takeaway
  2    Adjacent industry with loose relevance to creator/community work
  1    Generic social media or marketing content with no creator-economy
       or fandom angle
"""

_SCORE_5_KEYWORDS = [
    "nil deal", "nil collective", "nil ambassador", "name image likeness",
    "ambassador program", "creator fund", "creator partnership case",
]

_SCORE_4_KEYWORDS = [
    "influencer marketing", "micro-influencer", "brand deal",
    "sponsored content", "disclosure", "engagement rate",
    "ugc", "user-generated content",
    "ambassador program", "mobilizer", "organizer", "grassroots",
    "movement organizing", "field director",
    "fan identity", "parasocial", "fandom psychology", "tribal identity",
    "sense of belonging", "fan loyalty",
]

_SCORE_3_KEYWORDS = [
    "creator economy", "monetization", "personal brand",
    "subscriber growth", "newsletter growth", "creator fund", "creator tools",
    "social commerce", "shoppable", "affiliate link", "platform update",
    "feed ranking",
]

_SCORE_2_KEYWORDS = [
    "social media", "instagram", "tiktok", "youtube", "creator",
    "community", "fandom", "fans", "audience",
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
