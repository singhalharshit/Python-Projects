"""
User Competitor Feedback Model
Tracks user accept/reject actions for learning loop
"""
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class UserCompetitorFeedback(Base):
    """
    Tracks user feedback on competitor suggestions.
    
    Powers the learning loop:
    - Accept actions strengthen similar signals
    - Reject actions penalize similar signals
    """
    __tablename__ = "user_competitor_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    creator_id = Column(String, ForeignKey('creators.id'), nullable=False, index=True)
    
    # Feedback
    action = Column(String, nullable=False)  # 'accept' or 'reject'
    
    # System confidence at time of suggestion
    confidence = Column(Float)  # 0.0 - 1.0
    
    # Signal breakdown at time of suggestion (for learning)
    signals_at_feedback = Column(String)  # JSON string of signal scores
    
    # Optional rejection reason (for future analysis)
    rejection_reason = Column(String)  # 'too_small', 'irrelevant', 'different_audience', etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Composite index for fast lookups
    __table_args__ = (
        Index('idx_user_creator_feedback', 'user_id', 'creator_id'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'creator_id': self.creator_id,
            'action': self.action,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
