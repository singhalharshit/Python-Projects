"""
Competitor Candidate Model
Stores generated competitor candidates before user feedback
"""
from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class CompetitorCandidate(Base):
    """
    Stores competitor candidates generated for a user.
    
    Tracks:
    - Which candidates were generated
    - Their scores and signal breakdowns
    - Whether they were shown to the user
    - Ranking order
    """
    __tablename__ = "competitor_candidates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    creator_id = Column(String, ForeignKey('creators.id'), nullable=False, index=True)
    
    # Scoring
    total_score = Column(Float, nullable=False)
    rank = Column(Integer)  # Ranking position (1 = best)
    
    # Signal breakdown (JSON for flexibility)
    signals_json = Column(JSON)  # {
    #   "content_similarity": 0.85,
    #   "hashtag_overlap": 0.72,
    #   "audio_overlap": 0.45,
    #   "engagement_similarity": 0.91,
    #   "tier_similarity": 0.88,
    #   "time_similarity": 0.65
    # }
    
    # Discovery metadata
    discovery_path = Column(String)  # 'hashtag', 'audio', 'mention', 'semantic'
    shown_to_user = Column(Boolean, default=False)
    
    # Timestamps
    generated_at = Column(DateTime, server_default=func.now())
    shown_at = Column(DateTime)  # When shown to user
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'creator_id': self.creator_id,
            'total_score': self.total_score,
            'rank': self.rank,
            'signals': self.signals_json,
            'discovery_path': self.discovery_path,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }
