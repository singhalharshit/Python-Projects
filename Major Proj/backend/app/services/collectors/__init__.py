"""
Collectors package - exports all data collectors
"""
from app.services.collectors.google_trends_collector import GoogleTrendsCollector
from app.services.collectors.google_news_collector import GoogleNewsCollector

# Optional collectors (require API keys and additional dependencies)
try:
    from app.services.collectors.youtube_collector import YouTubeCollector
except ImportError:
    YouTubeCollector = None

try:
    from app.services.collectors.reddit_collector import RedditCollector
except ImportError:
    RedditCollector = None

__all__ = [
    "GoogleTrendsCollector",
    "GoogleNewsCollector",
    "YouTubeCollector",
    "RedditCollector",
]
