"""
Niche database model for micro-niche definitions
"""
from sqlalchemy import Column, String, DateTime, JSON, Float, Uuid
from datetime import datetime
import uuid
from app.core.database import Base


class Niche(Base):
    __tablename__ = "niches"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500))
    
    # Current vibe analysis
    current_vibe = Column(String(50))  # "hype", "critique", "calm_clarity"
    vibe_description = Column(String(500))
    vibe_confidence = Column(String(20))  # "low", "medium", "high"
    vibe_updated_at = Column(DateTime)
    
    # Data sources for this niche
    data_sources = Column(JSON, default=dict)
    # Example:
    # {
    #   "reddit": ["r/LocalLLaMA", "r/MachineLearning"],
    #   "youtube": ["channel_id_1", "channel_id_2"],
    #   "rss": ["https://blog.example.com/feed"]
    # }
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Niche {self.name}>"


# Predefined niches for Phase 1
PREDEFINED_NICHES = [
    {
        "name": "tech_creators",
        "description": "Developers creating AI tools, libraries, and applications",
        "data_sources": {
            "reddit": ["LocalLLaMA", "MachineLearning", "artificial"],
            "youtube": [],
            "rss": []
        }
    },
    {
        "name": "gaming_creators",
        "description": "Gaming news, reviews, and esports coverage",
        "data_sources": {
            "reddit": ["gaming", "Games", "esports"],
            "youtube": [],
            "rss": []
        }
    },
    {
        "name": "business_creators",
        "description": "Entrepreneurship, startups, and marketing advice",
        "data_sources": {
            "reddit": ["SideProject", "EntrepreneurRideAlong", "startups"],
            "youtube": [],
            "rss": []
        }
    }
]
