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
