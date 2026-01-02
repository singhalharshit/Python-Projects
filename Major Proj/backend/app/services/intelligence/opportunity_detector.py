"""
Opportunity Detector - Find content opportunities with scoring
"""
import logging
from typing import List, Optional
import numpy as np

from app.services.signals.abstract_signal import AbstractSignal, Opportunity, CreatorEmbedding
from app.services.signals.live_signal_collector import LiveSignalCollector
from app.services.intelligence.competitor_discovery import CompetitorDiscoveryEngine, CompetitorProfile

logger = logging.getLogger(__name__)


class OpportunityDetector:
    """
    Detects content opportunities by analyzing signals, competitors, and preferences.
    
    Philosophy:
    - Opportunities = right timing + differentiation + alignment
    - Conservative thresholds (better to miss than recommend bad)
    - Multi-factor scoring
    - Lifecycle-aware (emerging > saturated)
    
    Scoring factors:
    1. Timing (lifecycle phase) - 30%
    2. Differentiation (competitor gap) - 25%
    3. Alignment (fits creator style) - 20%
    4. Preference (user interest) - 15%
    5. Confidence (signal quality) - 10%
    """
    
    def __init__(
        self,
        signal_collector: LiveSignalCollector,
        competitor_engine: CompetitorDiscoveryEngine
    ):
        self.signal_collector = signal_collector
        self.competitor_engine = competitor_engine
        
        # Scoring weights
        self.weights = {
            'timing': 0.30,
            'differentiation': 0.25,
            'alignment': 0.20,
            'preference': 0.15,
            'confidence': 0.10
        }
    
    def detect_opportunities(
        self,
        creator_embedding: CreatorEmbedding,
        competitors: List[CompetitorProfile],
        user_preference_vector: Optional[np.ndarray] = None,
        max_opportunities: int = 20
    ) -> List[Opportunity]:
        """
        Find content opportunities for this creator.
        
        Args:
            creator_embedding: Creator's content representation
            competitors: List of competitors
            user_preference_vector: Learned preference vector (optional)
            max_opportunities: Maximum opportunities to return
        
        Returns:
            Ranked list of Opportunities
        """
        logger.info(
            f"Detecting opportunities for {creator_embedding.creator_id} "
            f"with {len(competitors)} competitors"
        )
        
        # 1. Collect live signals in creator's content space
        signals = self.signal_collector.collect_signals(
            search_space=creator_embedding.theme,
            radius=0.4,  # Explore nearby topics
            max_signals=50
        )
        
        if not signals:
            logger.warning("No signals collected")
            return []
        
        logger.info(f"Collected {len(signals)} signals")
        
        # 2. Evaluate each signal as an opportunity
        opportunities = []
        for signal in signals:
            opportunity = self._evaluate_opportunity(
                signal,
                creator_embedding,
                competitors,
                user_preference_vector
            )
            opportunities.append(opportunity)
        
        # 3. Sort by total score
        opportunities.sort(key=lambda o: o.total_score, reverse=True)
        
        # 4. Log top opportunities
        for i, opp in enumerate(opportunities[:5], 1):
            logger.info(
                f"#{i} Opportunity: {opp.signal.representative_text} "
                f"(score: {opp.total_score:.2f}, "
                f"type: {opp.recommendation_type}, "
                f"phase: {opp.signal.lifecycle_phase})"
            )
        
        return opportunities[:max_opportunities]
    
    def _evaluate_opportunity(
        self,
        signal: AbstractSignal,
        creator_embedding: CreatorEmbedding,
        competitors: List[CompetitorProfile],
        user_preference_vector: Optional[np.ndarray]
    ) -> Opportunity:
        """
        Evaluate a single signal as an opportunity.
        
        Returns:
            Opportunity with all scoring components
        """
        # 1. TIMING SCORE (lifecycle phase quality)
        timing_score = self._score_timing(signal)
        
        # 2. DIFFERENTIATION SCORE (competitor gap)
        diff_score = self._score_differentiation(signal, competitors)
        
        # 3. ALIGNMENT SCORE (fits creator's style)
        alignment_score = self._cosine_similarity(
            signal.content_vector,
            creator_embedding.theme
        )
        
        # 4. PREFERENCE SCORE (user has shown interest)
        if user_preference_vector is not None:
            preference_score = self._cosine_similarity(
                signal.content_vector,
                user_preference_vector
            )
        else:
            preference_score = 0.5  # Neutral if no preference data
        
        # 5. CONFIDENCE SCORE (signal quality)
        confidence_score = signal.confidence
        
        # Calculate total score (weighted combination)
        total_score = (
            timing_score * self.weights['timing'] +
            diff_score * self.weights['differentiation'] +
            alignment_score * self.weights['alignment'] +
            preference_score * self.weights['preference'] +
            confidence_score * self.weights['confidence']
        )
        
        # Determine recommendation type
        recommendation_type = self._determine_recommendation_type(
            signal,
            total_score
        )
        
        return Opportunity(
            signal=signal,
            timing_score=timing_score,
            differentiation_score=diff_score,
            alignment_score=alignment_score,
            preference_score=preference_score,
            confidence_score=confidence_score,
            total_score=total_score,
            recommendation_type=recommendation_type
        )
    
    def _score_timing(self, signal: AbstractSignal) -> float:
        """
        Score based on lifecycle phase.
        
        Best: emerging or early accelerating
        Worst: saturated or declining
        
        Returns:
            Timing score (0-1)
        """
        phase_scores = {
            'emerging': 1.0,      # Perfect timing
            'accelerating': 0.8,  # Good timing
            'peak': 0.6,          # Okay timing
            'stable': 0.5,        # Neutral
            'saturated': 0.2,     # Bad timing
            'declining': 0.1      # Very bad timing
        }
        
        base_score = phase_scores.get(signal.lifecycle_phase, 0.5)
        
        # Boost for high momentum + low saturation
        if signal.momentum > 0.7 and signal.saturation < 0.3:
            base_score *= 1.2
        
        # Penalize high saturation
        if signal.saturation > 0.7:
            base_score *= 0.5
        
        # Penalize high noise
        if signal.noise_level > 0.5:
            base_score *= 0.8
        
        return min(base_score, 1.0)
    
    def _score_differentiation(
        self,
        signal: AbstractSignal,
        competitors: List[CompetitorProfile]
    ) -> float:
        """
        Score based on competitor coverage.
        
        High score = competitors aren't covering this yet (blue ocean)
        Low score = competitors are all over this (red ocean)
        
        Returns:
            Differentiation score (0-1)
        """
        if not competitors:
            return 0.7  # Neutral if no competitors
        
        # Get gap analysis
        gap_analysis = self.competitor_engine.get_competitor_gap_analysis(
            creator_embedding=None,  # Not needed for this call
            competitors=competitors,
            topic_vector=signal.content_vector
        )
        
        # Gap score is already 0-1 (1 = big gap, 0 = no gap)
        gap_score = gap_analysis['gap_score']
        
        # Boost if very few competitors covering
        if gap_analysis['coverage_ratio'] < 0.2:
            gap_score *= 1.2
        
        return min(gap_score, 1.0)
    
    def _determine_recommendation_type(
        self,
        signal: AbstractSignal,
        total_score: float
    ) -> str:
        """
        Determine what to recommend.
        
        Returns:
            'post', 'consider', 'observe', or 'avoid'
        """
        # Check for anti-trends first
        if signal.is_anti_trend():
            return 'avoid'
        
        # Check lifecycle
        if signal.lifecycle_phase in ['saturated', 'declining']:
            return 'avoid'
        
        # Check total score
        if total_score >= 0.7 and signal.lifecycle_phase in ['emerging', 'accelerating']:
            return 'post'
        elif total_score >= 0.5:
            return 'consider'
        elif total_score >= 0.3:
            return 'observe'
        else:
            return 'avoid'
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        dot_product = np.dot(v1, v2)
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        
        if norm_product == 0:
            return 0.0
        
        return float(dot_product / norm_product)
    
    def filter_by_vibe(
        self,
        opportunities: List[Opportunity],
        preferred_vibe: Optional[str] = None,
        avoid_controversy: bool = True
    ) -> List[Opportunity]:
        """
        Filter opportunities by vibe preference.
        
        Args:
            opportunities: List of opportunities
            preferred_vibe: Preferred vibe (optional)
            avoid_controversy: Whether to filter out controversy
        
        Returns:
            Filtered opportunities
        """
        filtered = []
        
        for opp in opportunities:
            signal = opp.signal
            
            # Skip if no vibe detected
            if not signal.vibe:
                filtered.append(opp)
                continue
            
            # Filter controversy
            if avoid_controversy and signal.vibe == 'controversy':
                logger.info(
                    f"Filtered out controversial topic: {signal.representative_text}"
                )
                continue
            
            # Filter by preference
            if preferred_vibe and signal.vibe != preferred_vibe:
                continue
            
            filtered.append(opp)
        
        return filtered
    
    def get_anti_trends(
        self,
        opportunities: List[Opportunity],
        limit: int = 5
    ) -> List[Opportunity]:
        """
        Get anti-trends (topics to avoid).
        
        Args:
            opportunities: All opportunities
            limit: Max to return
        
        Returns:
            List of opportunities marked as 'avoid'
        """
        anti_trends = [
            opp for opp in opportunities
            if opp.recommendation_type == 'avoid'
        ]
        
        # Sort by saturation (highest first)
        anti_trends.sort(
            key=lambda o: o.signal.saturation,
            reverse=True
        )
        
        return anti_trends[:limit]
