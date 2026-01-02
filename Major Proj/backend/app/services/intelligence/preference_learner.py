"""
Preference Learner - Learns user preferences from behavior, not questions
"""
import logging
import uuid
from typing import Dict, Optional, List, Union
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from sqlalchemy.orm import Session

from app.models.user_action import UserAction

logger = logging.getLogger(__name__)


class PreferenceLearner:
    """
    Learns user preferences from actions, not explicit feedback.
    
    Philosophy:
    - NO surveys or questionnaires
    - Learn from behavior: select, reject, ignore, follow, rest
    - Vector-based preference updates (Spotify-style)
    - Continuous adaptation
    
    Actions and their meanings:
    - select: User chose this recommendation → pull preference toward
    - follow: User actually posted about it → strong pull toward
    - reject: User dismissed → push preference away
    - ignore: User saw but didn't act → slight push away
    - rest: User took rest day → no content update, but track pattern
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Learning rates by action type
        self.learning_rates = {
            'select': 0.3,    # Moderate pull
            'follow': 0.4,    # Strong pull (they actually did it)
            'reject': -0.2,   # Push away
            'ignore': -0.1,   # Slight push away
            'rest': 0.0       # No content preference update
        }
    
    def initialize_user(
        self,
        user_id: Union[str, uuid.UUID],
        initial_vector: np.ndarray
    ):
        """
        Initialize user preference vector.
        
        Args:
            user_id: User ID (string or UUID)
            initial_vector: Initial preference (usually from creator's own content)
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
        
        # Store as first action (special type: 'initialize')
        action = UserAction(
            user_id=user_uuid,
            action_type='initialize',
            timestamp=datetime.utcnow(),
            learning_weight=1.0,
            context={'source': 'onboarding'}
        )
        action.set_content_vector(initial_vector)
        
        self.db.add(action)
        self.db.commit()
        
        logger.info(f"Initialized preference vector for user {user_uuid}")
    
    def update_from_action(
        self,
        user_id: Union[str, uuid.UUID],
        action_type: str,
        content_vector: np.ndarray,
        context: Dict = None
    ):
        """
        Update user preferences based on an action.
        
        Args:
            user_id: User ID (string or UUID)
            action_type: 'select', 'reject', 'ignore', 'follow', 'rest'
            content_vector: Vector of content acted upon
            context: Optional context metadata
        """
        # Validate action type
        if action_type not in self.learning_rates:
            logger.warning(f"Unknown action type: {action_type}")
            return
        
        # Convert string user_id to UUID if needed
        if isinstance(user_id, str):
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                # If not a valid UUID string, generate a UUID from the string
                user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
        else:
            user_uuid = user_id
        
        # Record action
        action = UserAction(
            user_id=user_uuid,
            action_type=action_type,
            timestamp=datetime.utcnow(),
            learning_weight=abs(self.learning_rates[action_type]),
            context=context or {}
        )
        action.set_content_vector(content_vector)
        
        self.db.add(action)
        self.db.commit()
        
        logger.info(
            f"Recorded {action_type} action for user {user_uuid} "
            f"(weight: {action.learning_weight})"
        )
    
    def get_preference_vector(self, user_id: str) -> Optional[np.ndarray]:
        """
        Get current preference vector for user.
        
        Calculated by applying all actions to initial vector.
        
        Args:
            user_id: User ID
        
        Returns:
            Current preference vector or None if no actions
        """
        # Get all actions for user, ordered by time
        actions = self.db.query(UserAction).filter_by(
            user_id=user_id
        ).order_by(UserAction.timestamp).all()
        
        if not actions:
            logger.warning(f"No actions found for user {user_id}")
            return None
        
        # Start with initialization vector
        init_action = next((a for a in actions if a.action_type == 'initialize'), None)
        
        if not init_action:
            logger.warning(f"No initialization vector for user {user_id}")
            return None
        
        current_vector = init_action.get_content_vector().copy()
        
        # Apply each action sequentially
        for action in actions:
            if action.action_type == 'initialize':
                continue  # Already used
            
            content_vec = action.get_content_vector()
            if content_vec is None:
                continue
            
            alpha = self.learning_rates.get(action.action_type, 0.0)
            
            if alpha > 0:
                # Pull toward
                current_vector = (
                    (1 - alpha) * current_vector +
                    alpha * content_vec
                )
            elif alpha < 0:
                # Push away
                diff = content_vec - current_vector
                current_vector = current_vector - abs(alpha) * diff
            
            # Normalize to prevent drift
            norm = np.linalg.norm(current_vector)
            if norm > 0:
                current_vector = current_vector / norm
        
        return current_vector
    
    def infer_rest_patterns(self, user_id: str) -> Dict:
        """
        Infer when user tends to rest.
        
        Args:
            user_id: User ID
        
        Returns:
            {
                'confidence': 'low' | 'medium' | 'high',
                'pattern': 'weekly' | 'biweekly' | None,
                'preferred_day': 0-6 (Monday-Sunday) or None,
                'frequency': float (rest days per week)
            }
        """
        # Get rest actions from last 60 days
        cutoff = datetime.utcnow() - timedelta(days=60)
        
        rest_actions = self.db.query(UserAction).filter(
            UserAction.user_id == user_id,
            UserAction.action_type == 'rest',
            UserAction.timestamp >= cutoff
        ).all()
        
        if len(rest_actions) < 2:
            return {
                'confidence': 'low',
                'pattern': None,
                'preferred_day': None,
                'frequency': 0.0
            }
        
        # Analyze rest day patterns
        rest_weekdays = [a.timestamp.weekday() for a in rest_actions]
        weekday_counts = Counter(rest_weekdays)
        
        # Calculate frequency
        days_tracked = (datetime.utcnow() - cutoff).days
        weeks_tracked = days_tracked / 7
        frequency = len(rest_actions) / weeks_tracked if weeks_tracked > 0 else 0
        
        # Find most common day
        if weekday_counts:
            most_common_day, count = weekday_counts.most_common(1)[0]
            
            # Check if there's a clear pattern
            if count >= 3 and count / len(rest_actions) > 0.4:
                # Strong weekly pattern
                return {
                    'confidence': 'high' if count >= 5 else 'medium',
                    'pattern': 'weekly',
                    'preferred_day': most_common_day,
                    'frequency': frequency
                }
        
        return {
            'confidence': 'low',
            'pattern': None,
            'preferred_day': None,
            'frequency': frequency
        }
    
    def get_action_statistics(self, user_id: str) -> Dict:
        """
        Get statistics about user actions.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with action counts and patterns
        """
        # Get all actions
        actions = self.db.query(UserAction).filter_by(
            user_id=user_id
        ).all()
        
        if not actions:
            return {
                'total_actions': 0,
                'by_type': {},
                'first_action': None,
                'last_action': None
            }
        
        # Count by type
        action_counts = Counter(a.action_type for a in actions)
        
        # Calculate ratios
        total = len(actions)
        follow_rate = action_counts.get('follow', 0) / total if total > 0 else 0
        reject_rate = action_counts.get('reject', 0) / total if total > 0 else 0
        
        return {
            'total_actions': total,
            'by_type': dict(action_counts),
            'first_action': actions[0].timestamp.isoformat(),
            'last_action': actions[-1].timestamp.isoformat(),
            'follow_rate': follow_rate,
            'reject_rate': reject_rate,
            'engagement_score': follow_rate - (reject_rate * 0.5)  # Simple score
        }
    
    def get_preference_stability(self, user_id: str) -> float:
        """
        Calculate how stable user's preferences are.
        
        Low stability = preferences changing rapidly
        High stability = consistent preferences
        
        Args:
            user_id: User ID
        
        Returns:
            Stability score (0-1)
        """
        # Get recent actions (last 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        recent_actions = self.db.query(UserAction).filter(
            UserAction.user_id == user_id,
            UserAction.timestamp >= cutoff,
            UserAction.action_type.in_(['select', 'follow', 'reject'])
        ).order_by(UserAction.timestamp).all()
        
        if len(recent_actions) < 5:
            return 0.5  # Not enough data
        
        # Calculate preference vectors at different time points
        vectors = []
        window_size = max(3, len(recent_actions) // 5)
        
        for i in range(0, len(recent_actions) - window_size, window_size):
            window_actions = recent_actions[i:i+window_size]
            
            # Calculate average vector for this window
            positive_vecs = [
                a.get_content_vector()
                for a in window_actions
                if a.action_type in ['select', 'follow'] and a.get_content_vector() is not None
            ]
            
            if positive_vecs:
                avg_vec = np.mean(positive_vecs, axis=0)
                vectors.append(avg_vec)
        
        if len(vectors) < 2:
            return 0.5
        
        # Calculate similarity between consecutive windows
        similarities = []
        for i in range(len(vectors) - 1):
            sim = self._cosine_similarity(vectors[i], vectors[i+1])
            similarities.append(sim)
        
        # Average similarity = stability
        stability = np.mean(similarities) if similarities else 0.5
        
        return float(stability)
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        dot_product = np.dot(v1, v2)
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        
        if norm_product == 0:
            return 0.0
        
        return float(dot_product / norm_product)
    
    def get_recent_interests(
        self,
        user_id: str,
        days: int = 14,
        limit: int = 5
    ) -> List[Dict]:
        """
        Get user's recent interests based on followed recommendations.
        
        Args:
            user_id: User ID
            days: Look back period
            limit: Max interests to return
        
        Returns:
            List of interest dicts with vectors and context
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        followed_actions = self.db.query(UserAction).filter(
            UserAction.user_id == user_id,
            UserAction.action_type == 'follow',
            UserAction.timestamp >= cutoff
        ).order_by(UserAction.timestamp.desc()).limit(limit).all()
        
        interests = []
        for action in followed_actions:
            vec = action.get_content_vector()
            if vec is not None:
                interests.append({
                    'vector': vec,
                    'timestamp': action.timestamp.isoformat(),
                    'context': action.context
                })
        
        return interests
