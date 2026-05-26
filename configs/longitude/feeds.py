"""
configs/longitude/feeds.py — Longitude Feed Registry
------------------------------------------------------
Covers the Wasatch Back real estate market (Summit and Wasatch Counties, Utah).
Categories: national-brokerage | local-market | agent-intel | industry-practice | market-data | comp-market

All feeds are placeholders — verify RSS URLs before activating.
"""

FEEDS = [
    # ── National Brokerage ────────────────────────────────────────────────────
    # ("Inman News",    "https://www.inman.com/feed/",    "national-brokerage", "Pending verification"),
    # ("RealTrends",    "https://www.realtrends.com/feed/", "national-brokerage", "Pending verification"),
    # ("Compass Blog",  "https://example.com/feed/",      "national-brokerage", "Pending verification"),

    # ── Local Market ─────────────────────────────────────────────────────────
    # ("Park City Board of Realtors", "https://example.com/feed/", "local-market", "Pending"),

    # ── Agent Intelligence ────────────────────────────────────────────────────
    # ("RealScout Blog", "https://example.com/feed/", "agent-intel", "Pending"),

    # ── Industry Practice ─────────────────────────────────────────────────────
    # ("NAR Newsroom",  "https://www.nar.realtor/feed/", "industry-practice", "Pending"),

    # ── Market Data ───────────────────────────────────────────────────────────
    # ("Redfin News",   "https://www.redfin.com/news/feed/", "market-data", "Pending"),
    # ("Zillow Research", "https://www.zillow.com/research/feed/", "market-data", "Pending"),

    # ── Comparable Markets ────────────────────────────────────────────────────
    # ("Aspen Times Business", "https://example.com/feed/", "comp-market", "Pending"),
    # ("Jackson Hole News", "https://example.com/feed/", "comp-market", "Pending"),
]

NO_RSS_SOURCES = [
    # Add email-only or blocked sources here following the same pattern as waypoint/feeds.py
]
