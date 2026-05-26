"""
configs/waypoint/feeds.py — Waypoint Feed Registry (Crowd Commerce)
--------------------------------------------------------------------
Categories: travel | sports-biz | college-athletics | marketing | ad-revenue | fan-loyalty

RSS Research Status (May 2026):
  ✅ = confirmed live feed
  ❌ = no RSS — see NO_RSS_SOURCES below for workarounds
  ⚠️  = paywalled or requires subscription
  🚫 = hard-blocked (Cloudflare/IP block) — moved to NO_RSS_SOURCES
"""

# Each entry: (label, rss_url, category, notes)
FEEDS = [
    # ── Travel & Hospitality ──────────────────────────────────────────────────
    ("Skift",              "https://skift.com/feed/",                           "travel",            "✅ WordPress RSS"),
    ("PhocusWire",         "https://rss.app/feeds/T0AxO1lznu3cLDk1.xml",       "travel",            "✅ rss.app proxy — PhocusWire blocked direct RSS (403)"),
    ("HSMAI Insights",     "https://americas.hsmai.org/feed/",                  "travel",            "✅ WordPress RSS — hospitality sales/marketing"),
    ("Northstar Travel Today", "https://kill-the-newsletter.com/feeds/w4q2xpme11o1mtdtpm97.xml", "travel", "✅ Kill the Newsletter — daily travel industry email"),
    ("Breaking Travel News", "https://feeds.feedburner.com/breakingtravelnews", "travel",            "✅ Feedburner RSS — daily travel industry news"),

    # ── Sports Business ───────────────────────────────────────────────────────
    ("Front Office Sports","https://frontofficesports.com/feed/",               "sports-biz",        "✅ WordPress RSS"),
    ("SportsPro",          "https://www.sportspromedia.com/feed/",              "sports-biz",        "✅ Confirmed"),
    ("Sportico",           "https://www.sportico.com/feed/",                    "sports-biz",        "✅ WordPress RSS"),
    ("Boardroom",          "https://boardroom.tv/feed/",                        "sports-biz",        "✅ WordPress RSS — sports & entertainment business"),
    ("SportTechie",        "https://www.sporttechie.com/feed/",                 "sports-biz",        "✅ WordPress RSS — sports tech, fan experience, team ops"),

    # ── College Athletics ─────────────────────────────────────────────────────
    ("D1.ticker",          "https://www.d1ticker.com/feed/",                    "college-athletics", "✅ WordPress RSS"),
    ("Business of College Sports", "https://businessofcollegesports.com/feed/","college-athletics", "✅ WordPress RSS"),
    ("CollegeAD",          "https://collegead.com/feed/",                       "college-athletics", "✅ WordPress RSS"),
    ("NACDA News",         "https://nacda.com/rss",                             "college-athletics", "✅ Confirmed live — corrected URL April 2026"),
    ("Athletic Director U","https://athleticdirectoru.com/feed/",               "college-athletics", "✅ WordPress RSS — leadership, strategy & ops content for ADs"),
    ("NACMA Podcast",      "https://anchor.fm/s/36cd0a60/podcast/rss",          "college-athletics", "✅ Spotify/Anchor RSS — NACMA collegiate marketing podcast"),

    # ── Marketing / Commerce / Growth ─────────────────────────────────────────
    ("Marketing Brew",     "https://kill-the-newsletter.com/feeds/w89wfs89ooxgknow5jbp.xml", "marketing", "✅ Kill the Newsletter — daily email newsletter"),
    ("Litmus Blog",        "https://www.litmus.com/blog/feed/",                 "marketing",         "✅ WordPress RSS — email workflow/design"),
    ("Social Media Examiner", "https://www.socialmediaexaminer.com/feed/",      "marketing",         "✅ WordPress RSS — social media tactics, platform updates"),
    ("Content Marketing Institute", "https://contentmarketinginstitute.com/feed/", "marketing",      "✅ WordPress RSS — content strategy, brand storytelling"),
    ("HubSpot Marketing Blog", "https://blog.hubspot.com/marketing/rss.xml",    "marketing",         "✅ RSS — marketing strategy, email, social, automation (high volume)"),
    ("Sprout Social Insights", "https://sproutsocial.com/insights/feed/",       "marketing",         "✅ WordPress RSS — social media management, analytics"),

    # ── Athletic Department Revenue ───────────────────────────────────────────
    # Add ad-revenue feeds here as they are identified:
    # ("Publication Name", "https://example.com/feed/", "ad-revenue", "notes"),

    # ── Fan Loyalty & Engagement ──────────────────────────────────────────────
    # Add fan-loyalty feeds here as they are identified:
    # ("Publication Name", "https://example.com/feed/", "fan-loyalty", "notes"),
]


