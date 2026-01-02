"""
User Competitor Model
Tracks user's relationship with discovered competitors.
"""
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint, func, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
from typing import Dict, Any
import uuid


class UserCompetitor(Base):
    """
    Tracks which competitors a user has accepted or rejected.
    """
    __tablename__ = "user_competitors"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey('users.id'), nullable=False, index=True)
    
    # The competitor's creator ID (which is also a user_id effectively, but strictly speaking it's external)
    competitor_id = Column(String, nullable=False, index=True)
    
    # Status
    is_accepted = Column(Boolean, default=True)  # True if user accepted, False if rejected
    is_active = Column(Boolean, default=True)    # Soft delete
    
    # Scores at time of discovery
    relevance_score = Column(Float)
    differentiation_score = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Unique constraint: unique user-competitor pair
    __table_args__ = (
        UniqueConstraint('user_id', 'competitor_id', name='uq_user_competitor'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'competitor_id': self.competitor_id,
            'is_accepted': self.is_accepted,
            'relevance_score': self.relevance_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
