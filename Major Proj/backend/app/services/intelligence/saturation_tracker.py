"""
Saturation Tracker - Detect topic saturation and anti-trends
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import numpy as np

from app.models.topic_history import TopicHistory

logger = logging.getLogger(__name__)


class SaturationTracker:
    """
    Tracks topic frequency over time to detect saturation.
    
    Key functions:
    - Track topic appearances
    - Calculate saturation scores
    - Detect declining trends
    - Generate "too late" warnings
    
    Philosophy:
    - Prevent creators from posting on overcrowded topics
    - Detect when a trend has passed its peak
    - Conservative: Better to miss a trend than post too late
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def track_topic(
        self,
        topic_vector: np.ndarray,
        platform: str,
        momentum: float,
        representative_text: str = None
    ) -> TopicHistory:
        """
        Record a topic appearance.
        
        Args:
            topic_vector: Semantic embedding of the topic
            platform: Source platform
            momentum: Current momentum score
            representative_text: Human-readable topic name
        
        Returns:
            TopicHistory record (created or updated)
        """
        topic_hash = TopicHistory.hash_vector(topic_vector)
        
        # Check if topic exists
        existing = self.db.query(TopicHistory).filter_by(
            topic_hash=topic_hash
        ).first()
        
        if existing:
            # Update existing record
            existing.add_appearance(platform, momentum)
            
            # Update lifecycle phase
            existing.lifecycle_phase = existing.infer_lifecycle_phase()
            
            # Update saturation score
            existing.calculate_saturation()
            
            logger.info(
                f"Updated topic {existing.representative_text}: "
                f"appearances={existing.appearance_count}, "
                f"saturation={existing.saturation_score:.2f}, "
                f"phase={existing.lifecycle_phase}"
            )
            
        else:
            # Create new record
            new_topic = TopicHistory(
                id=topic_hash,
                topic_hash=topic_hash,
                representative_text=representative_text or "Unknown Topic",
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                appearance_count=1,
                source_platforms=[platform],
                momentum_history=[{
                    'date': datetime.utcnow().isoformat(),
                    'momentum': momentum,
                    'platform': platform
                }]
            )
            new_topic.set_topic_vector(topic_vector)
            new_topic.lifecycle_phase = "emerging"
            new_topic.saturation_score = 0.0
            
            self.db.add(new_topic)
            
            logger.info(f"New topic tracked: {representative_text}")
        
        self.db.commit()
        
        return existing if existing else new_topic
    
    def get_saturation_score(self, topic_vector: np.ndarray) -> float:
        """
        Get current saturation score for a topic.
        
        Args:
            topic_vector: Semantic embedding of the topic
        
        Returns:
            Saturation score (0-1), or 0.0 if topic not tracked
        """
        topic_hash = TopicHistory.hash_vector(topic_vector)
        
        history = self.db.query(TopicHistory).filter_by(
            topic_hash=topic_hash
        ).first()
        
        if not history:
            return 0.0  # New topic, not saturated
        
        # Calculate and update saturation
        saturation = history.calculate_saturation()
        self.db.commit()
        
        return saturation
    
    def is_saturated(
        self,
        topic_vector: np.ndarray,
        threshold: float = 0.7
    ) -> bool:
        """
        Check if topic is saturated.
        
        Args:
            topic_vector: Semantic embedding of the topic
            threshold: Saturation threshold (default 0.7)
        
        Returns:
            True if saturated
        """
        saturation = self.get_saturation_score(topic_vector)
        return saturation >= threshold
    
    def is_declining(self, topic_vector: np.ndarray) -> bool:
        """
        Check if topic is in declining phase.
        
        Args:
            topic_vector: Semantic embedding of the topic
        
        Returns:
            True if declining
        """
        topic_hash = TopicHistory.hash_vector(topic_vector)
        
        history = self.db.query(TopicHistory).filter_by(
            topic_hash=topic_hash
        ).first()
        
        if not history:
            return False
        
        lifecycle_phase = history.infer_lifecycle_phase()
        return lifecycle_phase == "declining"
    
    def should_avoid(
        self,
        topic_vector: np.ndarray,
        saturation_threshold: float = 0.7
    ) -> tuple[bool, str]:
        """
        Determine if topic should be avoided.
        
        Args:
            topic_vector: Semantic embedding of the topic
            saturation_threshold: Saturation threshold
        
        Returns:
            (should_avoid, reason)
        """
        topic_hash = TopicHistory.hash_vector(topic_vector)
        
        history = self.db.query(TopicHistory).filter_by(
            topic_hash=topic_hash
        ).first()
        
        if not history:
            return False, ""
        
        # Check saturation
        saturation = history.calculate_saturation()
        if saturation >= saturation_threshold:
            return True, f"Topic appears saturated (saturation: {saturation:.0%})"
        
        # Check lifecycle phase
        lifecycle_phase = history.infer_lifecycle_phase()
        if lifecycle_phase == "declining":
            return True, "Interest appears to be declining"
        
        if lifecycle_phase == "saturated":
            return True, "Topic appears overcrowded"
        
        # Check if peak has passed
        if history.peak_date:
            days_since_peak = (datetime.utcnow() - history.peak_date).days
            if days_since_peak > 3:
                return True, f"Peak was {days_since_peak} days ago"
        
        return False, ""
    
    def get_topic_history(
        self,
        topic_vector: np.ndarray
    ) -> Optional[TopicHistory]:
        """
        Get full history for a topic.
        
        Args:
            topic_vector: Semantic embedding of the topic
        
        Returns:
            TopicHistory record or None
        """
        topic_hash = TopicHistory.hash_vector(topic_vector)
        
        return self.db.query(TopicHistory).filter_by(
            topic_hash=topic_hash
        ).first()
    
    def get_anti_trends(
        self,
        limit: int = 10,
        min_appearances: int = 3
    ) -> List[TopicHistory]:
        """
        Get current anti-trends (topics to avoid).
        
        Args:
            limit: Maximum number to return
            min_appearances: Minimum appearances to consider
        
        Returns:
            List of TopicHistory records for anti-trends
        """
        # Query topics that are saturated or declining
        anti_trends = self.db.query(TopicHistory).filter(
            TopicHistory.appearance_count >= min_appearances,
            TopicHistory.lifecycle_phase.in_(['saturated', 'declining'])
        ).order_by(
            TopicHistory.saturation_score.desc()
        ).limit(limit).all()
        
        return anti_trends
    
    def get_emerging_topics(
        self,
        limit: int = 10,
        max_saturation: float = 0.3
    ) -> List[TopicHistory]:
        """
        Get emerging topics (good opportunities).
        
        Args:
            limit: Maximum number to return
            max_saturation: Maximum saturation score
        
        Returns:
            List of TopicHistory records for emerging topics
        """
        # Query topics in emerging or accelerating phase
        emerging = self.db.query(TopicHistory).filter(
            TopicHistory.saturation_score <= max_saturation,
            TopicHistory.lifecycle_phase.in_(['emerging', 'accelerating'])
        ).order_by(
            TopicHistory.last_seen.desc()
        ).limit(limit).all()
        
        return emerging
    
    def cleanup_old_topics(self, days: int = 90):
        """
        Clean up topics not seen in X days.
        
        Args:
            days: Number of days of inactivity before cleanup
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        deleted = self.db.query(TopicHistory).filter(
            TopicHistory.last_seen < cutoff
        ).delete()
        
        self.db.commit()
        
        logger.info(f"Cleaned up {deleted} old topics")
        
        return deleted
    
    def get_saturation_explanation(
        self,
        topic_vector: np.ndarray
    ) -> str:
        """
        Get calm explanation of saturation status.
        
        Args:
            topic_vector: Semantic embedding of the topic
        
        Returns:
            Human-readable explanation
        """
        history = self.get_topic_history(topic_vector)
        
        if not history:
            return "This topic is new to our tracking system."
        
        saturation = history.saturation_score
        lifecycle_phase = history.lifecycle_phase
        
        # Build calm explanation
        parts = []
        
        # Saturation level
        if saturation < 0.3:
            parts.append("This topic appears relatively fresh")
        elif saturation < 0.6:
            parts.append("This topic is gaining attention")
        elif saturation < 0.8:
            parts.append("This topic is becoming crowded")
        else:
            parts.append("This topic appears saturated")
        
        # Lifecycle context
        if lifecycle_phase == "emerging":
            parts.append("and is in an early phase")
        elif lifecycle_phase == "accelerating":
            parts.append("with building momentum")
        elif lifecycle_phase == "declining":
            parts.append("but interest seems to be fading")
        elif lifecycle_phase == "saturated":
            parts.append("with many creators covering it")
        
        # Appearance context
        days_active = (history.last_seen - history.first_seen).days
        if days_active > 0:
            parts.append(
                f"(tracked for {days_active} days, "
                f"{history.appearance_count} appearances)"
            )
        
        return " ".join(parts) + "."
