"""
Signal health monitoring model
"""
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.core.database import Base


class SignalHealth(Base):
    __tablename__ = "signal_health"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # "healthy", "degraded", "failed"
    
    # Health metrics
    last_success = Column(DateTime)
    last_failure = Column(DateTime)
    failure_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    response_time_ms = Column(Integer)  # Average response time
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SignalHealth {self.source}: {self.status}>"
    
    @property
    def is_healthy(self) -> bool:
        """Check if signal source is healthy"""
        return self.status == "healthy"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total
