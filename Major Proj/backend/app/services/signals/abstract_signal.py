"""
Abstract Signal - Platform-agnostic content signal representation
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class AbstractSignal:
    """
    Platform-agnostic representation of a content trend/topic.
    
    This is the universal signal format that all platform-specific
    collectors must map to. Enables cross-platform signal merging
    and comparison.
    
    Philosophy:
    - No platform-specific fields
    - Semantic content vector for similarity
    - Lifecycle and momentum metrics
    - Evidence trails for explainability
    """
    
    # Core identity
    content_vector: np.ndarray  # Semantic embedding (384-dim)
    
    # Lifecycle metrics (all 0-1 scale)
    momentum: float  # Rising/falling trend strength
    saturation: float  # How crowded/oversaturated
    recency: float  # How fresh/recent
    noise_level: float  # Signal clarity (lower is better)
    
    # Source tracking
    source_platforms: List[str]  # ['google_trends', 'youtube', etc.]
    evidence: List[Dict[str, Any]]  # Raw data points from each source
    
    # Metadata
    detected_at: datetime
    representative_text: Optional[str] = None  # Human-readable topic name
    
    # Derived properties (calculated)
    confidence: float = field(init=False)
    lifecycle_phase: str = field(init=False)
    vibe: Optional[str] = None  # 'hype', 'critique', 'calm', 'controversy'
    vibe_confidence: float = 0.0
    
    def __post_init__(self):
        """Calculate derived properties"""
        self.confidence = self._calculate_confidence()
        self.lifecycle_phase = self._infer_lifecycle()
    
    def _calculate_confidence(self) -> float:
        """
        Calculate signal confidence based on:
        - Multiple source agreement (more sources = higher confidence)
        - Low noise (clear signal)
        - Clear momentum direction
        
        Returns: 0-1 confidence score
        """
        # Source diversity bonus (max 0.6)
        source_bonus = min(len(self.source_platforms) * 0.2, 0.6)
        
        # Noise penalty (max -0.3)
        noise_penalty = self.noise_level * 0.3
        
        # Momentum clarity bonus (clear direction = higher confidence)
        # Momentum near 0.5 is unclear, near 0 or 1 is clear
        clarity_bonus = abs(self.momentum - 0.5) * 0.4
        
        confidence = source_bonus - noise_penalty + clarity_bonus
        
        return max(0.0, min(confidence, 1.0))
    
    def _infer_lifecycle(self) -> str:
        """
        Infer lifecycle phase from metrics.
        
        Returns: 'emerging', 'accelerating', 'peak', 'saturated', 'declining'
        """
        if self.momentum > 0.7 and self.saturation < 0.3:
            return "emerging"
        elif self.momentum > 0.6 and self.saturation < 0.6:
            return "accelerating"
        elif self.saturation > 0.8:
            return "saturated"
        elif self.momentum < 0.3:
            return "declining"
        elif self.momentum > 0.7:
            return "peak"
        else:
            return "stable"
    
    def is_opportunity(self) -> bool:
        """
        Quick check if this is a potential opportunity.
        True if: emerging/accelerating phase AND not saturated
        """
        return (
            self.lifecycle_phase in ["emerging", "accelerating"] and
            self.saturation < 0.7 and
            self.confidence > 0.5
        )
    
    def is_anti_trend(self) -> bool:
        """
        Quick check if this should be avoided.
        True if: saturated OR declining
        """
        return (
            self.lifecycle_phase in ["saturated", "declining"] or
            self.saturation > 0.7
        )
    
    def merge_with(self, other: 'AbstractSignal') -> 'AbstractSignal':
        """
        Merge this signal with another (same topic, different platform).
        
        Args:
            other: Another AbstractSignal representing the same topic
        
        Returns:
            New merged AbstractSignal
        """
        # Average content vectors
        merged_vector = (self.content_vector + other.content_vector) / 2
        
        # Take max momentum (most optimistic)
        merged_momentum = max(self.momentum, other.momentum)
        
        # Average saturation
        merged_saturation = (self.saturation + other.saturation) / 2
        
        # Max recency (most recent)
        merged_recency = max(self.recency, other.recency)
        
        # Min noise (best signal quality)
        merged_noise = min(self.noise_level, other.noise_level)
        
        # Combine platforms
        merged_platforms = list(set(self.source_platforms + other.source_platforms))
        
        # Combine evidence
        merged_evidence = self.evidence + other.evidence
        
        # Most recent detection time
        merged_detected_at = max(self.detected_at, other.detected_at)
        
        # Prefer non-None representative text
        merged_text = self.representative_text or other.representative_text
        
        # Merge vibe (prefer higher confidence)
        if self.vibe_confidence > other.vibe_confidence:
            merged_vibe = self.vibe
            merged_vibe_conf = self.vibe_confidence
        else:
            merged_vibe = other.vibe
            merged_vibe_conf = other.vibe_confidence
        
        return AbstractSignal(
            content_vector=merged_vector,
            momentum=merged_momentum,
            saturation=merged_saturation,
            recency=merged_recency,
            noise_level=merged_noise,
            source_platforms=merged_platforms,
            evidence=merged_evidence,
            detected_at=merged_detected_at,
            representative_text=merged_text,
            vibe=merged_vibe,
            vibe_confidence=merged_vibe_conf
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'representative_text': self.representative_text,
            'momentum': float(self.momentum),
            'saturation': float(self.saturation),
            'recency': float(self.recency),
            'noise_level': float(self.noise_level),
            'confidence': float(self.confidence),
            'lifecycle_phase': self.lifecycle_phase,
            'vibe': self.vibe,
            'vibe_confidence': float(self.vibe_confidence),
            'source_platforms': self.source_platforms,
            'source_count': len(self.source_platforms),
            'detected_at': self.detected_at.isoformat(),
            'is_opportunity': self.is_opportunity(),
            'is_anti_trend': self.is_anti_trend(),
            'evidence_count': len(self.evidence)
        }
    
    def get_explanation_context(self) -> str:
        """
        Generate human-readable context for explanations.
        Used by DecisionSynthesizer for calm explanations.
        """
        context_parts = []
        
        # Lifecycle context
        if self.lifecycle_phase == "emerging":
            context_parts.append("This topic is in an early phase")
        elif self.lifecycle_phase == "accelerating":
            context_parts.append("Momentum is building around this")
        elif self.lifecycle_phase == "saturated":
            context_parts.append("This topic appears crowded")
        elif self.lifecycle_phase == "declining":
            context_parts.append("Interest seems to be fading")
        
        # Source context
        if len(self.source_platforms) > 1:
            platforms = ", ".join(self.source_platforms[:2])
            context_parts.append(f"detected across {platforms}")
        
        # Vibe context
        if self.vibe and self.vibe_confidence > 0.6:
            if self.vibe == "hype":
                context_parts.append("with enthusiastic energy")
            elif self.vibe == "critique":
                context_parts.append("with critical discussion")
            elif self.vibe == "calm":
                context_parts.append("with measured interest")
            elif self.vibe == "controversy":
                context_parts.append("with mixed reactions")
        
        return ". ".join(context_parts) if context_parts else "Signals detected"


@dataclass
class CreatorEmbedding:
    """
    Multi-dimensional representation of a creator's content.
    
    Separate vectors for different aspects enable nuanced similarity:
    - Theme: What they talk about
    - Tone: How they communicate
    - Format: How they structure content
    - Trajectory: Growth pattern
    """
    
    theme: np.ndarray  # Semantic content themes (384-dim)
    tone: np.ndarray  # Communication style (5-dim)
    format: np.ndarray  # Content format patterns (4-dim)
    trajectory: np.ndarray  # Growth trajectory (4-dim)
    
    # Metadata
    creator_id: str
    platform: str
    analyzed_at: datetime
    post_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'creator_id': self.creator_id,
            'platform': self.platform,
            'analyzed_at': self.analyzed_at.isoformat(),
            'post_count': self.post_count,
            'dimensions': {
                'theme': self.theme.shape[0],
                'tone': self.tone.shape[0],
                'format': self.format.shape[0],
                'trajectory': self.trajectory.shape[0]
            }
        }
    
    def get_combined_vector(self, weights: Dict[str, float] = None) -> np.ndarray:
        """
        Get weighted combination of all vectors.
        
        Args:
            weights: Optional weights for each dimension
                    Default: {'theme': 0.6, 'tone': 0.2, 'format': 0.1, 'trajectory': 0.1}
        
        Returns:
            Combined vector (normalized)
        """
        if weights is None:
            weights = {'theme': 0.6, 'tone': 0.2, 'format': 0.1, 'trajectory': 0.1}
        
        # Normalize each vector
        theme_norm = self.theme / (np.linalg.norm(self.theme) + 1e-8)
        tone_norm = self.tone / (np.linalg.norm(self.tone) + 1e-8)
        format_norm = self.format / (np.linalg.norm(self.format) + 1e-8)
        trajectory_norm = self.trajectory / (np.linalg.norm(self.trajectory) + 1e-8)
        
        # For combination, we'll use theme as base and add weighted influences
        # This is a simplified approach - in production you might use more sophisticated methods
        combined = (
            theme_norm * weights['theme'] +
            np.pad(tone_norm, (0, len(theme_norm) - len(tone_norm))) * weights['tone'] +
            np.pad(format_norm, (0, len(theme_norm) - len(format_norm))) * weights['format'] +
            np.pad(trajectory_norm, (0, len(theme_norm) - len(trajectory_norm))) * weights['trajectory']
        )
        
        # Normalize result
        return combined / (np.linalg.norm(combined) + 1e-8)


@dataclass
class Opportunity:
    """
    Represents a content opportunity with scoring.
    """
    
    signal: AbstractSignal
    
    # Scoring components (all 0-1)
    timing_score: float  # Lifecycle phase quality
    differentiation_score: float  # Competitor gap
    alignment_score: float  # Fits creator's style
    preference_score: float  # User has shown interest
    confidence_score: float  # Signal quality
    
    # Combined score
    total_score: float
    
    # Recommendation type
    recommendation_type: str  # 'post', 'consider', 'observe', 'avoid'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'signal': self.signal.to_dict(),
            'scores': {
                'timing': float(self.timing_score),
                'differentiation': float(self.differentiation_score),
                'alignment': float(self.alignment_score),
                'preference': float(self.preference_score),
                'confidence': float(self.confidence_score),
                'total': float(self.total_score)
            },
            'recommendation_type': self.recommendation_type,
            'lifecycle_phase': self.signal.lifecycle_phase
        }


@dataclass
class DailyDecision:
    """
    The final daily decision presented to the user.
    
    Philosophy:
    - ONE clear action
    - Calm, conservative explanation
    - Emotional context
    - Rest is a valid action
    """
    
    action: str  # 'post', 'rest', 'observe'
    topic: Optional[str]
    confidence: float
    explanation: str
    
    # Optional fields
    timing: Optional[Dict[str, Any]] = None
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    avoid: List[Dict[str, Any]] = field(default_factory=list)
    
    # Emotional context
    emotional_context: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'action': self.action,
            'topic': self.topic,
            'confidence': float(self.confidence),
            'explanation': self.explanation,
            'timing': self.timing,
            'alternatives': self.alternatives,
            'avoid': self.avoid,
            'emotional_context': self.emotional_context,
            'metadata': self.metadata,
            'generated_at': self.generated_at.isoformat()
        }