NO_RSS_SOURCES = [
    # ── Dead/broken URLs as of April 2026 ────────────────────────────────────
    {
        "name": "Hospitality Net",
        "website": "https://www.hospitalitynet.org/",
        "platform": "Custom CMS",
        "workaround": "rss.app — original URL returned 404. Check https://www.hospitalitynet.org/rss for updated URL.",
        "generated_feed": "",
        "notes": "❌ 404 as of April 2026.",
    },
    {
        "name": "On3 NIL",
        "website": "https://www.on3.com/nil/news/",
        "platform": "Next.js (no standard RSS endpoint)",
        "workaround": "rss.app — generate a feed from https://www.on3.com/nil/news/",
        "generated_feed": "",
        "notes": "❌ /nil/news/feed/ returns 404. Use rss.app.",
    },

    # ── Hard blocked ──────────────────────────────────────────────────────────
    {
        "name": "PhocusWire",
        "website": "https://www.phocuswire.com/",
        "platform": "Custom CMS",
        "workaround": "rss.app — generate a feed from https://www.phocuswire.com/news",
        "generated_feed": "https://rss.app/feeds/T0AxO1lznu3cLDk1.xml",
        "notes": "✅ RESOLVED April 2026 — using rss.app proxy.",
    },

    # ── Email-only newsletters ─────────────────────────────────────────────────
    {
        "name": "Marketing Brew",
        "website": "https://www.marketingbrew.com/",
        "platform": "Morning Brew custom platform",
        "workaround": "Kill the Newsletter",
        "kill_the_newsletter_feed": "https://kill-the-newsletter.com/feeds/w89wfs89ooxgknow5jbp.xml",
        "notes": "✅ RESOLVED April 2026.",
    },
    {
        "name": "Northstar Travel Today",
        "website": "https://www.northstartravelgroup.com/",
        "platform": "Omeda email platform",
        "workaround": "Kill the Newsletter",
        "kill_the_newsletter_feed": "https://kill-the-newsletter.com/feeds/w4q2xpme11o1mtdtpm97.xml",
        "notes": "✅ RESOLVED April 2026.",
    },
    {
        "name": "Extra Points (Matt Brown)",
        "website": "https://www.extrapointsmb.com/",
        "platform": "Beehiiv",
        "workaround": "Kill the Newsletter",
        "kill_the_newsletter_feed": "",
        "notes": "College athletics business newsletter. Beehiiv RSS not enabled.",
    },
    {
        "name": "JohnWallStreet",
        "website": "https://johnwallstreet.com/",
        "platform": "Beehiiv",
        "workaround": "Kill the Newsletter",
        "kill_the_newsletter_feed": "",
        "notes": "Sports business newsletter. Beehiiv RSS not enabled.",
    },
    {
        "name": "No Huddle",
        "website": "https://nohuddle.beehiiv.com/",
        "platform": "Beehiiv",
        "workaround": "Kill the Newsletter",
        "kill_the_newsletter_feed": "",
        "notes": "Sports business meets innovation newsletter. Beehiiv RSS not enabled.",
    },
    {
        "name": "At the Center",
        "website": "https://www.atthecenter.co/",
        "platform": "Birdie.so",
        "workaround": "Kill the Newsletter or rss.app",
        "kill_the_newsletter_feed": "",
        "notes": "Biweekly essay on sports/culture/capital. Birdie.so platform — no /feed/.",
    },
    {
        "name": "Hashtag Sports",
        "website": "https://hashtagsports.com/",
        "platform": "Ghost (RSS suppressed)",
        "workaround": "rss.app",
        "generated_feed": "",
        "notes": "Ghost routing suppresses /rss/. Use rss.app.",
    },
    {
        "name": "Sports Business Journal",
        "website": "https://www.sportsbusinessjournal.com/",
        "platform": "Custom CMS (paywalled)",
        "workaround": "RSS at /RSS-Feeds.aspx — requires paid subscription.",
        "generated_feed": "",
        "notes": "⚠️ Subscription required.",
    },
]
