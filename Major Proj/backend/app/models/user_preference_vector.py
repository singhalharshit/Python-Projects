from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.types import Float
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class UserPreferenceVector(Base):
    __tablename__ = "user_preference_vectors"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vector = Column(ARRAY(Float), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
