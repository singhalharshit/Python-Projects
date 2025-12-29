"""
Recommendation database model
"""
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
import uuid
from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    niche = Column(String(100), nullable=False)
    
    # Recommendation details
    action = Column(String(50), nullable=False)  # "post", "engage", "rest"
    topic = Column(String(500))  # What to post about (if action="post")
    reasoning = Column(String(2000))  # Conservative explanation
    
    # Confidence metrics
    confidence_score = Column(Integer, nullable=False)  # 0-100
    certainty_level = Column(String(20), nullable=False)  # "low", "medium", "high"
    
    # Signal health status
    signal_health = Column(JSON, default=dict)
    # Example:
    # {
    #   "reddit": "healthy",
    #   "youtube": "healthy",
    #   "github": "degraded",
    #   "hackernews": "failed"
    # }
    
    # Anti-trends to avoid
    anti_trends = Column(JSON, default=list)
    # Example:
    # [
    #   {
    #     "topic": "AI agent frameworks",
    #     "reason": "Saturation detected. 15+ posts in last 3 days",
    #     "advice": "Avoid unless you have a unique angle"
    #   }
    # ]
    
    # Current vibe
    vibe = Column(JSON, default=dict)
    # Example:
    # {
    #   "current_mood": "calm_clarity",
    #   "description": "Audience receptive to technical depth",
    #   "confidence": "medium"
    # }
    
    # Timing suggestion
    timing = Column(JSON, default=dict)
    # Example:
    # {
    #   "best_time": "2025-12-29T14:00:00Z",
    #   "reason": "Peak engagement 2-4 PM UTC for this niche"
    # }
    
    # User feedback and outcomes
    user_feedback = Column(String(50))  # "accepted", "ignored", "modified"
    outcome = Column(JSON, default=dict)  # Track actual results if user shares
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    viewed_at = Column(DateTime)
    feedback_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Recommendation {self.action} for {self.niche} on {self.date}>"
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if recommendation has high confidence"""
        return self.confidence_score >= 75
    
    @property
    def should_rest(self) -> bool:
        """Check if recommendation suggests resting"""
        return self.action == "rest"
