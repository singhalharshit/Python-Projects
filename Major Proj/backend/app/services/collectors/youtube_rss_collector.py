"""
YouTube RSS Collector - Tracks competitor activity efficiently without API keys
"""
from typing import List, Dict, Any, Optional
import feedparser
import logging
from datetime import datetime, timedelta
import time
import re
from app.core.resilience import with_circuit_breaker

logger = logging.getLogger(__name__)

class YouTubeRSSCollector:
    """
    Collects recent videos from YouTube channels using public RSS feeds.
    URL Format: https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}
    
    Why RSS?
    - No API Key required
    - No quota limits (unlike Data API which has 10,000 unit limit)
    - Real-time updates for new uploads
    """
    
    BASE_URL = "https://www.youtube.com/feeds/videos.xml?channel_id="
    
    def __init__(self):
        self.session = None  # feedparser uses urllib internally/requests
        
    @with_circuit_breaker("youtube_rss")
    def get_recent_videos(self, channel_id: str, max_days: int = 7) -> List[Dict[str, Any]]:
        """
        Get videos uploaded by a channel in the last X days
        """
        feed_url = f"{self.BASE_URL}{channel_id}"
        
        try:
            logger.info(f"Fetching RSS feed for channel: {channel_id}")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:  # feedparser error flag
                logger.warning(f"Error parsing feed for {channel_id}: {feed.bozo_exception}")
                return []
            
            if not feed.entries:
                logger.info(f"No videos found for channel {channel_id}")
                return []
                
            recent_videos = []
            cutoff_date = datetime.utcnow() - timedelta(days=max_days)
            
            for entry in feed.entries:
                # published_parsed is a time.struct_time
                if not hasattr(entry, 'published_parsed'):
                    continue
                    
                pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                
                if pub_date > cutoff_date:
                    video_data = {
                        'video_id': entry.yt_videoid,
                        'title': entry.title,
                        'link': entry.link,
                        'published_at': pub_date.isoformat(),
                        'views': entry.media_statistics['views'] if 'media_statistics' in entry else 0,
                        'channel_title': feed.feed.title if 'title' in feed.feed else "Unknown Channel"
                    }
                    recent_videos.append(video_data)
            
            logger.info(f"Found {len(recent_videos)} recent videos for {channel_id}")
            return recent_videos
            
        except Exception as e:
            logger.error(f"Failed to fetch YouTube RSS for {channel_id}: {e}")
            return []

    def check_competitor_saturation(self, topic: str, competitor_ids: List[str]) -> Dict[str, Any]:
        """
        Check if competitors have covered a specific topic recently.
        Returns saturation details.
        """
        covered_by = []
        recent_videos_found = []
        
        # Normalize topic for checking
        topic_words = set(topic.lower().split())
        
        for channel_id in competitor_ids:
            videos = self.get_recent_videos(channel_id, max_days=14) # Check last 2 weeks
            
            for video in videos:
                title_lower = video['title'].lower()
                # Simple keyword matching
                # In Phase 4, use proper NLP similarity
                if any(word in title_lower for word in topic_words if len(word) > 3):
                    covered_by.append(video['channel_title'])
                    recent_videos_found.append(video)
                    break # Count once per competitor
        
        is_saturated = len(covered_by) > 0
        
        return {
            "is_saturated": is_saturated,
            "covered_by": list(set(covered_by)),
            "videos": recent_videos_found,
            "saturation_score": len(covered_by) / len(competitor_ids) if competitor_ids else 0
        }
