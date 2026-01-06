"""
User Preference Weights Model
Stores learnable signal weights for personalized scoring
"""
from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class UserPreferenceWeights(Base):
    """
    Stores learned preference weights for each user.
    
    These weights personalize the competitor scoring formula:
    score = w1*content + w2*hashtag + w3*audio + w4*engagement + w5*tier + w6*time
    
    Weights are updated via online learning (real-time) and offline learning (batch).
    """
    __tablename__ = "user_preference_weights"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True)
    
    # Signal weights (sum should be ~1.0 for normalization)
    content_weight = Column(Float, default=0.20)  # Bio + caption similarity
    hashtag_weight = Column(Float, default=0.20)  # Hashtag overlap
    audio_weight = Column(Float, default=0.15)    # Audio/reel overlap
    engagement_weight = Column(Float, default=0.15)  # Engagement pattern similarity
    tier_weight = Column(Float, default=0.15)     # Follower tier similarity
    time_weight = Column(Float, default=0.15)     # Posting time similarity
    
    # Learning metadata
    feedback_count = Column(Float, default=0)  # Number of feedback actions
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def normalize_weights(self):
        """Ensure weights sum to 1.0"""
        total = (
            self.content_weight + 
            self.hashtag_weight + 
            self.audio_weight + 
            self.engagement_weight + 
            self.tier_weight + 
            self.time_weight
        )
        
        if total > 0:
            self.content_weight /= total
            self.hashtag_weight /= total
            self.audio_weight /= total
            self.engagement_weight /= total
            self.tier_weight /= total
            self.time_weight /= total
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'user_id': str(self.user_id),
            'content_weight': self.content_weight,
            'hashtag_weight': self.hashtag_weight,
            'audio_weight': self.audio_weight,
            'engagement_weight': self.engagement_weight,
            'tier_weight': self.tier_weight,
            'time_weight': self.time_weight,
            'feedback_count': self.feedback_count,
            'last_updated_at': self.last_updated_at.isoformat() if self.last_updated_at else None
        }
