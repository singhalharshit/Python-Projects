"""
Emotional State Tracker - Infers emotional state from behavior
"""
import logging
import uuid
from typing import Dict, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user_action import EmotionalState, UserAction

logger = logging.getLogger(__name__)


class EmotionalStateTracker:
    """
    Tracks user's emotional state inferred from behavior.
    
    Philosophy:
    - NEVER ask users how they feel
    - Infer from behavioral signals
    - Track anxiety, trust, fatigue
    - Adapt recommendations based on state
    
    Signals:
    - Rapid checking → anxiety
    - Ignoring recommendations → fatigue or misalignment
    - Following advice → trust building
    - Taking rest → self-awareness
    - Posting frequency → fatigue risk
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_state(self, user_id: Union[str, uuid.UUID]) -> EmotionalState:
        """
        Get or create emotional state for user.
        
        Args:
            user_id: User ID (string or UUID)
        
        Returns:
            EmotionalState object
        """
        # Convert string user_id to UUID if needed
        if isinstance(user_id, str):
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                # If not a valid UUID string, generate a UUID from the string
                user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
                logger.info(f"Generated UUID {user_uuid} for user_id '{user_id}'")
        else:
            user_uuid = user_id
        
        state = self.db.query(EmotionalState).filter_by(
            user_id=user_uuid
        ).first()
        
        if not state:
            state = EmotionalState(
                user_id=user_uuid,
                anxiety_level=0.3,  # Start neutral
                trust_level=0.5,
                fatigue_level=0.0,
                posts_last_7_days=0,
                posts_last_30_days=0,
                rest_days_last_30=0,
                rapid_check_count=0,
                interaction_frequency=[],
                preference_volatility=0.0
            )
            self.db.add(state)
            self.db.commit()
            
            logger.info(f"Created emotional state for user {user_uuid}")
        
        return state
    
    def update_from_action(
        self,
        user_id: Union[str, uuid.UUID],
        action_type: str,
        context: Dict = None
    ):
        """
        Update emotional state based on user action.
        
        Args:
            user_id: User ID (string or UUID)
            action_type: Type of action
            context: Optional context
        """
        state = self.get_or_create_state(user_id)
        
        # Update based on action type
        if action_type == 'follow':
            # Following advice builds trust and reduces anxiety
            state.trust_level = min(state.trust_level + 0.1, 1.0)
            state.anxiety_level = max(state.anxiety_level - 0.05, 0.0)
            
            logger.info(
                f"User {user_id} followed advice: "
                f"trust↑ {state.trust_level:.2f}, "
                f"anxiety↓ {state.anxiety_level:.2f}"
            )
        
        elif action_type == 'ignore':
            # Ignoring suggests fatigue or misalignment
            state.fatigue_level = min(state.fatigue_level + 0.1, 1.0)
            
            logger.info(
                f"User {user_id} ignored recommendation: "
                f"fatigue↑ {state.fatigue_level:.2f}"
            )
        
        elif action_type == 'rest':
            # Rest reduces fatigue
            state.fatigue_level = max(state.fatigue_level - 0.3, 0.0)
            state.last_rest_day = datetime.utcnow()
            state.rest_days_last_30 += 1
            
            logger.info(
                f"User {user_id} took rest day: "
                f"fatigue↓ {state.fatigue_level:.2f}"
            )
        
        elif action_type == 'rapid_check':
            # Rapid checking indicates anxiety
            state.rapid_check_count += 1
            state.anxiety_level = min(state.anxiety_level + 0.1, 1.0)
            
            logger.info(
                f"User {user_id} rapid checking: "
                f"anxiety↑ {state.anxiety_level:.2f}"
            )
        
        elif action_type == 'reject':
            # Rejection might indicate misalignment
            # Slight anxiety increase (worried about missing out)
            state.anxiety_level = min(state.anxiety_level + 0.03, 1.0)
        
        # Track interaction
        if not state.interaction_frequency:
            state.interaction_frequency = []
        
        state.interaction_frequency.append(datetime.utcnow().isoformat())
        
        # Keep only last 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)
        state.interaction_frequency = [
            t for t in state.interaction_frequency
            if datetime.fromisoformat(t) > cutoff
        ]
        
        # Update posting frequency
        self._update_posting_frequency(state)
        
        # Detect rapid checking pattern
        self._detect_rapid_checking(state)
        
        self.db.commit()
    
    def _update_posting_frequency(self, state: EmotionalState):
        """Update posting frequency counters"""
        
        # Count posts in last 7 and 30 days
        now = datetime.utcnow()
        cutoff_7d = now - timedelta(days=7)
        cutoff_30d = now - timedelta(days=30)
        
        # Query follow actions (actual posts)
        posts_7d = self.db.query(UserAction).filter(
            UserAction.user_id == state.user_id,
            UserAction.action_type == 'follow',
            UserAction.timestamp >= cutoff_7d
        ).count()
        
        posts_30d = self.db.query(UserAction).filter(
            UserAction.user_id == state.user_id,
            UserAction.action_type == 'follow',
            UserAction.timestamp >= cutoff_30d
        ).count()
        
        state.posts_last_7_days = posts_7d
        state.posts_last_30_days = posts_30d
        
        # Increase fatigue if posting too frequently
        if posts_7d >= 5:
            state.fatigue_level = min(state.fatigue_level + 0.1, 1.0)
            logger.info(
                f"User {state.user_id} posting frequently: "
                f"{posts_7d} posts in 7 days, fatigue↑"
            )
    
    def _detect_rapid_checking(self, state: EmotionalState):
        """Detect rapid checking pattern (anxiety signal)"""
        
        if len(state.interaction_frequency) < 3:
            return
        
        # Get last 3 interactions
        recent = sorted(state.interaction_frequency)[-3:]
        recent_times = [datetime.fromisoformat(t) for t in recent]
        
        # Check if all within 1 hour
        time_span = (recent_times[-1] - recent_times[0]).total_seconds() / 3600
        
        if time_span < 1.0:
            # Rapid checking detected
            state.rapid_check_count += 1
            state.anxiety_level = min(state.anxiety_level + 0.05, 1.0)
            
            logger.warning(
                f"Rapid checking detected for user {state.user_id}: "
                f"3 checks in {time_span:.1f} hours"
            )
    
    def should_suggest_rest(self, user_id: str) -> tuple[bool, str]:
        """
        Determine if user should rest today.
        
        Args:
            user_id: User ID
        
        Returns:
            (should_rest, reason)
        """
        state = self.get_or_create_state(user_id)
        
        # Check anxiety level
        if state.anxiety_level > 0.7:
            return True, "High anxiety detected from behavior patterns"
        
        # Check fatigue level
        if state.fatigue_level > 0.6:
            return True, "Fatigue signals detected"
        
        # Check posting frequency
        if state.posts_last_7_days >= 5:
            return True, f"You've posted {state.posts_last_7_days} times this week"
        
        # Check if it's their preferred rest day
        if state.preferred_rest_day is not None:
            today = datetime.utcnow().weekday()
            if today == state.preferred_rest_day:
                return True, "Your usual rest day"
        
        # Check time since last rest
        if state.last_rest_day:
            days_since_rest = (datetime.utcnow() - state.last_rest_day).days
            if days_since_rest > 10 and state.posts_last_7_days >= 3:
                return True, f"It's been {days_since_rest} days since your last rest"
        
        return False, ""
    
    def get_emotional_context(self, user_id: str) -> Dict:
        """
        Get emotional context for recommendation.
        
        Used by DecisionSynthesizer to adapt tone and recommendations.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with emotional context
        """
        state = self.get_or_create_state(user_id)
        
        # Determine overall state
        if state.anxiety_level > 0.6:
            overall_state = "anxious"
            tone = "extra_calm"
        elif state.fatigue_level > 0.5:
            overall_state = "fatigued"
            tone = "supportive"
        elif state.trust_level > 0.7:
            overall_state = "confident"
            tone = "encouraging"
        else:
            overall_state = "neutral"
            tone = "calm"
        
        # Generate reassurance message
        reassurance = self._generate_reassurance(state)
        
        return {
            'overall_state': overall_state,
            'tone': tone,
            'reassurance': reassurance,
            'anxiety_level': state.anxiety_level,
            'trust_level': state.trust_level,
            'fatigue_level': state.fatigue_level,
            'should_rest': state.should_suggest_rest()
        }
    
    def _generate_reassurance(self, state: EmotionalState) -> str:
        """Generate calm reassurance message based on state"""
        
        if state.anxiety_level > 0.7:
            return "You're doing fine. This is a suggestion, not a requirement."
        
        elif state.fatigue_level > 0.6:
            return "Rest is productive. Your audience will still be there tomorrow."
        
        elif state.trust_level > 0.7:
            return "You've been making good decisions. Trust your instinct."
        
        elif state.posts_last_7_days >= 5:
            return "You've been consistent this week. A rest day won't hurt."
        
        else:
            return "Take your time. Quality over quantity."
    
    def get_state_summary(self, user_id: str) -> Dict:
        """
        Get summary of emotional state.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with state summary
        """
        state = self.get_or_create_state(user_id)
        
        return {
            'user_id': user_id,
            'anxiety_level': state.anxiety_level,
            'trust_level': state.trust_level,
            'fatigue_level': state.fatigue_level,
            'posts_last_7_days': state.posts_last_7_days,
            'posts_last_30_days': state.posts_last_30_days,
            'rest_days_last_30': state.rest_days_last_30,
            'last_rest_day': state.last_rest_day.isoformat() if state.last_rest_day else None,
            'rapid_check_count': state.rapid_check_count,
            'interaction_count': len(state.interaction_frequency) if state.interaction_frequency else 0,
            'should_rest': state.should_suggest_rest(),
            'updated_at': state.updated_at.isoformat() if state.updated_at else None
        }
    
    def reset_rapid_check_counter(self, user_id: str):
        """Reset rapid check counter (call daily)"""
        state = self.get_or_create_state(user_id)
        state.rapid_check_count = 0
        self.db.commit()
    
    def decay_emotional_levels(self, user_id: str, decay_rate: float = 0.1):
        """
        Gradually decay emotional levels over time.
        
        Call this periodically (e.g., daily) to prevent levels from staying high forever.
        
        Args:
            user_id: User ID
            decay_rate: How much to decay (0-1)
        """
        state = self.get_or_create_state(user_id)
        
        # Decay anxiety and fatigue toward neutral
        state.anxiety_level = max(
            state.anxiety_level - decay_rate,
            0.3  # Neutral baseline
        )
        
        state.fatigue_level = max(
            state.fatigue_level - decay_rate,
            0.0
        )
        
        # Trust decays slower (builds over time)
        if state.trust_level > 0.5:
            state.trust_level = max(
                state.trust_level - (decay_rate * 0.5),
                0.5
            )
        
        self.db.commit()
        
        logger.info(
            f"Decayed emotional levels for user {user_id}: "
            f"anxiety={state.anxiety_level:.2f}, "
            f"fatigue={state.fatigue_level:.2f}, "
            f"trust={state.trust_level:.2f}"
        )
