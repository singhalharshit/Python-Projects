"""
Live Signal Collector - Orchestrates signal collection from all platforms
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from sqlalchemy.orm import Session

from app.services.signals.abstract_signal import AbstractSignal
from app.services.signals.signal_merger import SignalMerger
from app.services.collectors.google_trends_collector import GoogleTrendsCollector
from app.services.collectors.google_news_collector import GoogleNewsCollector
from app.services.intelligence.embedding_service import EmbeddingService
from app.services.intelligence.sentiment_analyzer import get_sentiment_analyzer
from app.services.intelligence.saturation_tracker import SaturationTracker

logger = logging.getLogger(__name__)


class LiveSignalCollector:
    """
    Orchestrates signal collection from all available platforms.
    
    Philosophy:
    - Collect from all available sources
    - Graceful degradation if sources fail
    - Merge cross-platform signals
    - Enrich with sentiment and saturation
    - Return platform-agnostic AbstractSignals
    
    Process:
    1. Collect raw data from each platform
    2. Convert to AbstractSignals
    3. Enrich with sentiment analysis
    4. Enrich with saturation tracking
    5. Merge duplicate signals
    6. Return unified signal list
    """
    
    def __init__(self, db: Session = None):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.sentiment_analyzer = get_sentiment_analyzer()
        self.saturation_tracker = SaturationTracker(db) if db else None
        self.signal_merger = SignalMerger()
        
        # Initialize collectors
        self.collectors = {
            'google_trends': GoogleTrendsCollector(),
            'google_news': GoogleNewsCollector(),
        }
        
        # Try to initialize optional collectors
        self._initialize_optional_collectors()
    
    def _initialize_optional_collectors(self):
        """Initialize optional collectors (YouTube, etc.)"""
        try:
            from app.services.collectors.youtube_collector import YouTubeCollector
            self.collectors['youtube'] = YouTubeCollector()
            logger.info("YouTube collector initialized")
        except Exception as e:
            logger.info(f"YouTube collector not available: {e}")
    
    def collect_signals(
        self,
        search_space: np.ndarray,
        keywords: List[str] = None,
        radius: float = 0.4,
        max_signals: int = 50
    ) -> List[AbstractSignal]:
        """
        Collect signals relevant to a content space.
        
        Args:
            search_space: Embedding vector representing content area
            keywords: Optional keywords for collection
            radius: How far to search in semantic space
            max_signals: Maximum signals to return
        
        Returns:
            List of AbstractSignals (merged and enriched)
        """
        logger.info(
            f"Collecting signals for search space "
            f"(keywords: {keywords}, radius: {radius})"
        )
        
        all_signals = []
        
        # Collect from each platform
        for platform_name, collector in self.collectors.items():
            try:
                platform_signals = self._collect_from_platform(
                    platform_name,
                    collector,
                    keywords or []
                )
                all_signals.extend(platform_signals)
                
                logger.info(
                    f"✅ Collected {len(platform_signals)} signals from {platform_name}"
                )
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to collect from {platform_name}: {e}")
                continue
        
        if not all_signals:
            logger.warning("No signals collected from any platform")
            return []
        
        logger.info(f"Collected {len(all_signals)} total signals before merging")
        
        # Merge duplicate signals
        merged_signals = self.signal_merger.merge_signals(all_signals)
        
        # Filter by relevance to search space
        if search_space is not None:
            relevant_signals = self._filter_by_relevance(
                merged_signals,
                search_space,
                radius
            )
        else:
            relevant_signals = merged_signals
        
        # Sort by confidence and limit
        relevant_signals.sort(key=lambda s: s.confidence, reverse=True)
        final_signals = relevant_signals[:max_signals]
        
        logger.info(
            f"Returning {len(final_signals)} signals "
            f"(merged from {len(all_signals)}, "
            f"filtered from {len(merged_signals)})"
        )
        
        return final_signals
    
    def _collect_from_platform(
        self,
        platform_name: str,
        collector: Any,
        keywords: List[str]
    ) -> List[AbstractSignal]:
        """
        Collect signals from a specific platform and convert to AbstractSignals.
        """
        # Collect raw data
        if platform_name == 'google_trends':
            raw_data = collector.collect_niche_signals(
                keywords=keywords[:5],  # Max 5 for Google Trends
                niche="general",
                timeframe='now 7-d'
            )
        elif platform_name == 'google_news':
            raw_data = collector.collect_niche_signals(
                keywords=keywords,
                niche="general",
                max_articles=20
            )
        elif platform_name == 'youtube':
            raw_data = collector.collect_niche_signals(
                keywords=keywords,
                niche="general",
                max_results=10
            )
        else:
            logger.warning(f"Unknown platform: {platform_name}")
            return []
        
        # Convert to AbstractSignals
        signals = self._convert_to_abstract_signals(raw_data, platform_name)
        
        # Enrich with sentiment
        signals = self._enrich_with_sentiment(signals)
        
        # Enrich with saturation
        if self.saturation_tracker:
            signals = self._enrich_with_saturation(signals, platform_name)
        
        return signals
    
    def _convert_to_abstract_signals(
        self,
        raw_data: Dict[str, Any],
        platform: str
    ) -> List[AbstractSignal]:
        """
        Convert platform-specific data to AbstractSignals.
        """
        signals = []
        
        trending_topics = raw_data.get('trending_topics', [])
        
        for topic_data in trending_topics:
            try:
                # Extract topic text
                topic_text = topic_data.get('topic', '')
                
                # Generate content vector
                content_vector = self.embedding_service.encode_text(topic_text)
                
                # Extract metrics
                momentum = topic_data.get('momentum_score', 0.5)
                
                # Calculate recency (assume recent if from live collection)
                recency = 0.9
                
                # Calculate noise (inverse of data quality)
                noise = 1.0 - topic_data.get('confidence', 0.5)
                
                # Saturation will be enriched later
                saturation = 0.0
                
                # Create signal
                signal = AbstractSignal(
                    content_vector=content_vector,
                    momentum=momentum,
                    saturation=saturation,
                    recency=recency,
                    noise_level=noise,
                    source_platforms=[platform],
                    evidence=[topic_data],
                    detected_at=datetime.utcnow(),
                    representative_text=topic_text
                )
                
                signals.append(signal)
                
            except Exception as e:
                logger.warning(f"Failed to convert topic to signal: {e}")
                continue
        
        return signals
    
    def _enrich_with_sentiment(
        self,
        signals: List[AbstractSignal]
    ) -> List[AbstractSignal]:
        """
        Enrich signals with sentiment/vibe analysis.
        """
        for signal in signals:
            try:
                # Collect text samples from evidence
                text_samples = []
                for evidence in signal.evidence:
                    if 'title' in evidence:
                        text_samples.append(evidence['title'])
                    if 'description' in evidence:
                        text_samples.append(evidence['description'])
                
                if not text_samples:
                    continue
                
                # Analyze vibe
                vibe_analysis = self.sentiment_analyzer.analyze_vibe(text_samples)
                
                # Update signal
                signal.vibe = vibe_analysis['dominant_vibe']
                signal.vibe_confidence = vibe_analysis['confidence']
                
            except Exception as e:
                logger.warning(f"Sentiment analysis failed: {e}")
                continue
        
        return signals
    
    def _enrich_with_saturation(
        self,
        signals: List[AbstractSignal],
        platform: str
    ) -> List[AbstractSignal]:
        """
        Enrich signals with saturation tracking.
        """
        for signal in signals:
            try:
                # Track this topic appearance
                self.saturation_tracker.track_topic(
                    topic_vector=signal.content_vector,
                    platform=platform,
                    momentum=signal.momentum,
                    representative_text=signal.representative_text
                )
                
                # Get saturation score
                saturation = self.saturation_tracker.get_saturation_score(
                    signal.content_vector
                )
                
                # Update signal
                signal.saturation = saturation
                
            except Exception as e:
                logger.warning(f"Saturation tracking failed: {e}")
                continue
        
        return signals
    
    def _filter_by_relevance(
        self,
        signals: List[AbstractSignal],
        search_space: np.ndarray,
        radius: float
    ) -> List[AbstractSignal]:
        """
        Filter signals by relevance to search space.
        
        Args:
            signals: List of signals
            search_space: Target embedding vector
            radius: Maximum cosine distance
        
        Returns:
            Filtered signals
        """
        relevant_signals = []
        
        for signal in signals:
            # Calculate cosine similarity
            similarity = self._cosine_similarity(
                signal.content_vector,
                search_space
            )
            
            # Convert to distance
            distance = 1 - similarity
            
            # Check if within radius
            if distance <= radius:
                relevant_signals.append(signal)
        
        logger.info(
            f"Filtered {len(signals)} signals to {len(relevant_signals)} "
            f"within radius {radius}"
        )
        
        return relevant_signals
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        dot_product = np.dot(v1, v2)
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        
        if norm_product == 0:
            return 0.0
        
        return float(dot_product / norm_product)
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all collectors.
        
        Returns:
            Dict with status of each platform
        """
        status = {}
        
        for platform_name, collector in self.collectors.items():
            try:
                # Try a test collection
                test_result = collector.collect_niche_signals(
                    keywords=["test"],
                    niche="test",
                    timeframe='now 1-d' if platform_name == 'google_trends' else None,
                    max_articles=1 if platform_name == 'google_news' else None,
                    max_results=1 if platform_name == 'youtube' else None
                )
                
                status[platform_name] = {
                    'status': 'healthy',
                    'last_check': datetime.utcnow().isoformat()
                }
            except Exception as e:
                status[platform_name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'last_check': datetime.utcnow().isoformat()
                }
        
        return status
