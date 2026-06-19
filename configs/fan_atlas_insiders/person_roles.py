"""
configs/fan_atlas_insiders/person_roles.py — Fan Atlas Insiders Person-Role Definitions
--------------------------------------------------------------------------------------------
Used by brief_generator.py to route story briefs to the right audience.
"""

PERSON_ROLES = [
    {
        "name": "Loyalty Lab Staffer",
        "description": (
            "Waypoint's internal team executing Insider mobilization on "
            "behalf of school marketing teams who lack the bandwidth or "
            "expertise to act on Fan Atlas-level intelligence themselves. "
            "Needs current creator-economy and community-organizing craft "
            "to do that execution well."
        ),
        "priorities": ["mobilization technique", "creator partnership craft"],
        "watch_for": [
            "A named NIL or creator deal with real terms worth modeling",
            "A community-organizing technique transferable to Insider work",
        ],
    },
    {
        "name": "Fan Atlas Insider",
        "description": (
            "One of the six influencer categories the Fan Atlas mobilizes: "
            "outside individuals, outside platformers, outside celebrities, "
            "inside athletes/NIL, inside official reps, inside corporate "
            "sponsor/donor management. A leader of an existing micro-movement "
            "being federated, not recruited as an ambassador."
        ),
        "priorities": ["authentic voice", "compounding relationship value"],
        "watch_for": [
            "Platform changes affecting how they reach their own audience",
            "Peer examples of NIL/creator monetization done well",
        ],
    },
]
