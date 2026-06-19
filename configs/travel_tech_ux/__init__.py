"""
configs/travel_tech_ux/__init__.py

DISPLAY_NAME and CLOSING_LINE are read by core/brief_generator.py and
core/server.py so the engine doesn't have to hardcode company names per
config (previously a binary `if config == "waypoint"` check -- broken
once a third config existed). Every config exposes these two; see
configs/longitude/__init__.py for the sibling pattern.
"""

DISPLAY_NAME = "Travel Tech BI"

CLOSING_LINE = (
    "- **Competitive read close:** [what this means for Waypoint's own "
    "platform roadmap -- where we're ahead, where we're behind, what to "
    "watch]"
)
