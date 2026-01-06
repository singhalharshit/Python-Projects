from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class CompetitorFeedback(Base):
    __tablename__ = "competitor_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    competitor_id = Column(String, nullable=False)
    action = Column(String, nullable=False)  # 'accept' | 'reject'
    similarity_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
