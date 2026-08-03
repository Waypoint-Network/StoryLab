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
    """Fallback ladder -- used only for categories with no flywheel-group
    mapping in CATEGORY_GROUPS (e.g. a stray 'email-newsletter' feed).
    Categories that do map to a flywheel group are scored from the
    editable scoring_criteria DB table instead -- see core/scorer.py and
    SEED_CRITERIA below."""
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


# One-time seed for the scoring_criteria DB table (see core/scorer.py),
# splitting the flat ladder above into independent per-flywheel-group
# criteria. Only used the first time the table is empty for this config --
# after that, edits happen through the dashboard's Scoring Criteria panel,
# not this file. Treat this as a starting point, not a fixed rubric: the
# groupings below are a best-effort split by topic, not a precise migration.
# Each tuple is (flywheel_group, score_level, keyword). Level 1 has no
# keywords -- it's the automatic fallback when nothing else matches.
SEED_CRITERIA = [
    # Institutional (nil_case_study)
    ("Institutional", 5, "nil deal"),
    ("Institutional", 5, "nil collective"),
    ("Institutional", 5, "nil ambassador"),
    ("Institutional", 5, "name image likeness"),
    ("Institutional", 5, "creator partnership case"),
    ("Institutional", 5, "ambassador program"),
    ("Institutional", 2, "nil"),

    # Mobilizer (influencer_marketing, community_building)
    ("Mobilizer", 4, "influencer marketing"),
    ("Mobilizer", 4, "micro-influencer"),
    ("Mobilizer", 4, "brand deal"),
    ("Mobilizer", 4, "sponsored content"),
    ("Mobilizer", 4, "disclosure"),
    ("Mobilizer", 4, "engagement rate"),
    ("Mobilizer", 4, "ugc"),
    ("Mobilizer", 4, "user-generated content"),
    ("Mobilizer", 4, "mobilizer"),
    ("Mobilizer", 4, "organizer"),
    ("Mobilizer", 4, "grassroots"),
    ("Mobilizer", 4, "movement organizing"),
    ("Mobilizer", 4, "field director"),
    ("Mobilizer", 2, "instagram"),
    ("Mobilizer", 2, "tiktok"),
    ("Mobilizer", 2, "youtube"),
    ("Mobilizer", 2, "social media"),

    # Product (creator_economy)
    ("Product", 3, "creator economy"),
    ("Product", 3, "monetization"),
    ("Product", 3, "personal brand"),
    ("Product", 3, "subscriber growth"),
    ("Product", 3, "newsletter growth"),
    ("Product", 3, "creator fund"),
    ("Product", 3, "creator tools"),
    ("Product", 3, "social commerce"),
    ("Product", 3, "shoppable"),
    ("Product", 3, "affiliate link"),
    ("Product", 3, "platform update"),
    ("Product", 3, "feed ranking"),
    ("Product", 2, "creator"),

    # Fan Graph (fandom_identity)
    ("Fan Graph", 4, "fan identity"),
    ("Fan Graph", 4, "parasocial"),
    ("Fan Graph", 4, "fandom psychology"),
    ("Fan Graph", 4, "tribal identity"),
    ("Fan Graph", 4, "sense of belonging"),
    ("Fan Graph", 4, "fan loyalty"),
    ("Fan Graph", 2, "community"),
    ("Fan Graph", 2, "fandom"),
    ("Fan Graph", 2, "fans"),
    ("Fan Graph", 2, "audience"),
]
