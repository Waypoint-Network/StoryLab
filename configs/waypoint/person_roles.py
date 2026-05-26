"""
configs/waypoint/person_roles.py — Waypoint Person-Role Definitions
--------------------------------------------------------------------
Used by brief_generator.py to route story briefs to the right audience.
"""

PERSON_ROLES = [
    {
        "name": "AD Marketing Director",
        "description": (
            "Athletic department CMO or marketing director at a P4 university. "
            "Responsible for fan acquisition, retention, email/CRM, and revenue programs. "
            "Skeptical of vendor pitches. Trusts peer case studies with real numbers. "
            "Decision-maker on travel programs, loyalty platforms, and fan engagement tech."
        ),
        "revenue_priorities": ["tickets", "travel", "sponsorship", "NIL"],
        "segments_they_care_about": ["alumni", "season ticket holders", "students", "donors"],
        "pain_points": [
            "Proving ROI of marketing spend to AD leadership",
            "Moving fans from awareness to travel booking",
            "Competing with pro sports for fan wallet share",
            "CRM/ESP integrations that don't talk to ticketing systems",
        ],
    },
    {
        "name": "College Fan",
        "description": (
            "Alumni or passionate fan of a P4 university. Plans away-game trips. "
            "Season ticket holder or aspiring member. Engages with school content on social. "
            "Motivated by school pride, shared experience, and access to exclusive moments."
        ),
        "revenue_priorities": ["travel booking", "membership", "merchandise"],
        "segments_they_care_about": ["alumni", "fans", "students"],
        "pain_points": [
            "Finding affordable away-game travel packages",
            "Feeling connected to the program between games",
            "Access to behind-the-scenes moments",
        ],
    },
    {
        "name": "Athletic Department CMO",
        "description": (
            "Senior marketing leader overseeing the full AD revenue and brand strategy. "
            "Reports to the Athletic Director. Owns the Waypoint partnership relationship. "
            "Focused on institutional revenue, donor relations, and program reputation."
        ),
        "revenue_priorities": ["tickets", "donations", "sponsorship", "travel"],
        "segments_they_care_about": ["donors", "alumni", "season ticket holders"],
        "pain_points": [
            "Justifying new revenue programs to the AD",
            "Coordinating across ticketing, development, and marketing teams",
            "Demonstrating measurable fan loyalty outcomes",
        ],
    },
]
