"""
Feedback Loop - Core Self-Learning Mechanism

Tracks user actions and continuously adapts the system.
This is how the system learns WITHOUT asking questions.
"""

import logging
from typing import Dict, List, Optional, Literal
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from sqlalchemy.orm import Session

from app.models.user_action import UserAction
from app.models.recommendation import Recommendation
from app.services.intelligence.preference_learner import PreferenceLearner
from app.services.intelligence.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

ActionType = Literal["viewed", "accepted", "rejected", "followed", "ignored"]


@dataclass
class ActionSignal:
    """Represents a user action and its learning implications"""
    action: ActionType
    weight: float  # How much to update preferences
    direction: Literal["positive", "negative", "neutral"]
    confidence: float  # How confident we are in this signal


class FeedbackLoop:
    """
    Learns from user behavior without asking questions.
    
    Learning Rules:
    - VIEWED: User saw it (neutral signal)
    - ACCEPTED: User agrees with recommendation (weak positive)
    - FOLLOWED: User actually posted about it (STRONG positive)
    - REJECTED: User disagrees (negative signal)
    - IGNORED: User didn't interact (weak negative)
    
    Emotional Safety Rules:
    - NEVER pressure users
    - NEVER shame rejections
    - NEVER optimize for engagement over wellbeing
    """
    
    def __init__(
        self,
        db: Session,
        preference_learner: PreferenceLearner,
        embedding_service: EmbeddingService
    ):
        self.db = db
        self.preference_learner = preference_learner
        self.embedding_service = embedding_service
        
    async def process_user_action(
        self,
        user_id: str,
        recommendation_id: str,
        action: ActionType,
        timestamp: Optional[datetime] = None,
        context: Optional[Dict] = None
    ):
        """
        Process a single user action and update preferences.
        
        This is the core learning loop.
        """
        timestamp = timestamp or datetime.utcnow()
        
        logger.info(f"Processing action: user={user_id}, rec={recommendation_id}, action={action}")
        
        # Get recommendation details
        recommendation = self.db.query(Recommendation).filter_by(
            id=recommendation_id
        ).first()
        
        if not recommendation:
            logger.error(f"Recommendation {recommendation_id} not found")
            return
        
        # Convert action to learning signal
        signal = self._action_to_signal(action, context)
        
        # Get content embedding
        content_embedding = self._get_content_embedding(recommendation)
        
        # Update preference vector
        if signal.direction == "positive":
            self.preference_learner.update_positive_preference(
                user_id=user_id,
                content_vector=content_embedding,
                weight=signal.weight
            )
        elif signal.direction == "negative":
            self.preference_learner.update_negative_preference(
                user_id=user_id,
                content_vector=content_embedding,
                weight=signal.weight
            )
        # neutral = no preference update
        
        # Store action in database for pattern analysis
        action_record = UserAction(
            user_id=user_id,
            recommendation_id=recommendation_id,
            action_type=action,
            timestamp=timestamp,
            context=context or {}
        )
        self.db.add(action_record)
        
        # Update recommendation success tracking
        if action in ["followed", "accepted"]:
            recommendation.was_accepted = True
            recommendation.acceptance_timestamp = timestamp
        elif action == "rejected":
            recommendation.was_rejected = True
            recommendation.rejection_timestamp = timestamp
        
        self.db.commit()
        
        logger.info(f"Preference update complete: direction={signal.direction}, weight={signal.weight}")
    
    def _action_to_signal(
        self,
        action: ActionType,
        context: Optional[Dict] = None
    ) -> ActionSignal:
        """
        Convert user action to learning signal.
        
        Different actions have different learning weights.
        """
        
        action_map = {
            "viewed": ActionSignal(
                action="viewed",
                weight=0.0,
                direction="neutral",
                confidence=0.5
            ),
            "accepted": ActionSignal(
                action="accepted",
                weight=0.4,
                direction="positive",
                confidence=0.7
            ),
            "followed": ActionSignal(
                action="followed",
                weight=1.0,  # STRONGEST signal
                direction="positive",
                confidence=0.95
            ),
            "rejected": ActionSignal(
                action="rejected",
                weight=0.3,
                direction="negative",
                confidence=0.6
            ),
            "ignored": ActionSignal(
                action="ignored",
                weight=0.1,
                direction="negative",
                confidence=0.4
            ),
        }
        
        signal = action_map.get(action)
        
        # Adjust based on context
        if context:
            # If user quickly rejected without reading, reduce weight
            if action == "rejected" and context.get("time_spent", 0) < 5:
                signal.weight *= 0.5
                signal.confidence *= 0.7
            
            # If user spent time reading before accepting, increase weight
            elif action == "accepted" and context.get("time_spent", 0) > 30:
                signal.weight *= 1.3
                signal.confidence *= 1.1
        
        return signal
    
    def _get_content_embedding(self, recommendation: Recommendation) -> np.ndarray:
        """Get semantic embedding of recommendation content"""
        
        # Combine topic, reasoning, and tags into content representation
        content_text = f"{recommendation.topic} {recommendation.reasoning} {' '.join(recommendation.tags or [])}"
        
        embedding = self.embedding_service.embed_text(content_text)
        return embedding
    
    async def analyze_pattern_changes(
        self,
        user_id: str,
        lookback_days: int = 30
    ) -> Dict:
        """
        Analyze if user preferences are shifting over time.
        
        Returns insights about preference drift.
        """
        
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Get recent actions
        recent_actions = self.db.query(UserAction).filter(
            UserAction.user_id == user_id,
            UserAction.timestamp >= cutoff_date
        ).order_by(UserAction.timestamp.desc()).all()
        
        if len(recent_actions) < 10:
            return {"status": "insufficient_data", "action_count": len(recent_actions)}
        
        # Split into early and late periods
        mid_point = len(recent_actions) // 2
        early_actions = recent_actions[mid_point:]
        late_actions = recent_actions[:mid_point]
        
        # Calculate acceptance rates
        early_acceptance = self._calculate_acceptance_rate(early_actions)
        late_acceptance = self._calculate_acceptance_rate(late_actions)
        
        # Detect drift
        drift = late_acceptance - early_acceptance
        
        analysis = {
            "status": "analyzed",
            "action_count": len(recent_actions),
            "early_acceptance_rate": early_acceptance,
            "late_acceptance_rate": late_acceptance,
            "drift": drift,
            "interpretation": self._interpret_drift(drift)
        }
        
        logger.info(f"Pattern analysis for user {user_id}: {analysis}")
        return analysis
    
    def _calculate_acceptance_rate(self, actions: List[UserAction]) -> float:
        """Calculate acceptance rate from action list"""
        if not actions:
            return 0.0
        
        accepted = sum(1 for a in actions if a.action_type in ["accepted", "followed"])
        return accepted / len(actions)
    
    def _interpret_drift(self, drift: float) -> str:
        """Interpret what preference drift means"""
        
        if abs(drift) < 0.1:
            return "stable_preferences"
        elif drift > 0.1:
            return "improving_fit"  # System is learning well
        elif drift < -0.1:
            return "declining_fit"  # System may need recalibration
        
        return "stable_preferences"
    
    async def detect_behavioral_patterns(
        self,
        user_id: str,
        pattern_type: Literal["time", "content", "mood"]
    ) -> Dict:
        """
        Detect patterns in user behavior for better personalization.
        
        Types:
        - time: When does user typically engage? (morning/evening)
        - content: What content types do they prefer?
        - mood: Are they risk-averse or adventurous?
        """
        
        # Get user's action history
        actions = self.db.query(UserAction).filter(
            UserAction.user_id == user_id
        ).order_by(UserAction.timestamp.desc()).limit(100).all()
        
        if len(actions) < 20:
            return {"status": "insufficient_data"}
        
        if pattern_type == "time":
            return self._detect_time_patterns(actions)
        elif pattern_type == "content":
            return self._detect_content_patterns(actions)
        elif pattern_type == "mood":
            return self._detect_mood_patterns(actions)
        
        return {"status": "unknown_pattern_type"}
    
    def _detect_time_patterns(self, actions: List[UserAction]) -> Dict:
        """Detect when user is most active"""
        
        hours = [action.timestamp.hour for action in actions]
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # Find peak hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [h for h, _ in sorted_hours[:3]]
        
        # Classify as morning/afternoon/evening
        avg_hour = np.mean(hours)
        
        if avg_hour < 12:
            preference = "morning"
        elif avg_hour < 18:
            preference = "afternoon"
        else:
            preference = "evening"
        
        return {
            "status": "detected",
            "preference": preference,
            "peak_hours": peak_hours,
            "average_hour": avg_hour
        }
    
    def _detect_content_patterns(self, actions: List[UserAction]) -> Dict:
        """Detect content type preferences"""
        
        # Get accepted recommendations
        accepted_actions = [
            a for a in actions 
            if a.action_type in ["accepted", "followed"]
        ]
        
        if len(accepted_actions) < 5:
            return {"status": "insufficient_data"}
        
        # Get recommendation details
        accepted_recs = [
            self.db.query(Recommendation).filter_by(id=a.recommendation_id).first()
            for a in accepted_actions
        ]
        
        # Analyze common themes
        all_topics = [rec.topic for rec in accepted_recs if rec]
        all_tags = []
        for rec in accepted_recs:
            if rec and rec.tags:
                all_tags.extend(rec.tags)
        
        # Find most common
        from collections import Counter
        topic_freq = Counter(all_topics)
        tag_freq = Counter(all_tags)
        
        return {
            "status": "detected",
            "top_topics": [t for t, _ in topic_freq.most_common(3)],
            "top_tags": [t for t, _ in tag_freq.most_common(5)]
        }
    
    def _detect_mood_patterns(self, actions: List[UserAction]) -> Dict:
        """Detect if user is risk-averse or adventurous"""
        
        # Risk-averse: Prefers high-confidence, familiar topics
        # Adventurous: Accepts lower-confidence, novel topics
        
        accepted_actions = [
            a for a in actions 
            if a.action_type in ["accepted", "followed"]
        ]
        
        if len(accepted_actions) < 10:
            return {"status": "insufficient_data"}
        
        # Get confidences of accepted recommendations
        accepted_recs = [
            self.db.query(Recommendation).filter_by(id=a.recommendation_id).first()
            for a in accepted_actions
        ]
        
        avg_confidence = np.mean([
            rec.confidence_score for rec in accepted_recs if rec
        ])
        
        # Classify
        if avg_confidence > 0.75:
            mood = "risk_averse"
        elif avg_confidence < 0.6:
            mood = "adventurous"
        else:
            mood = "balanced"
        
        return {
            "status": "detected",
            "mood": mood,
            "avg_confidence_accepted": avg_confidence,
            "interpretation": self._interpret_mood(mood)
        }
    
    def _interpret_mood(self, mood: str) -> str:
        """Explain what mood means for recommendations"""
        
        interpretations = {
            "risk_averse": "User prefers safe, high-confidence recommendations. Favor established trends.",
            "adventurous": "User is comfortable with uncertainty. Can suggest emerging trends.",
            "balanced": "User evaluates each opportunity individually. Provide clear rationale."
        }
        
        return interpretations.get(mood, "")
