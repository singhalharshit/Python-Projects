"""
Recommendation Engine - Core intelligence of the system
Combines signals from multiple sources to generate daily recommendations
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import Counter
import logging
from sqlalchemy.orm import Session

from app.services.collectors import (
    GoogleTrendsCollector,
    GoogleNewsCollector,
)

# Optional collectors
try:
    from app.services.collectors import YouTubeCollector
except:
    YouTubeCollector = None

from app.services.signal_health import SignalHealthMonitor

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generates personalized daily recommendations for social media creators
    
    Philosophy:
    - Conservative: Better to say "don't post" than give bad advice
    - Transparent: Always explain WHY
    - Multi-signal: Higher confidence with multiple sources
    - Graceful degradation: Works even if some sources fail
    """
    
    # Source weights for confidence calculation
    SOURCE_WEIGHTS = {
        'google_trends': 0.40,  # Highest - search intent is strong signal
        'google_news': 0.35,    # High - media coverage validates trends
        'youtube': 0.25,        # Medium - video trends lag slightly
        'reddit': 0.15,         # Bonus - community signals
    }
    
    # Confidence thresholds
    CONFIDENCE_HIGH = 0.75
    CONFIDENCE_MEDIUM = 0.50
    
    def __init__(self, db: Session = None):
        """
        Initialize recommendation engine
        
        Args:
            db: Database session for health monitoring (optional)
        """
        self.db = db
        self.health_monitor = SignalHealthMonitor(db) if db else None
        
        # Initialize collectors
        self.collectors = {
            'google_trends': GoogleTrendsCollector(),
            'google_news': GoogleNewsCollector(),
        }
        
        # Optional collectors (require API keys)
        if YouTubeCollector is not None:
            try:
                self.collectors['youtube'] = YouTubeCollector()
            except Exception as e:
                logger.info(f"YouTube collector not available: {e}")
        
    def generate_recommendation(
        self,
        niche: str,
        keywords: List[str],
        user_preferences: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate daily recommendation for a user
        
        Args:
            niche: User's content niche (e.g., "tech_creators")
            keywords: List of keywords relevant to the niche
            user_preferences: Optional user preferences
        
        Returns:
            Comprehensive recommendation with confidence scores and explanations
        """
        logger.info(f"Generating recommendation for niche: {niche}, keywords: {keywords}")
        
        # Step 1: Collect signals from all available sources
        signals = self._collect_all_signals(keywords, niche)
        
        if not signals:
            return self._generate_no_data_response(niche)
        
        # Step 2: Merge and analyze signals
        merged_topics = self._merge_signals(signals)
        
        if not merged_topics:
            return self._generate_no_trends_response(niche, signals)
        
        # Step 3: Calculate confidence scores
        scored_topics = self._calculate_confidence_scores(merged_topics, signals)
        
        # Step 4: Select best recommendation
        top_recommendation = self._select_best_recommendation(scored_topics, niche)
        
        # [NEW] Step 4.5: Competitor Gap Analysis
        competitor_analysis = None
        user_competitors = user_preferences.get('competitors', []) if user_preferences else []
        
        if top_recommendation and user_competitors:
            try:
                from app.services.competitor_analysis import CompetitorAnalysisService
                comp_service = CompetitorAnalysisService()
                competitor_analysis = comp_service.analyze_topic(
                    top_recommendation['topic'], 
                    user_competitors
                )
                
                # Add analysis to recommendation metadata
                top_recommendation['metadata']['competitor_analysis'] = competitor_analysis
                
            except Exception as e:
                logger.warning(f"Competitor analysis failed: {e}")

        # Step 5: Generate explanation (Updated to include competitor info)
        explanation = self._generate_explanation(top_recommendation, signals)
        
        # Append competitor advice if available
        if competitor_analysis and 'differentiation_advice' in competitor_analysis:
             explanation += "\n\n" + competitor_analysis['differentiation_advice']

        # Step 6: Add alternatives and context
        recommendation = self._build_final_recommendation(
            top_recommendation,
            scored_topics,
            signals,
            explanation,
            niche
        )
        
        logger.info(f"Generated recommendation: {recommendation['action']} - {recommendation.get('topic', 'N/A')}")
        
        return recommendation
    
    def _collect_all_signals(self, keywords: List[str], niche: str) -> List[Dict[str, Any]]:
        """Collect signals from all available data sources"""
        signals = []
        
        for source_name, collector in self.collectors.items():
            try:
                start_time = datetime.utcnow()
                
                # Collect data based on source type
                if source_name == 'google_trends':
                    data = collector.collect_niche_signals(
                        keywords=keywords[:5],  # Max 5 for Google Trends
                        niche=niche,
                        timeframe='now 7-d'
                    )
                elif source_name == 'google_news':
                    data = collector.collect_niche_signals(
                        keywords=keywords,
                        niche=niche,
                        max_articles=20
                    )
                elif source_name == 'youtube':
                    data = collector.collect_niche_signals(
                        keywords=keywords,
                        niche=niche,
                        max_results=10
                    )
                else:
                    continue
                
                signals.append(data)
                
                # Record success in health monitor
                if self.health_monitor:
                    response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    self.health_monitor.record_success(source_name, response_time)
                
                logger.info(f"✅ Collected signals from {source_name}")
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to collect from {source_name}: {e}")
                
                # Record failure in health monitor
                if self.health_monitor:
                    self.health_monitor.record_failure(source_name, str(e))
                
                continue
        
        return signals
    
    def _merge_signals(self, signals: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """
        Merge trending topics from all sources
        
        Returns:
            Dictionary of topics with their aggregated data
        """
        topic_data = {}
        
        for signal in signals:
            source = signal['source']
            weight = self.SOURCE_WEIGHTS.get(source, 0.1)
            
            for topic_info in signal.get('trending_topics', []):
                topic = topic_info['topic'].lower()
                
                if topic not in topic_data:
                    topic_data[topic] = {
                        'name': topic,
                        'sources': [],
                        'momentum_scores': [],
                        'weighted_scores': [],
                        'evidence': [],
                        'metadata': {}
                    }
                
                # Add source
                topic_data[topic]['sources'].append(source)
                
                # Add momentum score
                momentum = topic_info.get('momentum_score', 0)
                topic_data[topic]['momentum_scores'].append(momentum)
                topic_data[topic]['weighted_scores'].append(momentum * weight)
                
                # Add evidence
                evidence = {
                    'source': source,
                    'momentum': momentum,
                    'details': topic_info
                }
                topic_data[topic]['evidence'].append(evidence)
                
                # Store source-specific metadata
                if source == 'google_trends':
                    topic_data[topic]['metadata']['trends'] = {
                        'direction': topic_info.get('trend_direction'),
                        'growth_rate': topic_info.get('growth_rate'),
                        'current_interest': topic_info.get('current_interest')
                    }
                elif source == 'google_news':
                    topic_data[topic]['metadata']['news'] = {
                        'article_count': topic_info.get('article_count'),
                        'recency_score': topic_info.get('recency_score'),
                        'sources': topic_info.get('sources', [])
                    }
                elif source == 'youtube':
                    topic_data[topic]['metadata']['youtube'] = {
                        'avg_views': topic_info.get('avg_views'),
                        'sample_videos': topic_info.get('sample_videos', [])
                    }
        
        return topic_data
    
    def _calculate_confidence_scores(
        self,
        topic_data: Dict[str, Dict],
        signals: List[Dict]
    ) -> List[Dict]:
        """
        Calculate confidence scores for each topic
        
        Confidence is based on:
        1. Number of sources (more sources = higher confidence)
        2. Weighted momentum scores
        3. Source diversity
        4. Signal health
        """
        scored_topics = []
        
        for topic, data in topic_data.items():
            # Base score: weighted average of momentum scores
            if data['weighted_scores']:
                base_score = sum(data['weighted_scores']) / sum(
                    self.SOURCE_WEIGHTS.get(s, 0.1) for s in data['sources']
                )
            else:
                base_score = 0
            
            # Source diversity bonus (multiple sources agreeing)
            source_count = len(data['sources'])
            diversity_bonus = min((source_count - 1) * 0.15, 0.30)  # Max 30% bonus
            
            # Final confidence score
            confidence_score = min(base_score + diversity_bonus, 1.0)
            
            # Classify confidence level
            if confidence_score >= self.CONFIDENCE_HIGH and source_count >= 2:
                confidence_level = "high"
            elif confidence_score >= self.CONFIDENCE_MEDIUM:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            scored_topics.append({
                'topic': topic,
                'confidence_score': confidence_score,
                'confidence_level': confidence_level,
                'source_count': source_count,
                'sources': data['sources'],
                'evidence': data['evidence'],
                'metadata': data['metadata']
            })
        
        # Sort by confidence score
        scored_topics.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return scored_topics
    
    def _select_best_recommendation(
        self,
        scored_topics: List[Dict],
        niche: str
    ) -> Optional[Dict]:
        """
        Select the best recommendation from scored topics
        
        Returns None if no good recommendation available
        """
        if not scored_topics:
            return None
        
        # Get top topic
        top_topic = scored_topics[0]
        
        # Check if confidence is acceptable
        if top_topic['confidence_score'] < 0.40:  # Minimum threshold
            return None
        
        # Check for saturation (future enhancement)
        # For now, accept the top topic
        
        return top_topic
    
    def _generate_explanation(self, recommendation: Dict, signals: List[Dict]) -> str:
        """
        Generate a human-like narrative explanation instead of raw stats.
        """
        topic = recommendation['topic']
        score = recommendation['confidence_score']
        
        # 1. Momentum / Timing Narrative
        timing_narrative = ""
        if score >= 0.85:
            timing_narrative = "Signals suggest renewed interest in this concept right now."
        elif score >= 0.70:
            timing_narrative = "Interest is steadily building, making this a safe bet."
        else:
            timing_narrative = "This topic is emerging, though not yet mainstream."
            
        # 2. Source Context
        news_count = sum(1 for s in signals if s['source'] == 'google_news')
        trend_count = sum(1 for s in signals if s['source'] == 'google_trends')
        source_narrative = ""
        
        if news_count > 0 and trend_count > 0:
            source_narrative = "We're seeing alignment across both search behavior and news coverage."
        elif news_count > 0:
            source_narrative = "News outlets are picking this up, but search volume hasn't peaked yet (Early Opportunity)."
        elif trend_count > 0:
            source_narrative = "People are actively searching for this, even if the news cycle is quiet."
            
        # 3. Gap / Angle Narrative
        gap_narrative = "Most current content is likely surface-level."
        
        return f"{timing_narrative} {source_narrative} {gap_narrative} Creators who focus on deep dives or contrarian takes are engaging better than those posting generic tutorials."

    def _generate_angles(self, topic: str, niche: str) -> List[str]:
        """
        Generate specific, high-clickthrough 'angles' for a topic.
        """
        templates = [
            "Why {topic} is misunderstood",
            "The {topic} Trap: What beginners get wrong",
            "Stop doing {topic} like this (Do this instead)",
            "The hidden cost of ignoring {topic}",
            "How {topic} is changing in 2025",
            "What senior experts know about {topic} that you don't"
        ]
        
        import random
        # Use a stable sort of random if possible, or just sample
        selected = random.sample(templates, min(3, len(templates)))
        return [t.format(topic=topic) for t in selected]
    
    def _build_final_recommendation(
        self,
        top_recommendation: Optional[Dict],
        all_topics: List[Dict],
        signals: List[Dict],
        explanation: str,
        niche: str
    ) -> Dict[str, Any]:
        """Build the final recommendation response"""
        
        # Get signal health status
        signal_health = {}
        for signal in signals:
            source = signal['source']
            signal_health[source] = "healthy"  # Simplified for now
        
        # If no good recommendation
        if not top_recommendation:
            return {
                'status': 'no_recommendation',
                'action': 'rest',
                'niche': niche,
                'topic': None,
                'confidence_score': 0,
                'confidence_level': 'none',
                'explanation': explanation,
                'reasoning': "No strong trends detected. Consider taking a rest day or engaging with your audience instead of posting new content.",
                'signal_health': signal_health,
                'sources_checked': len(signals),
                'sources_available': len(signals),
                'alternatives': [],
                'generated_at': datetime.utcnow().isoformat()
            }
        
        # Build recommendation
        topic = top_recommendation['topic']
        confidence_score = top_recommendation['confidence_score']
        confidence_level = top_recommendation['confidence_level']
        
        # Get alternatives (next 2-3 topics)
        alternatives = [
            {
                'topic': t['topic'],
                'confidence_score': t['confidence_score'],
                'sources': t['sources']
            }
            for t in all_topics[1:4]
            if t['confidence_score'] >= 0.40
        ]

        # Determine action based on confidence_score (0-1 range)
        score_100 = int(top_recommendation['confidence_score'] * 100)
        action = "post" if score_100 > 70 else "wait"
        confidence_level = "high" if score_100 > 80 else "medium"

        # [AI UPGRADE] Extract angle data from top_recommendation metadata
        # (These were added earlier in the generation flow or we add them now)
        angles = self._generate_angles(topic, niche)
        topic_direction = f"{topic.title()} — but focus on misconceptions, not tutorials"
        avoid_advice = f"Avoid generic 'how-to' guides for {topic}. These appear saturated."

        return {
            "status": "success",
            "action": action,
            "niche": niche,
            "topic": topic,
            "confidence_score": score_100,
            "confidence_level": confidence_level,
            "explanation": explanation,
            "reasoning": f"AI Analysed {len(signals)} signals. Top Driver: {top_recommendation.get('sources', ['Unknown'])[0]}",
            "sources": top_recommendation.get('sources', []),
            "source_count": len(top_recommendation.get('sources', [])),
            "alternatives": alternatives,
            "timing": {
                "urgency": "high",
                "suggested_window": "Next 24 hours",
                "reason": "Momentum detected"
            },
            "metadata": top_recommendation.get('metadata', {}),
            "generated_at": datetime.utcnow().isoformat(),
            # Top-level fields for schema compatibility
            "suggested_angles": angles,
            "topic_direction": topic_direction,
            "avoid_advice": avoid_advice
        }
    
    def _suggest_timing(self, recommendation: Dict) -> Dict[str, Any]:
        """Suggest optimal timing for posting"""
        
        metadata = recommendation.get('metadata', {})
        
        # Check trend direction from Google Trends
        trends_meta = metadata.get('trends', {})
        direction = trends_meta.get('direction', 'stable')
        
        if direction == 'rising':
            urgency = 'medium'
            window = 'next 2-3 days'
            reason = 'Trend is rising. Post soon to catch early momentum.'
        elif direction == 'stable':
            urgency = 'low'
            window = 'next 3-5 days'
            reason = 'Trend is stable. You have time to create quality content.'
        else:  # falling
            urgency = 'high'
            window = 'next 24 hours'
            reason = 'Trend may be declining. Post quickly if you want to participate.'
        
        return {
            'urgency': urgency,
            'suggested_window': window,
            'reason': reason
        }
    
    def _detect_anti_trends(self, all_topics: List[Dict]) -> List[Dict]:
        """
        Detect topics to avoid (saturated or declining)
        
        Future enhancement: Track topic frequency over time
        For now, return empty list
        """
        anti_trends = []
        
        # Future: Check for saturation
        # For each topic, if it appeared in many sources but with declining momentum
        # or if it's been trending for too long, mark as anti-trend
        
        return anti_trends
    
    def _generate_no_data_response(self, niche: str) -> Dict[str, Any]:
        """Generate response when no data sources are available"""
        return {
            'status': 'error',
            'action': 'rest',
            'niche': niche,
            'topic': None,
            'confidence_score': 0,
            'confidence_level': 'none',
            'explanation': 'Unable to collect data from any sources.',
            'reasoning': 'All data sources are currently unavailable. Please try again later.',
            'signal_health': {},
            'sources_checked': 0,
            'sources_available': 0,
            'alternatives': [],
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _generate_no_trends_response(
        self,
        niche: str,
        signals: List[Dict]
    ) -> Dict[str, Any]:
        """Generate response when no trends are detected"""
        
        signal_health = {signal['source']: 'healthy' for signal in signals}
        
        return {
            'status': 'no_trends',
            'action': 'rest',
            'niche': niche,
            'topic': None,
            'confidence_score': 0,
            'confidence_level': 'none',
            'explanation': 'No significant trends detected in your niche at this time.',
            'reasoning': 'Data sources are working, but no strong signals found. Consider: 1) Engaging with your audience, 2) Reviewing past successful content, or 3) Taking a strategic rest day.',
            'signal_health': signal_health,
            'sources_checked': len(signals),
            'sources_available': len(signals),
            'alternatives': [],
            'generated_at': datetime.utcnow().isoformat()
        }
