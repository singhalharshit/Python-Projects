"""
User Action Model
Tracks user actions for behavioral learning (no explicit feedback)
"""
from sqlalchemy import Column, String, JSON, DateTime, Float, Integer, func, ForeignKey, Uuid, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
from typing import Dict, Any
import numpy as np
import uuid


class UserAction(Base):
    """
    Tracks user actions for behavioral preference learning.
    System learns from actions, not questions.
    """
    __tablename__ = "user_actions"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Action type: select, reject, ignore, follow, rest
    action_type = Column(String, nullable=False, index=True)
    
    # Content vector that was acted upon (stored as JSON text)
    content_vector = Column(Text)
    
    # Topic/recommendation ID (if applicable)
    recommendation_id = Column(Uuid, ForeignKey('recommendations.id'))
    
    # Context metadata
    context = Column(JSON)  # {platform, timing, confidence, etc.}
    
    # Timestamp
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    
    # Learning weight (how much this action affects preferences)
    learning_weight = Column(Float, default=1.0)
    
    # Relationships
    # user = relationship("User", back_populates="actions")
    
    def get_content_vector(self) -> np.ndarray:
        """Get content vector as numpy array"""
        if self.content_vector:
            import json
            return np.array(json.loads(self.content_vector))
        return None
    
    def set_content_vector(self, vector: np.ndarray):
        """Set content vector from numpy array"""
        if vector is not None:
            import json
            self.content_vector = json.dumps(vector.tolist())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'action_type': self.action_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'context': self.context or {},
            'learning_weight': self.learning_weight
        }


class EmotionalState(Base):
    """
    Tracks user's emotional state inferred from behavior.
    Never asks directly - infers from actions and patterns.
    """
    __tablename__ = "emotional_states"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, unique=True, index=True)
    
    # Emotional metrics (0-1 scale)
    anxiety_level = Column(Float, default=0.3)  # Start neutral
    trust_level = Column(Float, default=0.5)
    fatigue_level = Column(Float, default=0.0)
    
    # Behavioral metrics
    posts_last_7_days = Column(Integer, default=0)
    posts_last_30_days = Column(Integer, default=0)
    
    # Rest patterns
    last_rest_day = Column(DateTime)
    rest_days_last_30 = Column(Integer, default=0)
    preferred_rest_day = Column(Integer)  # 0-6 (Monday-Sunday)
    
    # Interaction patterns
    interaction_frequency = Column(JSON)  # List of timestamps
    rapid_check_count = Column(Integer, default=0)  # Rapid checking indicates anxiety
    
    # Preference stability
    preference_volatility = Column(Float, default=0.0)  # How much preferences change
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def should_suggest_rest(self) -> bool:
        """
        Determine if user should rest today.
        Based on emotional and behavioral signals.
        """
        # High anxiety
        if self.anxiety_level > 0.7:
            return True
        
        # High fatigue
        if self.fatigue_level > 0.6:
            return True
        
        # Posted too frequently
        if self.posts_last_7_days >= 5:
            return True
        
        # It's their preferred rest day
        if self.preferred_rest_day is not None:
            today = datetime.utcnow().weekday()
            if today == self.preferred_rest_day:
                return True
        
        return False
    
    def update_from_action(self, action_type: str):
        """Update emotional state based on action"""
        
        if action_type == 'follow':
            # Following advice builds trust and reduces anxiety
            self.trust_level = min(self.trust_level + 0.1, 1.0)
            self.anxiety_level = max(self.anxiety_level - 0.05, 0.0)
        
        elif action_type == 'ignore':
            # Ignoring suggests fatigue or misalignment
            self.fatigue_level = min(self.fatigue_level + 0.1, 1.0)
        
        elif action_type == 'rest':
            # Rest reduces fatigue
            self.fatigue_level = max(self.fatigue_level - 0.3, 0.0)
            self.last_rest_day = datetime.utcnow()
            self.rest_days_last_30 += 1
        
        elif action_type == 'rapid_check':
            # Rapid checking indicates anxiety
            self.rapid_check_count += 1
            self.anxiety_level = min(self.anxiety_level + 0.1, 1.0)
        
        # Track interaction
        if not self.interaction_frequency:
            self.interaction_frequency = []
        
        self.interaction_frequency.append(datetime.utcnow().isoformat())
        
        # Keep only last 30 days
        cutoff = datetime.utcnow().timestamp() - (30 * 24 * 60 * 60)
        self.interaction_frequency = [
            t for t in self.interaction_frequency
            if datetime.fromisoformat(t).timestamp() > cutoff
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'anxiety_level': self.anxiety_level,
            'trust_level': self.trust_level,
            'fatigue_level': self.fatigue_level,
            'posts_last_7_days': self.posts_last_7_days,
            'posts_last_30_days': self.posts_last_30_days,
            'last_rest_day': self.last_rest_day.isoformat() if self.last_rest_day else None,
            'should_rest': self.should_suggest_rest(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
