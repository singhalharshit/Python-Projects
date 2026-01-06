"""
Creator Post Model
Stores post-level signals for content similarity analysis
"""
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, Float, ForeignKey, ARRAY
from sqlalchemy.sql import func
from app.core.database import Base


class CreatorPost(Base):
    """
    Stores individual posts from creators for signal analysis.
    
    Signals extracted:
    - Hashtags (for hashtag overlap)
    - Mentions (for mention graph)
    - Audio names (for audio overlap)
    - Engagement metrics (for engagement pattern similarity)
    - Posting time (for posting time similarity)
    """
    __tablename__ = "creator_posts"
    
    id = Column(String, primary_key=True)  # Platform-specific post ID
    creator_id = Column(String, ForeignKey('creators.id'), nullable=False, index=True)
    platform = Column(String, nullable=False, default='instagram')
    
    # Content signals
    caption = Column(Text)
    hashtags = Column(ARRAY(String))  # List of hashtags (without #)
    mentions = Column(ARRAY(String))  # List of mentioned usernames (without @)
    audio_name = Column(String)  # For reels/videos
    
    # Post metadata
    post_type = Column(String)  # 'reel', 'carousel', 'image', 'video'
    post_url = Column(String)
    
    # Engagement signals
    likes = Column(Integer)
    comments = Column(Integer)
    views = Column(Integer)
    shares = Column(Integer)
    
    # Timing signals
    posted_at = Column(DateTime)  # When creator posted
    posting_hour = Column(Integer)  # Hour of day (0-23)
    posting_day = Column(Integer)  # Day of week (0-6)
    
    # Metadata
    scraped_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
