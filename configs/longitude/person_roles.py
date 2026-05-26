"""
configs/longitude/person_roles.py — Longitude Person-Role Definitions
"""

PERSON_ROLES = [
    {
        "name": "Wasatch Back Agent",
        "description": (
            "Residential real estate agent serving Summit and Wasatch Counties, Utah. "
            "Handles luxury and resort property. Motivated by referral network, local "
            "market knowledge, and relationship-first sales. Skeptical of tech that "
            "doesn't integrate with their workflow."
        ),
        "revenue_priorities": ["listings", "buyer relationships", "referrals"],
        "pain_points": [
            "Staying top-of-mind with past clients",
            "Competing with national brokerage brand recognition",
            "Converting off-season leads into spring transactions",
        ],
    },
    {
        "name": "Luxury Buyer",
        "description": (
            "High-net-worth buyer considering a primary or secondary property in the "
            "Wasatch Back. Often a remote worker, retiree, or business owner. "
            "Decision is lifestyle-driven. Price-sensitive to value, not price."
        ),
        "revenue_priorities": ["purchase decision", "lifestyle fit"],
        "pain_points": [
            "Understanding the micro-market (Park City vs Heber vs Kamas)",
            "Finding an agent who knows the resort market",
            "Timing the market in a low-inventory environment",
        ],
    },
    {
        "name": "Business Owner in Agent Network",
        "description": (
            "Local or regional business owner who is part of an agent's referral network. "
            "May be a past client, vendor, or community connector. Shares leads and "
            "expects reciprocal relationship value."
        ),
        "revenue_priorities": ["referrals", "community relationship"],
        "pain_points": [
            "Staying connected to the agent beyond the transaction",
            "Knowing when to refer friends and colleagues",
        ],
    },
]
