"""
YouTube Scraper Service
Scrapes creator data from YouTube Data API v3
"""
import logging
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class YouTubeScraper:
    """
    Scrapes creator data from YouTube using Data API v3.
    Manages quota usage and rate limiting.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube API client.
        
        Args:
            api_key: YouTube Data API key (or from env)
        """
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        
        if not self.api_key:
            logger.warning("YouTube API key not found. Set YOUTUBE_API_KEY in .env")
            self.youtube = None
        else:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                logger.info("YouTube API client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize YouTube API: {e}")
                self.youtube = None
        
        self.quota_used = 0
        self.quota_limit = 10000  # Daily limit
    
    def search_channels(
        self, 
        query: str, 
        max_results: int = 50,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Search for channels by keyword.
        
        Args:
            query: Search query (e.g., "programming tutorials")
            max_results: Number of results (max 50 per call)
            language: Language code
            
        Returns:
            List of channel data
        """
        if not self.youtube:
            logger.error("YouTube API not initialized")
            return []
        
        try:
            # Search for channels
            request = self.youtube.search().list(
                q=query,
                type='channel',
                part='snippet',
                maxResults=min(max_results, 50),
                relevanceLanguage=language,
                order='relevance'
            )
            
            response = request.execute()
            self.quota_used += 100  # Search costs 100 units
            
            channels = []
            for item in response.get('items', []):
                channel_id = item['id']['channelId']
                snippet = item['snippet']
                
                channels.append({
                    'id': channel_id,
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', '')
                })
            
            logger.info(f"Found {len(channels)} channels for query: {query}")
            return channels
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return []
    
    def get_channel_details(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a channel.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Channel details including stats and branding
        """
        if not self.youtube:
            return None
        
        try:
            request = self.youtube.channels().list(
                id=channel_id,
                part='snippet,statistics,brandingSettings'
            )
            
            response = request.execute()
            self.quota_used += 1  # Channel details costs 1 unit
            
            if not response.get('items'):
                return None
            
            item = response['items'][0]
            snippet = item.get('snippet', {})
            statistics = item.get('statistics', {})
            branding = item.get('brandingSettings', {}).get('channel', {})
            
            return {
                'id': channel_id,
                'name': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'custom_url': snippet.get('customUrl', ''),
                'subscriber_count': int(statistics.get('subscriberCount', 0)),
                'video_count': int(statistics.get('videoCount', 0)),
                'view_count': int(statistics.get('viewCount', 0)),
                'keywords': branding.get('keywords', ''),
                'country': snippet.get('country', ''),
                'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', '')
            }
            
        except HttpError as e:
            logger.error(f"Error fetching channel details: {e}")
            return None
    
    def get_recent_videos(
        self, 
        channel_id: str, 
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent videos from a channel.
        
        Args:
            channel_id: YouTube channel ID
            max_results: Number of videos to fetch
            
        Returns:
            List of video data
        """
        if not self.youtube:
            return []
        
        try:
            request = self.youtube.search().list(
                channelId=channel_id,
                type='video',
                part='snippet',
                maxResults=min(max_results, 50),
                order='date'
            )
            
            response = request.execute()
            self.quota_used += 100  # Search costs 100 units
            
            videos = []
            for item in response.get('items', []):
                snippet = item['snippet']
                videos.append({
                    'id': item['id']['videoId'],
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'published_at': snippet.get('publishedAt', '')
                })
            
            logger.info(f"Fetched {len(videos)} recent videos for channel {channel_id}")
            return videos
            
        except HttpError as e:
            logger.error(f"Error fetching videos: {e}")
            return []
    
    def extract_content_corpus(
        self, 
        channel_details: Dict[str, Any], 
        videos: List[Dict[str, Any]]
    ) -> str:
        """
        Extract text corpus from channel data for embedding generation.
        
        Args:
            channel_details: Channel metadata
            videos: Recent videos
            
        Returns:
            Combined text corpus
        """
        corpus_parts = []
        
        # Add channel description (weighted more)
        if channel_details.get('description'):
            corpus_parts.append(channel_details['description'])
            corpus_parts.append(channel_details['description'])  # Add twice for weight
        
        # Add channel keywords
        if channel_details.get('keywords'):
            corpus_parts.append(channel_details['keywords'])
        
        # Add video titles
        for video in videos:
            if video.get('title'):
                corpus_parts.append(video['title'])
        
        # Add video descriptions (first 200 chars each)
        for video in videos:
            if video.get('description'):
                corpus_parts.append(video['description'][:200])
        
        return " ".join(corpus_parts)
    
    def get_quota_status(self) -> Dict[str, int]:
        """Get current quota usage"""
        return {
            'used': self.quota_used,
            'limit': self.quota_limit,
            'remaining': self.quota_limit - self.quota_used
        }
    
    def reset_quota(self):
        """Reset daily quota counter"""
        self.quota_used = 0
        logger.info("Quota counter reset")


# Global instance
_youtube_scraper = None

def get_youtube_scraper() -> YouTubeScraper:
    """Get or create global YouTube scraper instance"""
    global _youtube_scraper
    if _youtube_scraper is None:
        _youtube_scraper = YouTubeScraper()
    return _youtube_scraper


youtube_scraper = get_youtube_scraper()
