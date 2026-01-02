"""
Decision Synthesizer - Generates ONE calm daily decision
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import numpy as np

from app.services.signals.abstract_signal import DailyDecision, Opportunity, CreatorEmbedding
from app.services.intelligence.emotional_tracker import EmotionalStateTracker
from app.services.intelligence.preference_learner import PreferenceLearner
from app.services.intelligence.opportunity_detector import OpportunityDetector
from app.services.intelligence.competitor_discovery import CompetitorProfile

logger = logging.getLogger(__name__)


class DecisionSynthesizer:
    """
    Synthesizes ONE calm daily decision from opportunities and emotional context.
    
    Philosophy:
    - ONE clear recommendation per day
    - Rest is a valid action
    - Calm, non-hyped language
    - Emotional safety first
    - Conservative over aggressive
    - Explain uncertainty honestly
    
    Decision types:
    - post: Clear opportunity, good timing, creator ready
    - rest: Creator needs break, or no strong signals
    - observe: Signals present but unclear, watch and wait
    """
    
    def __init__(
        self,
        emotional_tracker: EmotionalStateTracker,
        preference_learner: PreferenceLearner,
        opportunity_detector: OpportunityDetector
    ):
        self.emotional_tracker = emotional_tracker
        self.preference_learner = preference_learner
        self.opportunity_detector = opportunity_detector
    
    def synthesize_daily_decision(
        self,
        user_id: str,
        creator_embedding: CreatorEmbedding,
        competitors: List[CompetitorProfile]
    ) -> DailyDecision:
        """
        Generate ONE calm daily decision.
        
        Args:
            user_id: User ID
            creator_embedding: Creator's content representation
            competitors: List of competitors
        
        Returns:
            DailyDecision
        """
        logger.info(f"Synthesizing daily decision for user {user_id}")
        
        # 1. Check emotional state first
        emotional_context = self.emotional_tracker.get_emotional_context(user_id)
        
        # 2. Check if user should rest
        should_rest, rest_reason = self.emotional_tracker.should_suggest_rest(user_id)
        
        if should_rest:
            return self._create_rest_decision(
                emotional_context,
                rest_reason
            )
        
        # 3. Get user preferences
        preference_vector = self.preference_learner.get_preference_vector(user_id)
        
        # 4. Detect opportunities
        opportunities = self.opportunity_detector.detect_opportunities(
            creator_embedding=creator_embedding,
            competitors=competitors,
            user_preference_vector=preference_vector,
            max_opportunities=20
        )
        
        if not opportunities:
            return self._create_observe_decision(
                emotional_context,
                "No strong signals detected today"
            )
        
        # 5. Filter by vibe (avoid controversy)
        opportunities = self.opportunity_detector.filter_by_vibe(
            opportunities,
            avoid_controversy=True
        )
        
        # 6. Get best opportunity
        best_opportunity = opportunities[0] if opportunities else None
        
        if not best_opportunity:
            return self._create_observe_decision(
                emotional_context,
                "Signals present but unclear"
            )
        
        # 7. Get anti-trends
        anti_trends = self.opportunity_detector.get_anti_trends(
            opportunities,
            limit=3
        )
        
        # 8. Determine action based on best opportunity
        if best_opportunity.recommendation_type == 'post':
            return self._create_post_decision(
                best_opportunity,
                opportunities[1:4],  # Alternatives
                anti_trends,
                emotional_context
            )
        elif best_opportunity.recommendation_type == 'consider':
            return self._create_observe_decision(
                emotional_context,
                "Signals are present but not overwhelming",
                best_opportunity
            )
        else:
            return self._create_observe_decision(
                emotional_context,
                "No clear opportunities today"
            )
    
    def _create_post_decision(
        self,
        opportunity: Opportunity,
        alternatives: List[Opportunity],
        anti_trends: List[Opportunity],
        emotional_context: Dict
    ) -> DailyDecision:
        """Create a 'post' decision"""
        
        signal = opportunity.signal
        
        # Generate calm explanation
        explanation = self._generate_calm_explanation(
            opportunity,
            emotional_context
        )
        
        # Timing context
        timing = {
            'lifecycle_phase': signal.lifecycle_phase,
            'momentum': float(signal.momentum),
            'saturation': float(signal.saturation),
            'best_time': 'soon',  # Could be more sophisticated
            'urgency': 'low' if signal.lifecycle_phase == 'emerging' else 'medium'
        }
        
        # Format alternatives
        alt_list = [
            {
                'topic': alt.signal.representative_text,
                'score': float(alt.total_score),
                'phase': alt.signal.lifecycle_phase
            }
            for alt in alternatives
        ]
        
        # Format avoid list
        avoid_list = [
            {
                'topic': anti.signal.representative_text,
                'reason': self._get_avoid_reason(anti.signal),
                'saturation': float(anti.signal.saturation)
            }
            for anti in anti_trends
        ]
        
        return DailyDecision(
            action='post',
            topic=signal.representative_text,
            confidence=opportunity.total_score,
            explanation=explanation,
            timing=timing,
            alternatives=alt_list,
            avoid=avoid_list,
            emotional_context={
                'tone': emotional_context['tone'],
                'reassurance': emotional_context['reassurance']
            },
            metadata={
                'opportunity_scores': {
                    'timing': float(opportunity.timing_score),
                    'differentiation': float(opportunity.differentiation_score),
                    'alignment': float(opportunity.alignment_score),
                    'preference': float(opportunity.preference_score),
                    'confidence': float(opportunity.confidence_score)
                },
                'signal_sources': signal.source_platforms,
                'vibe': signal.vibe,
                'vibe_confidence': float(signal.vibe_confidence)
            }
        )
    
    def _create_rest_decision(
        self,
        emotional_context: Dict,
        reason: str
    ) -> DailyDecision:
        """Create a 'rest' decision"""
        
        # Generate supportive explanation
        explanation = self._generate_rest_explanation(
            emotional_context,
            reason
        )
        
        return DailyDecision(
            action='rest',
            topic=None,
            confidence=1.0,  # High confidence in rest recommendation
            explanation=explanation,
            emotional_context={
                'tone': 'supportive',
                'reassurance': emotional_context.get('reassurance', 'Rest is productive')
            },
            metadata={
                'rest_reason': reason,
                'anxiety_level': emotional_context.get('anxiety_level', 0),
                'fatigue_level': emotional_context.get('fatigue_level', 0)
            }
        )
    
    def _create_observe_decision(
        self,
        emotional_context: Dict,
        reason: str,
        best_opportunity: Optional[Opportunity] = None
    ) -> DailyDecision:
        """Create an 'observe' decision"""
        
        explanation = self._generate_observe_explanation(
            emotional_context,
            reason,
            best_opportunity
        )
        
        metadata = {
            'observe_reason': reason
        }
        
        if best_opportunity:
            metadata['watching_topic'] = best_opportunity.signal.representative_text
            metadata['watching_score'] = float(best_opportunity.total_score)
        
        return DailyDecision(
            action='observe',
            topic=best_opportunity.signal.representative_text if best_opportunity else None,
            confidence=0.5,
            explanation=explanation,
            emotional_context={
                'tone': emotional_context['tone'],
                'reassurance': 'Patience is a strategy'
            },
            metadata=metadata
        )
    
    def _generate_calm_explanation(
        self,
        opportunity: Opportunity,
        emotional_context: Dict
    ) -> str:
        """
        Generate calm, non-hyped explanation.
        
        Rules:
        - Reference signals, not algorithms
        - Acknowledge uncertainty
        - No pressure language
        - Supportive tone
        """
        signal = opportunity.signal
        
        parts = []
        
        # Opening (based on emotional state)
        if emotional_context['overall_state'] == 'anxious':
            parts.append("Here's what the data suggests, calmly:")
        elif emotional_context['overall_state'] == 'confident':
            parts.append("Based on current signals:")
        else:
            parts.append("Today's observation:")
        
        # Topic introduction
        parts.append(f"\n\n**{signal.representative_text}** appears to be {signal.lifecycle_phase}.")
        
        # Signal context
        signal_context = signal.get_explanation_context()
        if signal_context:
            parts.append(signal_context)
        
        # Differentiation
        if opportunity.differentiation_score > 0.6:
            parts.append("Your competitors aren't covering this angle yet.")
        elif opportunity.differentiation_score > 0.4:
            parts.append("Some competitors are touching on this, but there's room for your perspective.")
        
        # Confidence acknowledgment
        if opportunity.total_score < 0.8:
            parts.append(
                f"\n\nConfidence is moderate ({opportunity.total_score:.0%}). "
                "Signals are present but not overwhelming."
            )
        else:
            parts.append(
                f"\n\nConfidence is {opportunity.total_score:.0%}. "
                "Multiple signals align."
            )
        
        # Reassurance
        parts.append(f"\n\n{emotional_context['reassurance']}")
        
        return " ".join(parts)
    
    def _generate_rest_explanation(
        self,
        emotional_context: Dict,
        reason: str
    ) -> str:
        """Generate supportive rest explanation"""
        
        parts = []
        
        parts.append("**Suggestion: Rest today.**")
        parts.append(f"\n\n{reason}.")
        
        # Add context
        if 'anxiety' in reason.lower():
            parts.append(
                "\n\nYour interaction patterns suggest you might benefit from a break. "
                "This isn't a failure—it's strategic pacing."
            )
        elif 'fatigue' in reason.lower():
            parts.append(
                "\n\nConsistent output is valuable, but so is recovery. "
                "Your audience will still be there tomorrow."
            )
        elif 'posted' in reason.lower():
            parts.append(
                "\n\nYou've been active this week. "
                "Quality and sustainability matter more than frequency."
            )
        
        parts.append(f"\n\n{emotional_context.get('reassurance', 'Rest is productive.')}")
        
        return " ".join(parts)
    
    def _generate_observe_explanation(
        self,
        emotional_context: Dict,
        reason: str,
        best_opportunity: Optional[Opportunity]
    ) -> str:
        """Generate calm observe explanation"""
        
        parts = []
        
        parts.append("**Suggestion: Observe today.**")
        parts.append(f"\n\n{reason}.")
        
        if best_opportunity:
            signal = best_opportunity.signal
            parts.append(
                f"\n\nThere's some movement around **{signal.representative_text}**, "
                f"but it's in the {signal.lifecycle_phase} phase. "
                "Worth watching, not urgent."
            )
        
        parts.append(
            "\n\nNot every day needs a post. "
            "Sometimes the best move is to watch and wait."
        )
        
        parts.append(f"\n\n{emotional_context.get('reassurance', 'Patience is a strategy.')}")
        
        return " ".join(parts)
    
    def _get_avoid_reason(self, signal) -> str:
        """Get reason to avoid a topic"""
        
        if signal.lifecycle_phase == 'saturated':
            return "Appears overcrowded"
        elif signal.lifecycle_phase == 'declining':
            return "Interest is fading"
        elif signal.saturation > 0.7:
            return f"High saturation ({signal.saturation:.0%})"
        else:
            return "Timing unclear"
