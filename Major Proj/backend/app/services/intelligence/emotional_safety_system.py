"""
Emotional Safety System

FIRST PRINCIPLE: Reduce anxiety, not maximize output.
SECOND PRINCIPLE: Rest is a valid recommendation.
THIRD PRINCIPLE: Never pressure, never shame.
"""

import logging
from typing import Dict, Optional, Literal
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from sqlalchemy.orm import Session

from app.models.user_action import UserAction
from app.models.recommendation import Recommendation
from app.services.intelligence.emotional_tracker import EmotionalStateTracker

logger = logging.getLogger(__name__)


@dataclass
class SafetyGate:
    """Represents a safety check that blocks recommendations"""
    triggered: bool
    rule_name: str
    severity: Literal["info", "warning", "critical"]
    explanation: str
    recommended_action: Literal["rest", "observe", "proceed_caution"]


class EmotionalSafetySystem:
    """
    Enforces emotional safety rules before generating recommendations.
    
    This system can VETO recommendations if creator wellbeing is at risk.
    """
    
    # Safety thresholds (conservative by design)
    BURNOUT_THRESHOLD = 0.7  # Emotional state score
    MAX_CONSECUTIVE_POSTS = 7  # Days
    MIN_REST_DAYS_PER_MONTH = 4  # Required rest days
    ENGAGEMENT_DROP_THRESHOLD = -0.3  # 30% drop = warning
    
    def __init__(
        self,
        db: Session,
        emotional_tracker: EmotionalStateTracker
    ):
        self.db = db
        self.emotional_tracker = emotional_tracker
    
    def check_safety_gates(
        self,
        user_id: str,
        proposed_action: Literal["post", "engage", "observe"]
    ) -> Dict:
        """
        Check all safety gates before allowing recommendation.
        
        Returns:
            {
                "safe": bool,
                "gates_triggered": List[SafetyGate],
                "override_action": Optional[str],  # If unsafe
                "explanation": str
            }
        """
        logger.info(f"Checking safety gates for user {user_id}, proposed action: {proposed_action}")
        
        gates_triggered = []
        
        # Gate 1: Burnout Protection (CRITICAL)
        burnout_gate = self._check_burnout(user_id)
        if burnout_gate.triggered:
            gates_triggered.append(burnout_gate)
        
        # Gate 2: Streak Breaking (WARNING)
        streak_gate = self._check_posting_streak(user_id)
        if streak_gate.triggered:
            gates_triggered.append(streak_gate)
        
        # Gate 3: Engagement Drop (WARNING)
        engagement_gate = self._check_engagement_trend(user_id)
        if engagement_gate.triggered:
            gates_triggered.append(engagement_gate)
        
        # Gate 4: Rest Day Quota (INFO)
        rest_gate = self._check_rest_quota(user_id)
        if rest_gate.triggered:
            gates_triggered.append(rest_gate)
        
        # Gate 5: Time of Day (INFO)
        time_gate = self._check_time_appropriateness(user_id)
        if time_gate.triggered:
            gates_triggered.append(time_gate)
        
        # Determine if safe
        critical_gates = [g for g in gates_triggered if g.severity == "critical"]
        warning_gates = [g for g in gates_triggered if g.severity == "warning"]
        
        if critical_gates:
            # CRITICAL gates = force rest
            return {
                "safe": False,
                "gates_triggered": gates_triggered,
                "override_action": "rest",
                "explanation": self._generate_rest_explanation(critical_gates),
                "severity": "critical"
            }
        elif len(warning_gates) >= 2:
            # Multiple warnings = suggest observe
            return {
                "safe": False,
                "gates_triggered": gates_triggered,
                "override_action": "observe",
                "explanation": self._generate_observe_explanation(warning_gates),
                "severity": "warning"
            }
        elif warning_gates:
            # Single warning = proceed with caution
            return {
                "safe": True,
                "gates_triggered": gates_triggered,
                "override_action": None,
                "explanation": self._generate_caution_explanation(warning_gates),
                "severity": "warning"
            }
        else:
            # All clear
            return {
                "safe": True,
                "gates_triggered": gates_triggered,
                "override_action": None,
                "explanation": "All safety checks passed.",
                "severity": "info"
            }
    
    def _check_burnout(self, user_id: str) -> SafetyGate:
        """
        Check if creator shows signs of burnout.
        
        CRITICAL gate - overrides all other considerations.
        """
        emotional_state = self.emotional_tracker.get_current_state(user_id)
        
        if emotional_state.burnout_risk > self.BURNOUT_THRESHOLD:
            return SafetyGate(
                triggered=True,
                rule_name="burnout_protection",
                severity="critical",
                explanation=f"Your posting frequency and engagement patterns suggest you need a break. Burnout risk: {emotional_state.burnout_risk:.0%}",
                recommended_action="rest"
            )
        
        return SafetyGate(
            triggered=False,
            rule_name="burnout_protection",
            severity="critical",
            explanation="No burnout detected.",
            recommended_action="proceed_caution"
        )
    
    def _check_posting_streak(self, user_id: str) -> SafetyGate:
        """
        Check if creator has been posting too frequently without breaks.
        """
        # Get recent recommendations that were followed
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_posts = self.db.query(UserAction).filter(
            UserAction.user_id == user_id,
            UserAction.action_type == "followed",
            UserAction.timestamp >= thirty_days_ago
        ).order_by(UserAction.timestamp.desc()).all()
        
        if not recent_posts:
            return SafetyGate(
                triggered=False,
                rule_name="streak_breaking",
                severity="warning",
                explanation="No recent posting pattern detected.",
                recommended_action="proceed_caution"
            )
        
        # Calculate consecutive days
        post_dates = [action.timestamp.date() for action in recent_posts]
        post_dates = sorted(set(post_dates), reverse=True)
        
        consecutive_days = 1
        for i in range(len(post_dates) - 1):
            if (post_dates[i] - post_dates[i+1]).days == 1:
                consecutive_days += 1
            else:
                break
        
        if consecutive_days >= self.MAX_CONSECUTIVE_POSTS:
            return SafetyGate(
                triggered=True,
                rule_name="streak_breaking",
                severity="warning",
                explanation=f"You've posted {consecutive_days} days in a row. Taking a day off helps maintain quality and prevents audience fatigue.",
                recommended_action="rest"
            )
        
        return SafetyGate(
            triggered=False,
            rule_name="streak_breaking",
            severity="warning",
            explanation=f"Healthy posting pattern ({consecutive_days} consecutive days).",
            recommended_action="proceed_caution"
        )
    
    def _check_engagement_trend(self, user_id: str) -> SafetyGate:
        """
        Check if engagement has been dropping.
        
        Dropping engagement often means creator needs to reassess strategy.
        """
        emotional_state = self.emotional_tracker.get_current_state(user_id)
        
        if emotional_state.recent_engagement_trend < self.ENGAGEMENT_DROP_THRESHOLD:
            return SafetyGate(
                triggered=True,
                rule_name="engagement_trend",
                severity="warning",
                explanation=f"Your engagement has dropped by {abs(emotional_state.recent_engagement_trend):.0%}. Consider observing your audience and adjusting your approach before posting more.",
                recommended_action="observe"
            )
        
        return SafetyGate(
            triggered=False,
            rule_name="engagement_trend",
            severity="warning",
            explanation="Engagement trend is healthy.",
            recommended_action="proceed_caution"
        )
    
    def _check_rest_quota(self, user_id: str) -> SafetyGate:
        """
        Check if creator is taking enough rest days.
        
        Creators need breaks to stay creative and avoid burnout.
        """
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Count days with NO action
        all_days = set()
        action_days = set()
        
        actions = self.db.query(UserAction).filter(
            UserAction.user_id == user_id,
            UserAction.timestamp >= thirty_days_ago
        ).all()
        
        for action in actions:
            action_days.add(action.timestamp.date())
        
        # Generate all days in range
        current_date = thirty_days_ago.date()
        end_date = datetime.utcnow().date()
        while current_date <= end_date:
            all_days.add(current_date)
            current_date += timedelta(days=1)
        
        rest_days = len(all_days - action_days)
        
        if rest_days < self.MIN_REST_DAYS_PER_MONTH:
            return SafetyGate(
                triggered=True,
                rule_name="rest_quota",
                severity="info",
                explanation=f"You've only rested {rest_days} days this month. Consider taking more breaks to stay creative.",
                recommended_action="rest"
            )
        
        return SafetyGate(
            triggered=False,
            rule_name="rest_quota",
            severity="info",
            explanation=f"Good balance of activity and rest ({rest_days} rest days).",
            recommended_action="proceed_caution"
        )
    
    def _check_time_appropriateness(self, user_id: str) -> SafetyGate:
        """
        Check if current time matches user's typical pattern.
        
        If user usually posts in morning but it's night, suggest waiting.
        """
        # Get user's typical posting hours
        recent_actions = self.db.query(UserAction).filter(
            UserAction.user_id == user_id,
            UserAction.action_type.in_(["followed", "accepted"])
        ).order_by(UserAction.timestamp.desc()).limit(30).all()
        
        if len(recent_actions) < 5:
            return SafetyGate(
                triggered=False,
                rule_name="time_appropriateness",
                severity="info",
                explanation="Not enough data to determine time preferences.",
                recommended_action="proceed_caution"
            )
        
        # Calculate typical hours
        typical_hours = [action.timestamp.hour for action in recent_actions]
        avg_hour = np.mean(typical_hours)
        current_hour = datetime.utcnow().hour
        
        # Check if current time is significantly different
        hour_diff = abs(current_hour - avg_hour)
        if hour_diff > 6:  # More than 6 hours off
            return SafetyGate(
                triggered=True,
                rule_name="time_appropriateness",
                severity="info",
                explanation=f"You usually engage around {int(avg_hour):02d}:00. Consider checking back then for better context.",
                recommended_action="observe"
            )
        
        return SafetyGate(
            triggered=False,
            rule_name="time_appropriateness",
            severity="info",
            explanation="Current time aligns with your patterns.",
            recommended_action="proceed_caution"
        )
    
    def _generate_rest_explanation(self, gates: list[SafetyGate]) -> str:
        """Generate calm explanation for why rest is needed"""
        
        explanations = [gate.explanation for gate in gates]
        
        intro = "We recommend taking a day off today. Here's why:\n\n"
        body = "\n\n".join(f"• {exp}" for exp in explanations)
        outro = "\n\nRest is productive. It helps you:\n• Maintain creative energy\n• Avoid audience fatigue\n• Return with better ideas\n• Protect long-term sustainability"
        
        return intro + body + outro
    
    def _generate_observe_explanation(self, gates: list[SafetyGate]) -> str:
        """Generate explanation for observe day"""
        
        explanations = [gate.explanation for gate in gates]
        
        intro = "Today is a good day to observe rather than post. Here's what we're seeing:\n\n"
        body = "\n\n".join(f"• {exp}" for exp in explanations)
        outro = "\n\nUse today to:\n• Study audience reactions\n• Analyze what's working\n• Plan your next move\n• Build strategy, not just content"
        
        return intro + body + outro
    
    def _generate_caution_explanation(self, gates: list[SafetyGate]) -> str:
        """Generate cautionary note"""
        
        explanations = [gate.explanation for gate in gates]
        
        intro = "You can proceed, but keep these in mind:\n\n"
        body = "\n\n".join(f"• {exp}" for exp in explanations)
        
        return intro + body
