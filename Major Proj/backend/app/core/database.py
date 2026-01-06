"""
Database connection setup with SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session
    
    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database - create all tables
    Called on application startup
    """
    # Import all models so they are registered with Base
    from app.models.user import User
    from app.models.niche import Niche
    from app.models.trend import Trend
    from app.models.recommendation import Recommendation
    from app.models.signal_health import SignalHealth
    from app.models.user_action import UserAction, EmotionalState
    from app.models.topic_history import TopicHistory
    from app.models.dynamic_niche import DynamicNiche
    from app.models.user_competitor import UserCompetitor
    
    # New models for Creator Similarity Engine
    from app.models.creator_post import CreatorPost
    from app.models.competitor_candidate import CompetitorCandidate
    from app.models.user_competitor_feedback import UserCompetitorFeedback
    from app.models.user_preference_weights import UserPreferenceWeights
    
    Base.metadata.create_all(bind=engine)
