"""
Trend database model for storing detected trends
"""
from sqlalchemy import Column, String, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.core.database import Base


class Trend(Base):
    __tablename__ = "trends"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    niche = Column(String(100), nullable=False, index=True)
    topic = Column(String(500), nullable=False)
    source = Column(String(50), nullable=False)  # "reddit", "youtube", etc.
    
    # Trend metrics
    momentum_score = Column(Float, default=0.0)  # 0-1 scale
    saturation_level = Column(Float, default=0.0)  # 0-1 scale
    lifecycle_stage = Column(String(50))  # "emerging", "growing", "peak", "declining"
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    metadata = Column(JSON, default=dict)
    # Example metadata:
    # {
    #   "reddit": {
    #     "upvotes": 1500,
    #     "comments": 250,
    #     "subreddit": "LocalLLaMA",
    #     "post_ids": ["abc123", "def456"]
    #   },
    #   "keywords": ["local-first", "AI", "privacy"],
    #   "related_topics": ["edge computing", "on-device ML"]
    # }
    
    def __repr__(self):
        return f"<Trend {self.topic[:50]} in {self.niche}>"
    
    @property
    def is_emerging(self) -> bool:
        """Check if trend is in emerging stage"""
        return self.lifecycle_stage == "emerging" and self.momentum_score > 0.3
    
    @property
    def is_saturated(self) -> bool:
        """Check if trend is saturated (anti-trend)"""
        return self.saturation_level > 0.7
