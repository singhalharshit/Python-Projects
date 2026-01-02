"""
Topic History Model
Tracks topic appearances over time for saturation detection
"""
from sqlalchemy import Column, String, Integer, JSON, DateTime, Float, func
from app.core.database import Base
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
import hashlib


class TopicHistory(Base):
    """
    Tracks topic appearances over time to detect saturation and lifecycle phases.
    Uses vector hashing for deduplication across different phrasings.
    """
    __tablename__ = "topic_history"
    
    id = Column(String, primary_key=True)
    
    # Topic hash for deduplication (MD5 of rounded vector)
    topic_hash = Column(String, unique=True, index=True, nullable=False)
    
    # Topic vector (stored as JSON array)
    topic_vector = Column(JSON, nullable=False)
    
    # Representative text (for human readability)
    representative_text = Column(String)
    
    # Appearance tracking
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    appearance_count = Column(Integer, default=1)
    
    # Lifecycle tracking
    lifecycle_phase = Column(String)  # emerging, accelerating, peak, saturated, declining
    
    # Saturation metrics
    saturation_score = Column(Float, default=0.0)  # 0-1
    peak_date = Column(DateTime)  # When it peaked
    decline_rate = Column(Float)  # Rate of decline if declining
    
    # Source tracking
    source_platforms = Column(JSON)  # List of platforms where detected
    
    # Momentum history (last 7 days)
    momentum_history = Column(JSON)  # List of {date, momentum} dicts
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    @staticmethod
    def hash_vector(vector: np.ndarray) -> str:
        """
        Create hash for vector (for deduplication).
        Rounds to 2 decimals to catch similar vectors.
        """
        rounded = np.round(vector, 2)
        return hashlib.md5(rounded.tobytes()).hexdigest()
    
    def get_topic_vector(self) -> np.ndarray:
        """Get topic vector as numpy array"""
        if self.topic_vector:
            return np.array(self.topic_vector)
        return None
    
    def set_topic_vector(self, vector: np.ndarray):
        """Set topic vector from numpy array"""
        self.topic_vector = vector.tolist()
        self.topic_hash = self.hash_vector(vector)
    
    def add_appearance(self, platform: str, momentum: float):
        """Record a new appearance"""
        self.appearance_count += 1
        self.last_seen = datetime.utcnow()
        
        # Update source platforms
        if not self.source_platforms:
            self.source_platforms = []
        if platform not in self.source_platforms:
            self.source_platforms.append(platform)
        
        # Update momentum history
        if not self.momentum_history:
            self.momentum_history = []
        
        self.momentum_history.append({
            'date': datetime.utcnow().isoformat(),
            'momentum': momentum,
            'platform': platform
        })
        
        # Keep only last 30 days
        cutoff = datetime.utcnow().timestamp() - (30 * 24 * 60 * 60)
        self.momentum_history = [
            h for h in self.momentum_history
            if datetime.fromisoformat(h['date']).timestamp() > cutoff
        ]
    
    def calculate_saturation(self) -> float:
        """
        Calculate current saturation score (0-1).
        Based on frequency, recency, and momentum trend.
        """
        now = datetime.utcnow()
        
        # Frequency score
        days_since_first = max((now - self.first_seen).days, 1)
        appearances_per_day = self.appearance_count / days_since_first
        frequency_score = min(appearances_per_day / 10, 1.0)  # Normalize to 0-1
        
        # Recency score (higher if seen recently)
        days_since_last = max((now - self.last_seen).days, 0)
        recency_score = 1.0 / (1.0 + days_since_last)
        
        # Momentum trend (is it declining?)
        if self.momentum_history and len(self.momentum_history) >= 3:
            recent_momentum = [h['momentum'] for h in self.momentum_history[-5:]]
            momentum_trend = np.polyfit(range(len(recent_momentum)), recent_momentum, 1)[0]
            
            # If declining, increase saturation
            if momentum_trend < 0:
                trend_penalty = abs(momentum_trend) * 0.5
            else:
                trend_penalty = 0
        else:
            trend_penalty = 0
        
        # Combine scores
        saturation = min(
            (frequency_score * 0.5 + recency_score * 0.3 + trend_penalty * 0.2),
            1.0
        )
        
        self.saturation_score = saturation
        return saturation
    
    def infer_lifecycle_phase(self) -> str:
        """
        Infer current lifecycle phase.
        Returns: emerging, accelerating, peak, saturated, declining
        """
        if not self.momentum_history or len(self.momentum_history) < 3:
            return "emerging"
        
        # Get recent momentum values
        recent_momentum = [h['momentum'] for h in self.momentum_history[-7:]]
        avg_momentum = np.mean(recent_momentum)
        
        # Calculate trend
        momentum_trend = np.polyfit(range(len(recent_momentum)), recent_momentum, 1)[0]
        
        saturation = self.calculate_saturation()
        
        # Determine phase
        if saturation > 0.8:
            return "saturated"
        elif momentum_trend < -0.1:
            return "declining"
        elif momentum_trend > 0.15 and saturation < 0.4:
            return "emerging"
        elif momentum_trend > 0.05 and saturation < 0.6:
            return "accelerating"
        elif avg_momentum > 0.7:
            return "peak"
        else:
            return "stable"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'representative_text': self.representative_text,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'appearance_count': self.appearance_count,
            'lifecycle_phase': self.lifecycle_phase or self.infer_lifecycle_phase(),
            'saturation_score': self.saturation_score,
            'source_platforms': self.source_platforms or [],
            'momentum_trend': self.momentum_history[-5:] if self.momentum_history else []
        }
