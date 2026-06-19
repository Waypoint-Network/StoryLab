"""
configs/fan_atlas_insiders/feeds.py — Fan Atlas Insiders Feed Registry
---------------------------------------------------------------------------
Covers creator economy, influencer marketing, NIL case studies, community
building, and fandom psychology -- the craft material for Loyalty Lab's
Insider training, not AD/CMO pitching. This is genuinely new territory:
Crowd Commerce never covered it, so unlike travel_tech_ux there's no
verified feed list to carry over.

Categories: creator_economy | influencer_marketing | nil_case_study |
            community_building | fandom_identity

All feeds below are placeholders -- verify RSS URLs before activating.
Same convention as configs/longitude/feeds.py. Expanding this list with
the specific creator-economy newsletters and podcasts Insiders already
follow will produce a better source list than guessing further from here.
"""

FEEDS = [
    # ── NIL Case Study ───────────────────────────────────────────────────────
    # ("On3 (NIL)",         "https://www.on3.com/nil/feed/",        "nil_case_study",      "Pending verification"),

    # ── Influencer Marketing ────────────────────────────────────────────────
    # ("Later (creator/social commerce craft)", "https://later.com/blog/feed/", "influencer_marketing", "Pending verification"),
    # ("Hootsuite (creator/social trends)",     "https://blog.hootsuite.com/feed/", "influencer_marketing", "Pending verification"),

    # ── Fandom Identity ─────────────────────────────────────────────────────
    # ("SportTechie (fandom/engagement angle)", "https://www.sporttechie.com/feed", "fandom_identity", "Pending verification — note: also used by travel_tech_ux under sports_fan_specific"),

    # ── Creator Economy ─────────────────────────────────────────────────────
    # Add creator-economy newsletters/podcasts here once identified:
    # ("Publication Name", "https://example.com/feed/", "creator_economy", "notes"),

    # ── Community Building ──────────────────────────────────────────────────
    # Add organizing/community-building sources here once identified
    # (Marshall Ganz / Hahrie Han adjacent material is more likely books and
    # papers than RSS feeds -- this category may end up curated manually
    # rather than fed by RSS at all):
    # ("Publication Name", "https://example.com/feed/", "community_building", "notes"),
]

NO_RSS_SOURCES = [
    # Add email-only or blocked sources here following the same pattern as
    # travel_tech_ux/feeds.py once real candidates are identified.
]
