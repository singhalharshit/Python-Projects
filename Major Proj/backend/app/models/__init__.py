"""
Models package - exports all database models
"""
from app.models.user import User
from app.models.niche import Niche, PREDEFINED_NICHES
from app.models.trend import Trend
from app.models.recommendation import Recommendation
from app.models.signal_health import SignalHealth
from app.models.dynamic_niche import DynamicNiche
from app.models.topic_history import TopicHistory
from app.models.user_action import UserAction, EmotionalState
from app.models.user_competitor import UserCompetitor
from app.models.creator import Creator

__all__ = [
    "User",
    "Niche",
    "PREDEFINED_NICHES",
    "Trend",
    "Recommendation",
    "SignalHealth",
    "DynamicNiche",
    "TopicHistory",
    "UserAction",
    "EmotionalState",
    "UserCompetitor",
    "Creator",
]
