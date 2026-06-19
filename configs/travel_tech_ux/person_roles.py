"""
configs/travel_tech_ux/person_roles.py — Travel Tech BI Person-Role Definitions
---------------------------------------------------------------------------------
Used by brief_generator.py to route story briefs to the right audience.
This branch's audience is internal, not external -- the readers are
Waypoint's own product/platform people, not AD marketing directors.
"""

PERSON_ROLES = [
    {
        "name": "Waypoint Product/Platform Lead",
        "description": (
            "Owns Waypoint's own booking platform, UX, and technical roadmap. "
            "Wants to know what competitors and adjacent OTAs are shipping, "
            "which loyalty-tech and personalization patterns are gaining "
            "traction, and where Waypoint's own conversion funnel might be "
            "falling behind or ahead of category norms."
        ),
        "priorities": ["platform roadmap", "UX benchmarking", "loyalty tech"],
        "watch_for": [
            "Competitor UX/checkout changes worth matching or avoiding",
            "Loyalty program mechanics worth adapting",
            "Emerging AI/agentic booking capability before it's table stakes",
        ],
    },
    {
        "name": "Waypoint Founder/Strategy",
        "description": (
            "Tracks the competitive and category landscape at a higher level -- "
            "less interested in implementation detail, more interested in "
            "where the travel-tech and fan-commerce category is heading and "
            "whether Waypoint's positioning still holds."
        ),
        "priorities": ["category trends", "competitive positioning"],
        "watch_for": [
            "Market-size or demand-forecast data relevant to fan travel",
            "A competitor entering the college-sports travel space directly",
        ],
    },
]
