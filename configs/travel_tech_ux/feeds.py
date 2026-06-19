"""
configs/travel_tech_ux/feeds.py — Travel Tech BI Feed Registry
-----------------------------------------------------------------
Transitioned from configs/waypoint/feeds.py (Crowd Commerce). The verified
feed URLs below are carried over unchanged -- that RSS research (proxy
workarounds, Kill the Newsletter conversions, dead-feed notes) is real,
tested work and applies just as well to an internal audience as it did
to the AD/CMO one. Only the category assignments changed, to match this
branch's own categories (see scoring_rules.py).

Categories: ota_ux_conversion | industry_research | next_gen_capability |
            loyalty_retention | social_commerce_campaign | sports_fan_specific

RSS Research Status (carried over from Crowd Commerce, May 2026):
  ✅ = confirmed live feed
  ❌ = no RSS — see NO_RSS_SOURCES below for workarounds
  ⚠️  = paywalled or requires subscription
  🚫 = hard-blocked (Cloudflare/IP block) — moved to NO_RSS_SOURCES

ota_ux_conversion and loyalty_retention have no verified feeds yet --
none of Crowd Commerce's sources covered OTA checkout/conversion UX or
loyalty-tech trade press specifically. Candidates below are commented out
pending verification, same convention as configs/longitude/feeds.py.
"""

# Each entry: (label, rss_url, category, notes)
FEEDS = [
    # ── Industry Research ─────────────────────────────────────────────────────
    ("Skift",              "https://skift.com/feed/",                           "industry_research", "✅ WordPress RSS"),
    ("PhocusWire",         "https://rss.app/feeds/T0AxO1lznu3cLDk1.xml",       "industry_research", "✅ rss.app proxy — PhocusWire blocked direct RSS (403)"),
    ("HSMAI Insights",     "https://americas.hsmai.org/feed/",                  "industry_research", "✅ WordPress RSS — hospitality sales/marketing"),
    ("Northstar Travel Today", "https://kill-the-newsletter.com/feeds/w4q2xpme11o1mtdtpm97.xml", "industry_research", "✅ Kill the Newsletter — daily travel industry email"),
    ("Breaking Travel News", "https://feeds.feedburner.com/breakingtravelnews", "industry_research", "✅ Feedburner RSS — daily travel industry news"),

    # ── Sports / Fan Specific ─────────────────────────────────────────────────
    ("Front Office Sports","https://frontofficesports.com/feed/",               "sports_fan_specific", "✅ WordPress RSS"),
    ("SportsPro",          "https://www.sportspromedia.com/feed/",              "sports_fan_specific", "✅ Confirmed"),
    ("Sportico",           "https://www.sportico.com/feed/",                    "sports_fan_specific", "✅ WordPress RSS"),
    ("Boardroom",          "https://boardroom.tv/feed/",                        "sports_fan_specific", "✅ WordPress RSS — sports & entertainment business"),
    ("SportTechie",        "https://www.sporttechie.com/feed/",                 "sports_fan_specific", "✅ WordPress RSS — sports tech, fan experience, team ops"),

    # ── Social Commerce / Campaign Timing ─────────────────────────────────────
    ("Marketing Brew",     "https://kill-the-newsletter.com/feeds/w89wfs89ooxgknow5jbp.xml", "social_commerce_campaign", "✅ Kill the Newsletter — daily email newsletter"),
    ("Litmus Blog",        "https://www.litmus.com/blog/feed/",                 "social_commerce_campaign", "✅ WordPress RSS — email workflow/design"),
    ("Social Media Examiner", "https://www.socialmediaexaminer.com/feed/",      "social_commerce_campaign", "✅ WordPress RSS — social media tactics, platform updates"),
    ("Content Marketing Institute", "https://contentmarketinginstitute.com/feed/", "social_commerce_campaign", "✅ WordPress RSS — content strategy, brand storytelling"),
    ("Sprout Social Insights", "https://sproutsocial.com/insights/feed/",       "social_commerce_campaign", "✅ WordPress RSS — social media management, analytics"),

    # ── Next-Gen Capability ────────────────────────────────────────────────────
    ("HubSpot Marketing Blog", "https://blog.hubspot.com/marketing/rss.xml",    "next_gen_capability", "✅ RSS — marketing automation, martech (high volume)"),
    # Candidates, not yet verified as live RSS:
    # ("Hopper Blog",         "https://www.hopper.com/blog/feed/",              "next_gen_capability",  "Pending verification — dynamic pricing / AI travel agent"),

    # ── OTA UX / Conversion ────────────────────────────────────────────────────
    # No verified feed yet. Partner-hub sites (Booking, Agoda, Expedia) gate
    # real content behind partner auth -- likely needs a different approach
    # than RSS entirely. Add candidates here as they're identified:
    # ("Booking Partner Hub", "https://example.com/feed/", "ota_ux_conversion", "Pending"),

    # ── Loyalty / Retention ─────────────────────────────────────────────────────
    # No verified feed yet. Candidates, not yet verified:
    # ("The Wise Marketer",   "https://thewisemarketer.com/feed/",              "loyalty_retention", "Pending verification"),
    # ("Loyalty Lobby",       "https://loyaltylobby.com/feed/",                 "loyalty_retention", "Pending verification"),
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
        "notes": "❌ /nil/news/feed/ returns 404. Use rss.app. Relevant here for fan-loyalty-tech/NIL-commerce signal, not just AD pitching.",
    },

    # ── Hard blocked ──────────────────────────────────────────────────────────
    {
        "name": "PhocusWire",
        "website": "https://www.phocuswire.com/",
        "platform": "Custom CMS",
        "workaround": "rss.app — generate a feed from https://www.phocuswire.com/news",
        "generated_feed": "https://rss.app/feeds/T0AxO1lznu3cLDk1.xml",
        "notes": "✅ RESOLVED April 2026 — using rss.app proxy. Already active above.",
    },

    # ── Email-only newsletters ─────────────────────────────────────────────────
    {
        "name": "Marketing Brew",
        "website": "https://www.marketingbrew.com/",
        "platform": "Morning Brew custom platform",
        "workaround": "Kill the Newsletter",
        "kill_the_newsletter_feed": "https://kill-the-newsletter.com/feeds/w89wfs89ooxgknow5jbp.xml",
        "notes": "✅ RESOLVED April 2026. Already active above.",
    },
    {
        "name": "Northstar Travel Today",
        "website": "https://www.northstartravelgroup.com/",
        "platform": "Omeda email platform",
        "workaround": "Kill the Newsletter",
        "kill_the_newsletter_feed": "https://kill-the-newsletter.com/feeds/w4q2xpme11o1mtdtpm97.xml",
        "notes": "✅ RESOLVED April 2026. Already active above.",
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
