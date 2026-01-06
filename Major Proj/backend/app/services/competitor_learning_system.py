"""
Competitor Learning System
Stores and learns from discovered competitors to improve future discovery
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.creator import Creator

logger = logging.getLogger(__name__)


class CompetitorLearningSystem:
    """
    Self-learning system that:
    1. Stores every discovered competitor
    2. Learns which competitors are selected by users
    3. Improves discovery based on historical data
    4. No hardcoding - purely data-driven
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def store_discovered_competitors(
        self,
        competitors: List[Dict[str, Any]],
        source_username: str,
        niche: str
    ) -> None:
        """
        Store discovered competitors in database for learning.
        Every discovery enriches the system.
        """
        logger.info(f"📚 Storing {len(competitors)} discovered competitors...")
        
        for competitor in competitors:
            try:
                # Check if creator already exists
                creator = self.db.query(Creator).filter_by(
                    handle=competitor.get('username', ''),
                    platform=competitor.get('platform', 'instagram')
                ).first()
                
                if not creator:
                    # Create new creator
                    creator = Creator(
                        handle=competitor.get('username', ''),
                        name=competitor.get('name', ''),
                        platform=competitor.get('platform', 'instagram'),
                        niche=niche,
                        language='en',
                        subscriber_count=self._parse_subscriber_count(
                            competitor.get('subs', '0')
                        ),
                        avg_engagement_rate=competitor.get('confidence_score', 0) / 100,
                        content_samples=competitor.get('tags', []),
                        tags=competitor.get('tags', []),
                        metadata={
                            'discovered_via': competitor.get('discovered_via'),
                            'discovery_signals': competitor.get('discovery_signals', 1),
                            'match_reason': competitor.get('match_reason', ''),
                            'source_username': source_username
                        }
                    )
                    self.db.add(creator)
                    logger.info(f"  ✅ Added new creator: {creator.handle}")
                else:
                    # Update existing creator (increment discovery count)
                    if creator.metadata:
                        creator.metadata['discovery_count'] = creator.metadata.get('discovery_count', 0) + 1
                    creator.updated_at = datetime.utcnow()
                    logger.info(f"  ♻️  Updated existing creator: {creator.handle}")
                
                self.db.commit()
                
            except Exception as e:
                logger.error(f"  ❌ Failed to store {competitor.get('username')}: {e}")
                self.db.rollback()
                continue
    
    def get_learned_competitors(
        self,
        niche: str,
        limit: int = 20,
        min_discovery_count: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get competitors learned from previous discoveries.
        Prioritizes frequently discovered creators.
        """
        logger.info(f"🧠 Fetching learned competitors for niche: {niche}...")
        
        try:
            creators = self.db.query(Creator).filter(
                Creator.niche.ilike(f"%{niche}%")
            ).order_by(
                desc(Creator.updated_at)
            ).limit(limit * 2).all()  # Fetch more for filtering
            
            competitors = []
            for creator in creators:
                # Get discovery count from metadata
                discovery_count = 0
                if creator.metadata:
                    discovery_count = creator.metadata.get('discovery_count', 1)
                
                # Filter by minimum discoveries
                if discovery_count >= min_discovery_count:
                    competitors.append({
                        'name': creator.name,
                        'username': creator.handle,
                        'subs': self._format_subscriber_count(creator.subscriber_count),
                        'avatar': None,
                        'tags': creator.tags or [],
                        'confidence_score': creator.avg_engagement_rate * 100,
                        'match_reason': f"Discovered {discovery_count} times",
                        'creator_id': creator.handle,
                        'platform': creator.platform,
                        'discovery_count': discovery_count
                    })
            
            # Sort by discovery count
            competitors.sort(key=lambda x: x['discovery_count'], reverse=True)
            
            logger.info(f"  ✅ Found {len(competitors)} learned competitors")
            return competitors[:limit]
            
        except Exception as e:
            logger.error(f"  ❌ Failed to fetch learned competitors: {e}")
            return []
    
    def learn_from_selection(
        self,
        selected_usernames: List[str],
        rejected_usernames: List[str],
        niche: str
    ) -> None:
        """
        Learn from user's selections and rejections.
        Adjusts confidence scores for future recommendations.
        """
        logger.info(f"📖 Learning from selections...")
        
        try:
            # Boost selected creators
            for username in selected_usernames:
                creator = self.db.query(Creator).filter_by(
                    handle=username
                ).first()
                
                if creator:
                    # Increase engagement rate (proxy for quality)
                    creator.avg_engagement_rate = min(
                        creator.avg_engagement_rate * 1.1,
                        1.0
                    )
                    
                    # Update metadata
                    if creator.metadata:
                        creator.metadata['selection_count'] = creator.metadata.get('selection_count', 0) + 1
                    
                    logger.info(f"  ✅ Boosted: {username}")
            
            # Reduce score for rejected creators
            for username in rejected_usernames:
                creator = self.db.query(Creator).filter_by(
                    handle=username
                ).first()
                
                if creator:
                    # Decrease engagement rate
                    creator.avg_engagement_rate = max(
                        creator.avg_engagement_rate * 0.9,
                        0.1
                    )
                    
                    # Update metadata
                    if creator.metadata:
                        creator.metadata['rejection_count'] = creator.metadata.get('rejection_count', 0) + 1
                    
                    logger.info(f"  ⬇️  Reduced: {username}")
            
            self.db.commit()
            logger.info(f"  ✅ Learning complete")
            
        except Exception as e:
            logger.error(f"  ❌ Learning failed: {e}")
            self.db.rollback()
    
    def get_trending_competitors(
        self,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get competitors that are trending (frequently discovered recently).
        """
        logger.info(f"📈 Fetching trending competitors (last {days} days)...")
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            creators = self.db.query(Creator).filter(
                Creator.updated_at >= cutoff_date
            ).order_by(
                desc(Creator.updated_at)
            ).limit(limit).all()
            
            competitors = []
            for creator in creators:
                competitors.append({
                    'name': creator.name,
                    'username': creator.handle,
                    'subs': self._format_subscriber_count(creator.subscriber_count),
                    'avatar': None,
                    'tags': creator.tags or [],
                    'confidence_score': creator.avg_engagement_rate * 100,
                    'match_reason': "Trending recently",
                    'creator_id': creator.handle,
                    'platform': creator.platform
                })
            
            logger.info(f"  ✅ Found {len(competitors)} trending competitors")
            return competitors
            
        except Exception as e:
            logger.error(f"  ❌ Failed to fetch trending: {e}")
            return []
    
    def _parse_subscriber_count(self, subs_str: str) -> int:
        """Parse subscriber string to number"""
        try:
            if '-' in subs_str:
                # "100K - 500K" -> take average
                parts = subs_str.split('-')
                low = self._parse_single_count(parts[0].strip())
                high = self._parse_single_count(parts[1].strip())
                return (low + high) // 2
            else:
                return self._parse_single_count(subs_str)
        except:
            return 0
    
    def _parse_single_count(self, count_str: str) -> int:
        """Parse single count string"""
        count_str = count_str.strip().upper()
        if 'M' in count_str:
            return int(float(count_str.replace('M', '')) * 1000000)
        elif 'K' in count_str:
            return int(float(count_str.replace('K', '')) * 1000)
        else:
            return int(count_str)
    
    def _format_subscriber_count(self, count: int) -> str:
        """Format subscriber count to string"""
        if count >= 1000000:
            return f"{count / 1000000:.1f}M"
        elif count >= 1000:
            return f"{count / 1000:.0f}K"
        else:
            return str(count)


def get_learning_system(db: Session):
    """Get learning system instance"""
    return CompetitorLearningSystem(db)
