"""
YouTube data collector using YouTube Data API v3
"""
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import Counter
import logging
from app.core.config import settings
from app.core.resilience import with_circuit_breaker

logger = logging.getLogger(__name__)


class YouTubeCollector:
    """Collects trend signals from YouTube using Data API v3"""
    
    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
    
    @with_circuit_breaker("youtube")
    def collect_niche_signals(
        self,
        keywords: List[str],
        niche: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Collect trending signals from YouTube based on keywords
        
        Args:
            keywords: Search keywords for the niche
            niche: Niche identifier
            max_results: Number of videos to analyze
        
        Returns:
            Dictionary with trending topics and engagement metrics
        """
        logger.info(f"Collecting YouTube signals for {niche} with keywords: {keywords}")
        
        all_videos = []
        all_topics = []
        
        for keyword in keywords:
            try:
                # Search for recent videos (last 7 days)
                published_after = (datetime.utcnow() - timedelta(days=7)).isoformat("T") + "Z"
                
                search_response = self.youtube.search().list(
                    q=keyword,
                    part="snippet",
                    type="video",
                    order="viewCount",  # Most viewed first
                    publishedAfter=published_after,
                    maxResults=max_results
                ).execute()
                
                video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
                
                if not video_ids:
                    continue
                
                # Get detailed statistics
                videos_response = self.youtube.videos().list(
                    part="statistics,snippet",
                    id=",".join(video_ids)
                ).execute()
                
                for video in videos_response.get("items", []):
                    stats = video["statistics"]
                    snippet = video["snippet"]
                    
                    # Extract topics from title and tags
                    topics = self._extract_topics(
                        snippet.get("title", ""),
                        snippet.get("tags", [])
                    )
                    all_topics.extend(topics)
                    
                    all_videos.append({
                        "id": video["id"],
                        "title": snippet.get("title"),
                        "channel": snippet.get("channelTitle"),
                        "published": snippet.get("publishedAt"),
                        "views": int(stats.get("viewCount", 0)),
                        "likes": int(stats.get("likeCount", 0)),
                        "comments": int(stats.get("commentCount", 0)),
                        "url": f"https://youtube.com/watch?v={video['id']}"
                    })
                
                logger.info(f"Collected {len(video_ids)} videos for keyword '{keyword}'")
                
            except Exception as e:
                logger.error(f"Error collecting YouTube data for '{keyword}': {e}")
                continue
        
        # Analyze trending topics
        trending_topics = self._identify_trending_topics(all_topics, all_videos)
        
        # Calculate engagement metrics
        engagement_metrics = self._calculate_engagement_metrics(all_videos)
        
        return {
            "source": "youtube",
            "niche": niche,
            "trending_topics": trending_topics,
            "engagement_metrics": engagement_metrics,
            "total_videos_analyzed": len(all_videos),
            "keywords": keywords,
            "timestamp": datetime.utcnow(),
            "top_videos": all_videos[:5]  # Keep top 5 for reference
        }
    
    def _extract_topics(self, title: str, tags: List[str]) -> List[str]:
        """Extract topic keywords from video title and tags"""
        topics = []
        
        # Add tags directly
        topics.extend([tag.lower() for tag in tags])
        
        # Extract from title (similar to Reddit)
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "is", "are", "was", "were", "how", "what", "why"
        }
        
        words = title.lower().split()
        title_topics = [w.strip(".,!?;:()[]{}\"'") for w in words if len(w) > 3]
        title_topics = [t for t in title_topics if t not in stop_words]
        
        topics.extend(title_topics)
        
        return topics
    
    def _identify_trending_topics(
        self,
        all_topics: List[str],
        all_videos: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Identify trending topics based on frequency and engagement"""
        
        topic_counts = Counter(all_topics)
        top_topics = topic_counts.most_common(10)
        
        trending = []
        for topic, count in top_topics:
            # Find videos containing this topic
            related_videos = [
                v for v in all_videos
                if topic in v["title"].lower()
            ]
            
            if not related_videos:
                continue
            
            # Calculate momentum based on views and engagement
            avg_views = sum(v["views"] for v in related_videos) / len(related_videos)
            avg_likes = sum(v["likes"] for v in related_videos) / len(related_videos)
            avg_comments = sum(v["comments"] for v in related_videos) / len(related_videos)
            
            # Engagement rate (likes + comments relative to views)
            engagement_rate = (avg_likes + avg_comments) / max(avg_views, 1)
            
            momentum = (count * 0.3) + (avg_views / 10000 * 0.4) + (engagement_rate * 100 * 0.3)
            
            trending.append({
                "topic": topic,
                "frequency": count,
                "momentum_score": min(momentum / 100, 1.0),
                "avg_views": int(avg_views),
                "avg_engagement_rate": engagement_rate,
                "sample_videos": [v["title"] for v in related_videos[:2]]
            })
        
        trending.sort(key=lambda x: x["momentum_score"], reverse=True)
        
        return trending
    
    def _calculate_engagement_metrics(self, videos: List[Dict]) -> Dict[str, float]:
        """Calculate overall engagement metrics"""
        
        if not videos:
            return {
                "avg_views": 0,
                "avg_likes": 0,
                "avg_comments": 0,
                "engagement_velocity": 0.0
            }
        
        avg_views = sum(v["views"] for v in videos) / len(videos)
        avg_likes = sum(v["likes"] for v in videos) / len(videos)
        avg_comments = sum(v["comments"] for v in videos) / len(videos)
        
        # Velocity based on recent activity
        # Assuming 10K views, 500 likes, 100 comments is "high"
        velocity = min(
            (avg_views / 10000) * 0.5 +
            (avg_likes / 500) * 0.3 +
            (avg_comments / 100) * 0.2,
            1.0
        )
        
        return {
            "avg_views": int(avg_views),
            "avg_likes": int(avg_likes),
            "avg_comments": int(avg_comments),
            "engagement_velocity": velocity
        }
