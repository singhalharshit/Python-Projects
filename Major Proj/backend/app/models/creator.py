from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, func, Float, ARRAY
from app.core.database import Base

class Creator(Base):
    __tablename__ = "creators"

    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)
    name = Column(String, nullable=False)
    handle = Column(String)
    bio = Column(Text)
    subscriber_count = Column(Integer)
    language = Column(String)
    niche = Column(String)
    embedding = Column(ARRAY(Float))  # Store as simple array, search happens in FAISS
    content_samples = Column(JSON)
    tags = Column(JSON)
    metadata_json = Column("metadata", JSON) # metadata is reserved in SQLAlchemy sometimes, safe mapping
    
    # New fields for enhanced signal storage
    verified = Column(Integer, default=0)  # 0 = not verified, 1 = verified
    category = Column(String)  # Instagram category if available
    avg_engagement_rate = Column(Float)  # Average engagement rate (likes+comments)/followers
    posting_frequency = Column(Float)  # Posts per week
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

