"""
configs/fan_atlas_insiders/__init__.py

See configs/travel_tech_ux/__init__.py for why this exists.
"""

DISPLAY_NAME = "Fan Atlas Insiders"

CLOSING_LINE = (
    "- **Insider craft close:** [what this means for how Loyalty Lab "
    "trains and mobilizes Fan Atlas Insiders -- the technique to adopt, "
    "not just the trend to note]"
)

# Optional: groups feeds.py's raw category values into Waypoint flywheel
# map labels for dashboard display. Read by core/server.py; core/dashboard.html
# falls back to raw per-category tabs when a config doesn't define this.
CATEGORY_GROUPS = {
    "nil_case_study":       "Institutional",
    "influencer_marketing": "Mobilizer",
    "community_building":   "Mobilizer",
    "creator_economy":      "Product",
    "fandom_identity":      "Fan Graph",
}

# The durable editorial homes for the Fan Atlas flywheel. The source
# categories above remain the data model; these descriptions make the
# intelligence briefs useful without changing stored article categories.
FLYWHEEL_BRIEFS = {
    "Institutional": {
        "slug": "institutional",
        "eyebrow": "School systems and NIL operations",
        "description": "Named school, NIL, and ambassador-program mechanics that reveal how institutions are organizing the work.",
        "suggested_question": "Which institutional practice in these sources is concrete enough to validate with a school or NIL partner before adapting it?",
    },
    "Mobilizer": {
        "slug": "mobilizer",
        "eyebrow": "Insider activation and community craft",
        "description": "Practical ways people organize, equip, and activate trusted voices inside a fan community.",
        "suggested_question": "Which activation mechanic is specific enough to test with a small Insider cohort, and what behavior would show that it worked?",
    },
    "Product": {
        "slug": "product",
        "eyebrow": "Tools and product mechanics",
        "description": "Capabilities, platforms, and creator-economy mechanics that may improve the Fan Atlas experience.",
        "suggested_question": "Does any described product mechanic solve a verified Fan Atlas need well enough to research, prototype, or deliberately rule out?",
    },
    "Fan Graph": {
        "slug": "fan-graph",
        "eyebrow": "Fandom behavior and relationship signals",
        "description": "Evidence about identity, belonging, influence, and the relationships that move fan behavior.",
        "suggested_question": "Which relationship or identity mechanism is worth validating against Fan Atlas behavior before designing an experiment around it?",
    },
}
