"""
Signal Merger - Merges duplicate signals from different platforms
"""
import logging
from typing import List
import numpy as np
from sklearn.cluster import DBSCAN

from app.services.signals.abstract_signal import AbstractSignal

logger = logging.getLogger(__name__)


class SignalMerger:
    """
    Merges signals representing the same topic from different platforms.
    
    Uses vector similarity (DBSCAN clustering) to identify duplicates.
    
    Philosophy:
    - Same topic from multiple platforms = stronger signal
    - Boost confidence for cross-platform validation
    - Preserve evidence from all sources
    """
    
    def __init__(self, similarity_threshold: float = 0.15):
        """
        Args:
            similarity_threshold: Cosine distance threshold for merging
                                 (lower = more strict, default 0.15)
        """
        self.similarity_threshold = similarity_threshold
    
    def merge_signals(self, signals: List[AbstractSignal]) -> List[AbstractSignal]:
        """
        Merge duplicate signals from different platforms.
        
        Args:
            signals: List of AbstractSignals from various platforms
        
        Returns:
            List of merged AbstractSignals (deduplicated)
        """
        if not signals:
            return []
        
        if len(signals) == 1:
            return signals
        
        logger.info(f"Merging {len(signals)} signals...")
        
        # Extract content vectors
        vectors = np.array([s.content_vector for s in signals])
        
        # Cluster by similarity using DBSCAN
        clustering = DBSCAN(
            eps=self.similarity_threshold,
            min_samples=1,
            metric='cosine'
        ).fit(vectors)
        
        # Group signals by cluster
        clusters = {}
        for idx, label in enumerate(clustering.labels_):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(signals[idx])
        
        # Merge each cluster
        merged_signals = []
        for cluster_id, cluster_signals in clusters.items():
            if len(cluster_signals) == 1:
                # Single signal, no merging needed
                merged_signals.append(cluster_signals[0])
            else:
                # Multiple signals, merge them
                merged = self._merge_signal_cluster(cluster_signals)
                merged_signals.append(merged)
                
                logger.info(
                    f"Merged {len(cluster_signals)} signals into 1: "
                    f"{merged.representative_text} "
                    f"(platforms: {', '.join(merged.source_platforms)})"
                )
        
        logger.info(
            f"Merged {len(signals)} signals into {len(merged_signals)} "
            f"({len(signals) - len(merged_signals)} duplicates removed)"
        )
        
        return merged_signals
    
    def _merge_signal_cluster(
        self,
        signals: List[AbstractSignal]
    ) -> AbstractSignal:
        """
        Merge multiple signals representing the same topic.
        
        Strategy:
        - Average content vectors
        - Take max momentum (most optimistic)
        - Average saturation
        - Max recency (most recent)
        - Min noise (best quality)
        - Combine platforms and evidence
        """
        # Average content vectors
        avg_vector = np.mean([s.content_vector for s in signals], axis=0)
        
        # Max momentum (most optimistic signal)
        max_momentum = max(s.momentum for s in signals)
        
        # Average saturation
        avg_saturation = np.mean([s.saturation for s in signals])
        
        # Max recency (most recent)
        max_recency = max(s.recency for s in signals)
        
        # Min noise (best signal quality)
        min_noise = min(s.noise_level for s in signals)
        
        # Combine platforms (unique)
        all_platforms = list(set(
            platform
            for signal in signals
            for platform in signal.source_platforms
        ))
        
        # Combine evidence
        all_evidence = [
            evidence
            for signal in signals
            for evidence in signal.evidence
        ]
        
        # Most recent detection time
        max_detected_at = max(s.detected_at for s in signals)
        
        # Prefer non-None representative text
        representative_text = next(
            (s.representative_text for s in signals if s.representative_text),
            None
        )
        
        # Merge vibe (prefer higher confidence)
        best_vibe_signal = max(signals, key=lambda s: s.vibe_confidence)
        merged_vibe = best_vibe_signal.vibe
        merged_vibe_confidence = best_vibe_signal.vibe_confidence
        
        # Create merged signal
        merged = AbstractSignal(
            content_vector=avg_vector,
            momentum=max_momentum,
            saturation=avg_saturation,
            recency=max_recency,
            noise_level=min_noise,
            source_platforms=all_platforms,
            evidence=all_evidence,
            detected_at=max_detected_at,
            representative_text=representative_text,
            vibe=merged_vibe,
            vibe_confidence=merged_vibe_confidence
        )
        
        return merged
    
    def calculate_merge_benefit(
        self,
        signal1: AbstractSignal,
        signal2: AbstractSignal
    ) -> float:
        """
        Calculate benefit of merging two signals.
        
        Returns:
            Confidence boost from merging (0-1)
        """
        # Check if they're similar enough to merge
        similarity = self._cosine_similarity(
            signal1.content_vector,
            signal2.content_vector
        )
        
        if similarity < (1 - self.similarity_threshold):
            return 0.0  # Too different
        
        # Benefit from cross-platform validation
        platform_diversity = len(set(
            signal1.source_platforms + signal2.source_platforms
        ))
        
        # Benefit from evidence accumulation
        evidence_boost = min(
            (len(signal1.evidence) + len(signal2.evidence)) / 20,
            0.3
        )
        
        # Total benefit
        benefit = (platform_diversity * 0.1) + evidence_boost
        
        return min(benefit, 0.5)
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        dot_product = np.dot(v1, v2)
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        
        if norm_product == 0:
            return 0.0
        
        return float(dot_product / norm_product)
