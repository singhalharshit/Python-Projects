"""
Top-Down Competitor Discovery for Large Creators
Builds category-based attention graph using public sources (manual/demo for now).
"""
from typing import List, Dict

# Example demo data (should later come from config/db/api)
CATEGORY_TOP_CREATORS = {
    "fitness": [
        {"creator_id": "blogilates", "platform": "youtube", "name": "Cassey Ho (Blogilates)", "subs": "8M+", "tags": ["fitness", "pilates"], "geo": "global"},
        {"creator_id": "chrisheria", "platform": "youtube", "name": "Chris Heria", "subs": "5M+", "tags": ["home workouts", "calisthenics"], "geo": "global"},
        {"creator_id": "kayla_itsines", "platform": "instagram", "name": "Kayla Itsines", "subs": "15M+", "tags": ["fitness", "hiit"], "geo": "global"},
        {"creator_id": "pamela_rf", "platform": "youtube", "name": "Pamela Reif", "subs": "9M+", "tags": ["fitness", "nutrition"], "geo": "global"},
        {"creator_id": "thenx", "platform": "youtube", "name": "THENX", "subs": "7M+", "tags": ["bodyweight", "workouts"], "geo": "global"},
        {"creator_id": "simeonpanda", "platform": "instagram", "name": "Simeon Panda", "subs": "8M+", "tags": ["fitness", "motivation"], "geo": "global"},
        {"creator_id": "jeffnippard", "platform": "youtube", "name": "Jeff Nippard", "subs": "4M+", "tags": ["science based", "training"], "geo": "global"},
        {"creator_id": "whitneyysimmons", "platform": "instagram", "name": "Whitney Simmons", "subs": "3M+", "tags": ["fitness", "wellness"], "geo": "global"},
        {"creator_id": "melissa_wood_health", "platform": "instagram", "name": "Melissa Wood Tepperberg", "subs": "1M+", "tags": ["mindful", "yoga", "pilates"], "geo": "global"},
    ],
    # Add tech, lifestyle, education for demo
}

def get_topdown_competitors(category: str, user_profile: dict = None, limit: int = 10) -> List[Dict]:
    """
    Returns top creators for a category, optionally filtered by user features (geo, style...)
    """
    creators = CATEGORY_TOP_CREATORS.get(category.lower(), [])
    # TODO: personalizing further (geo/style), but just truncate for now
    return creators[:limit]

