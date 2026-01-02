"""
Google News RSS collector
No API key required - uses public RSS feeds
"""
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import Counter
import logging
from urllib.parse import quote_plus
from app.core.resilience import with_circuit_breaker

logger = logging.getLogger(__name__)


class GoogleNewsCollector:
    """Collects trend signals from Google News RSS feeds"""
    
    BASE_URL = "https://news.google.com/rss"
    
    def __init__(self):
        pass
    
    @with_circuit_breaker("google_news")
    def collect_niche_signals(
        self,
        keywords: List[str],
        niche: str,
        max_articles: int = 20,
        language: str = 'en',
        country: str = 'US'
    ) -> Dict[str, Any]:
        """
        Collect trending signals from Google News RSS feeds
        
        Args:
            keywords: Search keywords for the niche
            niche: Niche identifier
            max_articles: Maximum articles to analyze per keyword
            language: Language code (e.g., 'en', 'es')
            country: Country code (e.g., 'US', 'GB')
        
        Returns:
            Dictionary with trending topics and news metrics
        """
        logger.info(f"Collecting Google News signals for {niche} with keywords: {keywords}")
        
        all_articles = []
        all_topics = []
        
        for keyword in keywords:
            try:
                # Build RSS feed URL for search query
                search_url = f"{self.BASE_URL}/search?q={quote_plus(keyword)}&hl={language}&gl={country}&ceid={country}:{language}"
                
                # Parse RSS feed
                feed = feedparser.parse(search_url)
                
                if not feed.entries:
                    logger.warning(f"No articles found for keyword: {keyword}")
                    continue
                
                # Process articles
                for entry in feed.entries[:max_articles]:
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    
                    # Extract topics from title
                    topics = self._extract_topics(entry.title)
                    all_topics.extend(topics)
                    
                    article = {
                        "title": entry.title,
                        "link": entry.link,
                        "published": pub_date,
                        "source": entry.source.title if hasattr(entry, 'source') else "Unknown",
                        "keyword": keyword
                    }
                    
                    all_articles.append(article)
                
                logger.info(f"Collected {len(feed.entries[:max_articles])} articles for keyword '{keyword}'")
                
            except Exception as e:
                logger.error(f"Error collecting Google News data for '{keyword}': {e}")
                continue
        
        # Analyze trending topics
        trending_topics = self._identify_trending_topics(all_topics, all_articles)
        
        # Calculate news metrics
        news_metrics = self._calculate_news_metrics(all_articles, keywords)
        
        return {
            "source": "google_news",
            "niche": niche,
            "trending_topics": trending_topics,
            "news_metrics": news_metrics,
            "total_articles_analyzed": len(all_articles),
            "keywords": keywords,
            "timestamp": datetime.utcnow(),
            "recent_articles": all_articles[:10]  # Keep top 10 for reference
        }
    
    def _extract_topics(self, title: str) -> List[str]:
        """Extract topic keywords from article title"""
        
        # Common stop words to filter out
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "is", "are", "was", "were", "how", "what", "why", "when",
            "where", "who", "which", "this", "that", "these", "those", "will", "can",
            "could", "should", "would", "may", "might", "must", "has", "have", "had",
            "be", "been", "being", "do", "does", "did", "done", "doing", "says", "said"
        }
        
        # Split and clean words
        words = title.lower().split()
        topics = [w.strip(".,!?;:()[]{}\"'") for w in words if len(w) > 3]
        topics = [t for t in topics if t not in stop_words and t.isalpha()]
        
        return topics
    
    def _identify_trending_topics(
        self,
        all_topics: List[str],
        all_articles: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Identify trending topics based on frequency and recency"""
        
        topic_counts = Counter(all_topics)
        top_topics = topic_counts.most_common(15)
        
        trending = []
        now = datetime.utcnow()
        
        for topic, count in top_topics:
            # Find articles containing this topic
            related_articles = [
                a for a in all_articles
                if topic in a["title"].lower()
            ]
            
            if not related_articles:
                continue
            
            # Calculate recency score (articles in last 24 hours get higher score)
            recency_score = 0
            for article in related_articles:
                if article["published"]:
                    hours_ago = (now - article["published"]).total_seconds() / 3600
                    if hours_ago <= 24:
                        recency_score += 1.0
                    elif hours_ago <= 48:
                        recency_score += 0.5
                    elif hours_ago <= 72:
                        recency_score += 0.25
            
            # Calculate momentum (frequency + recency)
            frequency_score = min(count / 10, 1.0)  # Normalize to 0-1
            recency_normalized = min(recency_score / 5, 1.0)  # Normalize to 0-1
            
            momentum = (frequency_score * 0.5) + (recency_normalized * 0.5)
            
            # Get unique sources
            sources = list(set([a["source"] for a in related_articles]))
            
            trending.append({
                "topic": topic,
                "frequency": count,
                "momentum_score": round(momentum, 3),
                "recency_score": round(recency_normalized, 3),
                "article_count": len(related_articles),
                "sources": sources[:5],  # Top 5 sources
                "sample_headlines": [a["title"] for a in related_articles[:3]]
            })
        
        # Sort by momentum score
        trending.sort(key=lambda x: x["momentum_score"], reverse=True)
        
        return trending
    
    def _calculate_news_metrics(
        self,
        articles: List[Dict],
        keywords: List[str]
    ) -> Dict[str, Any]:
        """Calculate overall news coverage metrics"""
        
        if not articles:
            return {
                "total_articles": 0,
                "articles_per_keyword": 0,
                "unique_sources": 0,
                "coverage_velocity": 0.0,
                "recent_coverage_rate": 0.0
            }
        
        # Count articles per keyword
        articles_per_keyword = len(articles) / len(keywords) if keywords else 0
        
        # Count unique sources
        unique_sources = len(set([a["source"] for a in articles]))
        
        # Calculate coverage velocity (articles in last 24 hours)
        now = datetime.utcnow()
        recent_articles = [
            a for a in articles
            if a["published"] and (now - a["published"]).total_seconds() <= 86400  # 24 hours
        ]
        
        recent_coverage_rate = len(recent_articles) / len(articles) if articles else 0
        
        # Velocity score (0-1 scale)
        velocity = min(len(recent_articles) / 20, 1.0)  # 20+ recent articles = max velocity
        
        return {
            "total_articles": len(articles),
            "articles_per_keyword": round(articles_per_keyword, 2),
            "unique_sources": unique_sources,
            "coverage_velocity": round(velocity, 3),
            "recent_coverage_rate": round(recent_coverage_rate, 3),
            "recent_articles_24h": len(recent_articles)
        }
    
    @with_circuit_breaker("google_news")
    def get_topic_feed(
        self,
        topic: str,
        language: str = 'en',
        country: str = 'US',
        max_articles: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get articles for a specific topic
        
        Args:
            topic: Topic to search for
            language: Language code
            country: Country code
            max_articles: Maximum number of articles to return
        
        Returns:
            List of article dictionaries
        """
        try:
            search_url = f"{self.BASE_URL}/search?q={quote_plus(topic)}&hl={language}&gl={country}&ceid={country}:{language}"
            feed = feedparser.parse(search_url)
            
            articles = []
            for entry in feed.entries[:max_articles]:
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": pub_date,
                    "source": entry.source.title if hasattr(entry, 'source') else "Unknown"
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching topic feed: {e}")
            return []
    
    @with_circuit_breaker("google_news")
    def get_headlines(
        self,
        language: str = 'en',
        country: str = 'US',
        max_headlines: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get top headlines
        
        Args:
            language: Language code
            country: Country code
            max_headlines: Maximum number of headlines to return
        
        Returns:
            List of headline dictionaries
        """
        try:
            headlines_url = f"{self.BASE_URL}?hl={language}&gl={country}&ceid={country}:{language}"
            feed = feedparser.parse(headlines_url)
            
            headlines = []
            for entry in feed.entries[:max_headlines]:
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                
                headlines.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": pub_date,
                    "source": entry.source.title if hasattr(entry, 'source') else "Unknown"
                })
            
            return headlines
            
        except Exception as e:
            logger.error(f"Error fetching headlines: {e}")
            return []
