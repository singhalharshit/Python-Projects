"""
User database model
"""
from sqlalchemy import Column, String, DateTime, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # User preferences
    selected_niches = Column(ARRAY(String), default=list)  # List of niche IDs
    timezone = Column(String(50), default="UTC")
    notification_time = Column(String(10), default="09:00")  # HH:MM format
    
    # Additional preferences stored as JSON
    preferences = Column(JSON, default=dict)
    # Example preferences:
    # {
    #   "platforms": ["twitter", "linkedin"],
    #   "content_types": ["technical", "educational"],
    #   "risk_tolerance": "conservative"
    # }
    
    def __repr__(self):
        return f"<User {self.email}>"
