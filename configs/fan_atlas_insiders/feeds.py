"""
configs/fan_atlas_insiders/feeds.py — Fan Atlas Insiders Feed Registry
---------------------------------------------------------------------------
Covers creator economy, influencer marketing, NIL case studies, community
building, and fandom psychology -- the craft material for Loyalty Lab's
Insider training, not AD/CMO pitching. Categories map to four dashboard
tabs via CATEGORY_GROUPS in __init__.py: Institutional, Mobilizer,
Product, Fan Graph.

Categories: creator_economy | influencer_marketing | nil_case_study |
            community_building | fandom_identity

RSS Research Status (verified August 2026):
  ✅ = confirmed live feed, returning items
  ❌ = no RSS -- see NO_RSS_SOURCES below
  ⚠️  = live content but currently broken (parser or transport issue) --
       see NO_RSS_SOURCES for root cause; fixes deferred deliberately,
       handled separately since they'd touch shared core/aggregator.py

creator_economy below is reused from travel_tech_ux's verified
travel/booking-tech pool per explicit instruction, as a placeholder to
get the pipeline flowing -- expect low relevance scores against this
config's creator-economy rubric until pruned or replaced with real
creator-economy sources.

community_building has no verified feed yet -- Circle's blog (the one
candidate identified) has no discoverable RSS; see NO_RSS_SOURCES.
"""

# Each entry: (label, rss_url, category, notes)
FEEDS = [
    # ── NIL Case Study (-> Institutional) ────────────────────────────────────
    ("On3 (NIL)", "https://www.on3.com/nil/feed/", "nil_case_study",
     "✅ Verified Aug 2026 -- genuinely NIL-specific content, confirmed distinct "
     "from the general On3 feed (not a silent redirect)"),
    ("Sportico", "https://www.sportico.com/feed/", "nil_case_study",
     "✅ Verified Aug 2026 -- WordPress RSS"),

    # ── Influencer Marketing (-> Mobilizer) ──────────────────────────────────
    ("Later", "https://later.com/rss.xml", "influencer_marketing",
     "✅ Verified Aug 2026 -- real feed is /rss.xml, not /blog/feed/ (404) as "
     "originally guessed"),
    ("Influencer Marketing Hub", "https://influencermarketinghub.com/feed/", "influencer_marketing",
     "✅ Verified Aug 2026 -- WordPress RSS"),
    ("Social Media Examiner", "https://www.socialmediaexaminer.com/feed/", "influencer_marketing",
     "✅ Verified Aug 2026 -- reused from travel_tech_ux"),

    # ── Community Building (-> Mobilizer) ────────────────────────────────────
    # No working feed identified yet. Circle (circle.so) blog was the one
    # candidate tried -- no RSS found, see NO_RSS_SOURCES below. Add real
    # organizing/community-building sources here once identified.

    # ── Creator Economy (-> Product) ─────────────────────────────────────────
    # Reused from travel_tech_ux's verified pool per explicit instruction --
    # placeholder signal, not a topical fit. Expect pruning.
    ("Skift", "https://skift.com/feed/", "creator_economy",
     "✅ Verified Aug 2026 -- reused from travel_tech_ux"),
    ("HSMAI Insights", "https://americas.hsmai.org/feed/", "creator_economy",
     "✅ Verified Aug 2026 -- reused from travel_tech_ux"),
    ("Breaking Travel News", "https://feeds.feedburner.com/breakingtravelnews", "creator_economy",
     "✅ Verified Aug 2026 -- reused from travel_tech_ux"),
    ("Northstar Travel Today", "https://kill-the-newsletter.com/feeds/w4q2xpme11o1mtdtpm97.xml", "creator_economy",
     "✅ Verified Aug 2026 -- Kill the Newsletter, reused from travel_tech_ux"),

    # ── Fandom Identity (-> Fan Graph) ────────────────────────────────────────
    ("Boardroom", "https://boardroom.tv/feed/", "fandom_identity",
     "✅ Verified Aug 2026 -- athlete brand/culture angle, reused from travel_tech_ux"),
    ("SportsPro", "https://www.sportspromedia.com/feed/", "fandom_identity",
     "✅ Verified Aug 2026 -- reused from travel_tech_ux"),
]


NO_RSS_SOURCES = [
    # ── Live content, feed currently broken -- fixes deferred deliberately ──
    {
        "name": "Front Office Sports",
        "website": "https://frontofficesports.com/",
        "platform": "WordPress",
        "workaround": "None yet. Feed at /feed/ returns current, real content, "
                      "but its XML is malformed -- a <media:thumbnail> element "
                      "uses an undeclared namespace prefix. Needs a parser "
                      "tolerance fix in core/aggregator.py (shared code) -- "
                      "deferred, to be handled separately and deliberately.",
        "generated_feed": "",
        "notes": "⚠️ Verified Aug 2026. Same URL travel_tech_ux uses for this "
                 "source -- may currently be broken there too.",
    },
    {
        "name": "SportTechie",
        "website": "https://www.sporttechie.com/",
        "platform": "WordPress",
        "workaround": "None yet. Feed at /feed/ is reachable -- manually "
                      "confirmed real content comes back -- but the site's TLS "
                      "cert has expired. core/aggregator.py's existing cert-"
                      "expiry fallback doesn't trigger because urllib wraps "
                      "the SSL error in URLError rather than raising "
                      "ssl.SSLCertVerificationError directly. Needs a small "
                      "aggregator.py fix -- deferred, to be handled separately "
                      "and deliberately.",
        "generated_feed": "",
        "notes": "⚠️ Verified Aug 2026.",
    },

    # ── No feed found ─────────────────────────────────────────────────────────
    {
        "name": "Circle (circle.so) blog",
        "website": "https://circle.so/blog",
        "platform": "Unknown -- no RSS autodiscovery tag in page HTML",
        "workaround": "None found. Tried /blog/rss, /blog/feed, /blog/rss.xml, "
                      "/feed/, /atom.xml, /blog.rss -- all 404. No <link "
                      "rel=\"alternate\"> RSS/Atom tag present on the blog page "
                      "either.",
        "generated_feed": "",
        "notes": "❌ Verified Aug 2026. Likely no RSS feed exists for this "
                 "property.",
    },

    # ── Hard blocked / down ───────────────────────────────────────────────────
    {
        "name": "PhocusWire (rss.app proxy)",
        "website": "https://www.phocuswire.com/",
        "platform": "rss.app proxy",
        "workaround": "Same proxy travel_tech_ux uses -- currently returning "
                      "402 Payment Required (rss.app tier issue on their end, "
                      "not a URL problem).",
        "generated_feed": "https://rss.app/feeds/T0AxO1lznu3cLDk1.xml",
        "notes": "❌ Verified Aug 2026: currently down. May also be down for "
                 "travel_tech_ux right now.",
    },
]
