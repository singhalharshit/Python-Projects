"""
Reddit data collector using PRAW library
"""
import praw
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import Counter
import logging
from app.core.config import settings
from app.core.resilience import with_circuit_breaker, with_rate_limit

logger = logging.getLogger(__name__)


class RedditCollector:
    """Collects trend signals from Reddit using PRAW"""
    
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT
        )
    
    @with_circuit_breaker("reddit")
    @with_rate_limit("reddit")
    def collect_niche_signals(
        self,
        subreddits: List[str],
        niche: str,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        Collect trending signals from specified subreddits
        
        Args:
            subreddits: List of subreddit names (without r/)
            niche: Niche identifier
            limit: Number of posts to analyze per subreddit
        
        Returns:
            Dictionary with trending topics and engagement metrics
        """
        logger.info(f"Collecting Reddit signals for {niche} from {len(subreddits)} subreddits")
        
        all_topics = []
        all_posts = []
        engagement_data = []
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get hot posts (most recent trending)
                hot_posts = list(subreddit.hot(limit=limit))
                
                for post in hot_posts:
                    # Extract topic keywords from title
                    topics = self._extract_topics(post.title)
                    all_topics.extend(topics)
                    
                    # Track engagement metrics
                    engagement_data.append({
                        "upvotes": post.score,
                        "comments": post.num_comments,
                        "upvote_ratio": post.upvote_ratio,
                        "created_utc": datetime.fromtimestamp(post.created_utc)
                    })
                    
                    all_posts.append({
                        "id": post.id,
                        "title": post.title,
                        "subreddit": subreddit_name,
                        "url": post.url,
                        "score": post.score,
                        "comments": post.num_comments,
                        "created": datetime.fromtimestamp(post.created_utc)
                    })
                
                logger.info(f"Collected {len(hot_posts)} posts from r/{subreddit_name}")
                
            except Exception as e:
                logger.error(f"Error collecting from r/{subreddit_name}: {e}")
                continue
        
        # Analyze trending topics
        trending_topics = self._identify_trending_topics(all_topics, all_posts)
        
        # Calculate engagement velocity
        engagement_velocity = self._calculate_engagement_velocity(engagement_data)
        
        return {
            "source": "reddit",
            "niche": niche,
            "trending_topics": trending_topics,
            "engagement_velocity": engagement_velocity,
            "total_posts_analyzed": len(all_posts),
            "subreddits": subreddits,
            "timestamp": datetime.utcnow(),
            "raw_posts": all_posts[:10]  # Keep top 10 for reference
        }
    
    def _extract_topics(self, title: str) -> List[str]:
        """
        Extract topic keywords from post title
        Simple keyword extraction - can be enhanced with NLP
        """
        # Remove common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "should",
            "could", "may", "might", "must", "can", "i", "you", "he", "she", "it",
            "we", "they", "what", "which", "who", "when", "where", "why", "how"
        }
        
        # Simple tokenization
        words = title.lower().split()
        topics = [w.strip(".,!?;:()[]{}\"'") for w in words if len(w) > 3]
        topics = [t for t in topics if t not in stop_words]
        
        return topics
    
    def _identify_trending_topics(
        self,
        all_topics: List[str],
        all_posts: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Identify trending topics based on frequency and recency"""
        
        # Count topic frequency
        topic_counts = Counter(all_topics)
        
        # Get top topics
        top_topics = topic_counts.most_common(10)
        
        trending = []
        for topic, count in top_topics:
            # Find posts containing this topic
            related_posts = [
                p for p in all_posts
                if topic in p["title"].lower()
            ]
            
            # Calculate momentum (frequency + recency + engagement)
            avg_score = sum(p["score"] for p in related_posts) / len(related_posts) if related_posts else 0
            avg_comments = sum(p["comments"] for p in related_posts) / len(related_posts) if related_posts else 0
            
            # Recency bonus (posts from last 24 hours get higher score)
            recent_count = sum(
                1 for p in related_posts
                if (datetime.utcnow() - p["created"]).days < 1
            )
            
            momentum = (count * 0.4) + (avg_score * 0.3) + (avg_comments * 0.2) + (recent_count * 0.1)
            
            trending.append({
                "topic": topic,
                "frequency": count,
                "momentum_score": min(momentum / 100, 1.0),  # Normalize to 0-1
                "avg_engagement": avg_score,
                "recent_posts": recent_count,
                "sample_posts": [p["title"] for p in related_posts[:3]]
            })
        
        # Sort by momentum
        trending.sort(key=lambda x: x["momentum_score"], reverse=True)
        
        return trending
    
    def _calculate_engagement_velocity(
        self,
        engagement_data: List[Dict]
    ) -> float:
        """
        Calculate overall engagement velocity
        Higher velocity = more active discussion
        """
        if not engagement_data:
            return 0.0
        
        # Recent posts (last 24 hours) weighted more
        now = datetime.utcnow()
        recent_engagement = [
            e for e in engagement_data
            if (now - e["created_utc"]).days < 1
        ]
        
        if not recent_engagement:
            return 0.5  # Neutral velocity
        
        # Average engagement metrics
        avg_upvotes = sum(e["upvotes"] for e in recent_engagement) / len(recent_engagement)
        avg_comments = sum(e["comments"] for e in recent_engagement) / len(recent_engagement)
        
        # Normalize to 0-1 scale (assuming 100 upvotes and 20 comments is "high")
        velocity = min((avg_upvotes / 100) * 0.6 + (avg_comments / 20) * 0.4, 1.0)
        
        return velocity
