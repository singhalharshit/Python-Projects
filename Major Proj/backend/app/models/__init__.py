"""
Models package - exports all database models
"""
from app.models.user import User
from app.models.niche import Niche, PREDEFINED_NICHES
from app.models.trend import Trend
from app.models.recommendation import Recommendation
from app.models.signal_health import SignalHealth

__all__ = [
    "User",
    "Niche",
    "PREDEFINED_NICHES",
    "Trend",
    "Recommendation",
    "SignalHealth",
]
