"""
Competitor Preference Learner
Updates user preference weights based on competitor feedback (learning loop)

Specialized for Creator Similarity Engine
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.models.user_preference_weights import UserPreferenceWeights
from app.models.user_competitor_feedback import UserCompetitorFeedback

logger = logging.getLogger(__name__)


class CompetitorPreferenceLearner:
    """
    Learns user preferences from competitor accept/reject feedback.
    
    Learning Rules:
    - Accept: Boost weights for strong signals (score > 0.7)
    - Reject: Penalize weights for strong signals (score > 0.7)
    - Normalize: Keep weights summing to 1.0
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.boost_factor = 1.1  # 10% increase on accept
        self.penalty_factor = 0.9  # 10% decrease on reject
    
    def update_from_feedback(
        self,
        user_id: str,
        creator_id: str,
        action: str,
        signals: Dict[str, float],
        confidence: float
    ):
        """
        Update user's preference weights based on feedback.
        
        Args:
            user_id: User's ID
            creator_id: Competitor creator ID
            action: 'accept' or 'reject'
            signals: Signal scores at time of suggestion
            confidence: System confidence (0-1)
        """
        logger.info(f"Learning from {action} for user {user_id}")
        
        # Get or create user weights
        weights = self.db.query(UserPreferenceWeights).filter(
            UserPreferenceWeights.user_id == user_id
        ).first()
        
        if not weights:
            weights = UserPreferenceWeights(user_id=user_id)
            self.db.add(weights)
        
        # Record feedback
        feedback = UserCompetitorFeedback(
            user_id=user_id,
            creator_id=creator_id,
            action=action,
            confidence=confidence,
            signals_at_feedback=json.dumps(signals)
        )
        self.db.add(feedback)
        
        # Update weights based on action
        if action == 'accept':
            self._boost_weights(weights, signals)
        elif action == 'reject':
            self._penalize_weights(weights, signals)
        
        # Normalize weights
        weights.normalize_weights()
        
        # Update metadata
        weights.feedback_count += 1
        weights.last_updated_at = datetime.now()
        
        self.db.commit()
        
        logger.info(f"Updated weights for user {user_id}: {weights.to_dict()}")
    
    def _boost_weights(self, weights: UserPreferenceWeights, signals: Dict[str, float]):
        """Boost weights for strong signals on accept"""
        
        # Content similarity
        if signals.get('content_similarity', 0) > 0.7:
            weights.content_weight *= self.boost_factor
        
        # Hashtag overlap
        if signals.get('hashtag_overlap', 0) > 0.7:
            weights.hashtag_weight *= self.boost_factor
        
        # Audio overlap
        if signals.get('audio_overlap', 0) > 0.7:
            weights.audio_weight *= self.boost_factor
        
        # Engagement similarity
        if signals.get('engagement_similarity', 0) > 0.7:
            weights.engagement_weight *= self.boost_factor
        
        # Tier similarity
        if signals.get('tier_similarity', 0) > 0.7:
            weights.tier_weight *= self.boost_factor
        
        # Time similarity
        if signals.get('time_similarity', 0) > 0.7:
            weights.time_weight *= self.boost_factor
    
    def _penalize_weights(self, weights: UserPreferenceWeights, signals: Dict[str, float]):
        """Penalize weights for strong signals on reject"""
        
        # Content similarity
        if signals.get('content_similarity', 0) > 0.7:
            weights.content_weight *= self.penalty_factor
        
        # Hashtag overlap
        if signals.get('hashtag_overlap', 0) > 0.7:
            weights.hashtag_weight *= self.penalty_factor
        
        # Audio overlap
        if signals.get('audio_overlap', 0) > 0.7:
            weights.audio_weight *= self.penalty_factor
        
        # Engagement similarity
        if signals.get('engagement_similarity', 0) > 0.7:
            weights.engagement_weight *= self.penalty_factor
        
        # Tier similarity
        if signals.get('tier_similarity', 0) > 0.7:
            weights.tier_weight *= self.penalty_factor
        
        # Time similarity
        if signals.get('time_similarity', 0) > 0.7:
            weights.time_weight *= self.penalty_factor
    
    def get_user_weights(self, user_id: str) -> Dict[str, float]:
        """Get user's current weights"""
        weights = self.db.query(UserPreferenceWeights).filter(
            UserPreferenceWeights.user_id == user_id
        ).first()
        
        if weights:
            return weights.to_dict()
        else:
            # Return defaults
            return {
                'content_weight': 0.20,
                'hashtag_weight': 0.20,
                'audio_weight': 0.15,
                'engagement_weight': 0.15,
                'tier_weight': 0.15,
                'time_weight': 0.15,
                'feedback_count': 0
            }
