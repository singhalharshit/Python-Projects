"""
Signal health monitoring service
Tracks reliability of each data source
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict
import logging
from app.models.signal_health import SignalHealth

logger = logging.getLogger(__name__)


class SignalHealthMonitor:
    """Monitors and tracks health of data sources"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_success(self, source: str, response_time_ms: int = None):
        """Record successful data collection from a source"""
        
        signal = self.db.query(SignalHealth).filter(
            SignalHealth.source == source
        ).first()
        
        if not signal:
            signal = SignalHealth(
                source=source,
                success_count=0,
                failure_count=0
            )
            self.db.add(signal)
        
        signal.last_success = datetime.utcnow()
        signal.success_count += 1
        signal.failure_count = 0  # Reset failure count on success
        
        if response_time_ms:
            # Update average response time (simple moving average)
            if signal.response_time_ms:
                signal.response_time_ms = int(
                    (signal.response_time_ms * 0.7) + (response_time_ms * 0.3)
                )
            else:
                signal.response_time_ms = response_time_ms
        
        # Update status based on metrics
        if signal.failure_count == 0:
            signal.status = "healthy"
        
        self.db.commit()
        logger.info(f"Signal health: {source} - SUCCESS (response: {response_time_ms}ms)")
    
    def record_failure(self, source: str, error: str = None):
        """Record failed data collection from a source"""
        
        signal = self.db.query(SignalHealth).filter(
            SignalHealth.source == source
        ).first()
        
        if not signal:
            signal = SignalHealth(
                source=source,
                success_count=0,
                failure_count=0
            )
            self.db.add(signal)
        
        signal.last_failure = datetime.utcnow()
        signal.failure_count += 1
        
        # Update status based on failure count
        if signal.failure_count >= 5:
            signal.status = "failed"
        elif signal.failure_count >= 2:
            signal.status = "degraded"
        
        self.db.commit()
        logger.warning(f"Signal health: {source} - FAILURE (count: {signal.failure_count}) - {error}")
    
    def get_all_health_status(self) -> Dict[str, str]:
        """Get health status of all sources"""
        
        signals = self.db.query(SignalHealth).all()
        
        return {
            signal.source: signal.status
            for signal in signals
        }
    
    def get_source_health(self, source: str) -> Dict:
        """Get detailed health information for a source"""
        
        signal = self.db.query(SignalHealth).filter(
            SignalHealth.source == source
        ).first()
        
        if not signal:
            return {
                "source": source,
                "status": "unknown",
                "success_rate": 0.0
            }
        
        return {
            "source": source,
            "status": signal.status,
            "success_rate": signal.success_rate,
            "last_success": signal.last_success,
            "last_failure": signal.last_failure,
            "response_time_ms": signal.response_time_ms
        }
    
    def calculate_overall_confidence(self, sources: list) -> float:
        """
        Calculate overall confidence based on health of multiple sources
        
        Args:
            sources: List of source names
        
        Returns:
            Confidence score 0-1
        """
        if not sources:
            return 0.0
        
        healthy_count = 0
        degraded_count = 0
        
        for source in sources:
            signal = self.db.query(SignalHealth).filter(
                SignalHealth.source == source
            ).first()
            
            if signal:
                if signal.status == "healthy":
                    healthy_count += 1
                elif signal.status == "degraded":
                    degraded_count += 1
        
        # Calculate confidence
        # Healthy = 1.0, Degraded = 0.5, Failed = 0.0
        total_weight = (healthy_count * 1.0) + (degraded_count * 0.5)
        confidence = total_weight / len(sources)
        
        return confidence
