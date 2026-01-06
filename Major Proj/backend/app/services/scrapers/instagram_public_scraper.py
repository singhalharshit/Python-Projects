"""
Instagram Public Scraper
Ethical scraping using only public endpoints - NO LOGIN REQUIRED

Features:
- Profile data (bio, followers, posts)
- Recent posts (captions, hashtags, mentions, audio)
- Hashtag exploration
- Audio/reel exploration
- Rate limiting and caching
"""
import logging
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class InstagramPublicScraper:
    """
    Scrapes Instagram using only public data.
    
    Ethical Guidelines:
    - NO login required
    - NO private follower lists
    - NO DMs or stories
    - Only public profiles
    - Respects rate limits
    """
    
    def __init__(self, cache_duration_hours: int = 24):
        self.cache = {}
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.last_request_time = None
        self.min_delay_seconds = 2  # Minimum 2 seconds between requests
        self.max_delay_seconds = 5  # Maximum 5 seconds between requests
        self.failure_count = 0
        self.max_failures = 3  # Circuit breaker threshold
        
        # User agent to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def _rate_limit_wait(self):
        """Wait to respect rate limits"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            delay = self.min_delay_seconds + (self.max_delay_seconds - self.min_delay_seconds) * 0.5
            
            if elapsed < delay:
                wait_time = delay - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if still valid"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.cache_duration:
                logger.debug(f"Cache hit: {key}")
                return data
            else:
                del self.cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Cache data"""
        self.cache[key] = (data, datetime.now())
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker is open"""
        if self.failure_count >= self.max_failures:
            logger.error(f"Circuit breaker open: {self.failure_count} consecutive failures")
            raise Exception("Instagram scraper circuit breaker open - too many failures")
    
    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get Instagram profile data (public only).
        
        Args:
            username: Instagram username
        
        Returns:
            Profile dict or None
        """
        cache_key = f"profile:{username}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        self._check_circuit_breaker()
        self._rate_limit_wait()
        
        try:
            # Use Instagram's public JSON endpoint (no login required)
            url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 404:
                logger.warning(f"Profile not found: {username}")
                return None
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch profile {username}: {response.status_code}")
                self.failure_count += 1
                return None
            
            # Reset failure count on success
            self.failure_count = 0
            
            # Parse JSON response
            try:
                data = response.json()
                user_data = data.get('graphql', {}).get('user', {})
                
                if not user_data:
                    # Try alternative JSON structure
                    user_data = data.get('user', {})
                
                profile = {
                    'id': user_data.get('id'),
                    'username': username,
                    'full_name': user_data.get('full_name'),
                    'bio': user_data.get('biography', ''),
                    'follower_count': user_data.get('edge_followed_by', {}).get('count', 0),
                    'following_count': user_data.get('edge_follow', {}).get('count', 0),
                    'post_count': user_data.get('edge_owner_to_timeline_media', {}).get('count', 0),
                    'verified': user_data.get('is_verified', False),
                    'category': user_data.get('category_name'),
                    'profile_pic_url': user_data.get('profile_pic_url_hd'),
                    'is_private': user_data.get('is_private', False),
                    'scraped_at': datetime.now().isoformat()
                }
                
                self._set_cache(cache_key, profile)
                logger.info(f"Successfully scraped profile: {username}")
                return profile
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON for {username}")
                self.failure_count += 1
                return None
                
        except requests.RequestException as e:
            logger.error(f"Request failed for {username}: {e}")
            self.failure_count += 1
            return None
    
    def get_recent_posts(self, username: str, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Get recent posts from a profile.
        
        Args:
            username: Instagram username
            limit: Max posts to return
        
        Returns:
            List of post dicts
        """
        cache_key = f"posts:{username}:{limit}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        self._check_circuit_breaker()
        self._rate_limit_wait()
        
        try:
            url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch posts for {username}: {response.status_code}")
                self.failure_count += 1
                return []
            
            self.failure_count = 0
            
            data = response.json()
            user_data = data.get('graphql', {}).get('user', {}) or data.get('user', {})
            edges = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
            
            posts = []
            for edge in edges[:limit]:
                node = edge.get('node', {})
                
                # Extract hashtags from caption
                caption = node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', '')
                hashtags = re.findall(r'#(\w+)', caption)
                mentions = re.findall(r'@(\w+)', caption)
                
                post = {
                    'id': node.get('id'),
                    'shortcode': node.get('shortcode'),
                    'caption': caption,
                    'hashtags': hashtags,
                    'mentions': mentions,
                    'post_type': 'video' if node.get('is_video') else 'image',
                    'likes': node.get('edge_liked_by', {}).get('count', 0),
                    'comments': node.get('edge_media_to_comment', {}).get('count', 0),
                    'views': node.get('video_view_count', 0),
                    'posted_at': datetime.fromtimestamp(node.get('taken_at_timestamp', 0)).isoformat(),
                    'url': f"https://www.instagram.com/p/{node.get('shortcode')}/"
                }
                
                posts.append(post)
            
            self._set_cache(cache_key, posts)
            logger.info(f"Successfully scraped {len(posts)} posts for {username}")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to get posts for {username}: {e}")
            self.failure_count += 1
            return []
    
    def search_hashtag(self, hashtag: str, limit: int = 50) -> List[str]:
        """
        Find creators using a specific hashtag.
        
        Args:
            hashtag: Hashtag to search (without #)
            limit: Max creators to return
        
        Returns:
            List of usernames
        """
        cache_key = f"hashtag:{hashtag}:{limit}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        self._check_circuit_breaker()
        self._rate_limit_wait()
        
        try:
            url = f"https://www.instagram.com/explore/tags/{hashtag}/?__a=1&__d=dis"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to search hashtag {hashtag}: {response.status_code}")
                self.failure_count += 1
                return []
            
            self.failure_count = 0
            
            data = response.json()
            hashtag_data = data.get('graphql', {}).get('hashtag', {}) or data.get('hashtag', {})
            edges = hashtag_data.get('edge_hashtag_to_media', {}).get('edges', [])
            
            usernames = set()
            for edge in edges[:limit]:
                node = edge.get('node', {})
                owner = node.get('owner', {})
                username = owner.get('username')
                if username:
                    usernames.add(username)
            
            result = list(usernames)
            self._set_cache(cache_key, result)
            logger.info(f"Found {len(result)} creators for hashtag #{hashtag}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to search hashtag {hashtag}: {e}")
            self.failure_count += 1
            return []
    
    def search_audio(self, audio_name: str, limit: int = 50) -> List[str]:
        """
        Find creators using specific audio (for reels).
        
        Note: This is more limited as Instagram doesn't have a public audio search API.
        We'll return empty for now and rely on other discovery paths.
        
        Args:
            audio_name: Audio name to search
            limit: Max creators to return
        
        Returns:
            List of usernames
        """
        logger.warning("Audio search not implemented - Instagram doesn't provide public audio search")
        return []


# Global instance
_instagram_scraper = None


def get_instagram_public_scraper() -> InstagramPublicScraper:
    """Get or create Instagram scraper instance"""
    global _instagram_scraper
    if _instagram_scraper is None:
        _instagram_scraper = InstagramPublicScraper()
    return _instagram_scraper
