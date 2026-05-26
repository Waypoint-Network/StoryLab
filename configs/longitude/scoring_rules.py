"""
configs/longitude/scoring_rules.py — Longitude Relevance Scoring
-----------------------------------------------------------------
Relevance rubric for the Wasatch Back real estate audience:
agents, brokers, buyers, and the business owner networks agents serve.

Score  Signal
-----  ------
  5    Wasatch Back/Summit County specific data; agent movement in the market;
       luxury/resort real estate transactions; Park City, Deer Valley specifics
  4    Utah real estate trends; mountain resort market data; comp market moves
       (Aspen, Jackson Hole, Sun Valley, Steamboat); luxury buyer behavior
  3    National luxury real estate trends; agent practice and tech adoption;
       brokerage M&A; buyer/seller rep best practices
  2    General real estate news; mortgage rates; national housing market
  1    Generic business or finance content with no real estate angle
"""

_SCORE_5_KEYWORDS = [
    "park city", "wasatch", "summit county", "wasatch county",
    "deer valley", "canyons", "alta", "snowbird",
    "utah real estate", "utah luxury", "utah mountain",
    "kamas", "heber", "midway utah",
]

_SCORE_4_KEYWORDS = [
    "resort real estate", "mountain real estate", "ski real estate",
    "aspen", "jackson hole", "sun valley", "steamboat springs",
    "luxury real estate", "luxury home", "luxury market",
    "second home", "vacation home", "primary residence luxury",
    "agent movement", "agent joins", "team formation", "brokerage",
    "compass", "sotheby's", "berkshire hathaway", "coldwell banker", "exp realty",
]

_SCORE_3_KEYWORDS = [
    "real estate market", "housing market", "home prices",
    "days on market", "inventory", "median price",
    "buyer demand", "seller market", "real estate technology",
    "agent productivity", "agent marketing", "real estate crm",
    "buyer representation", "seller representation", "commission",
]

_SCORE_2_KEYWORDS = [
    "real estate", "mortgage", "interest rate", "housing",
    "property", "listing", "mls", "realtor", "agent",
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
