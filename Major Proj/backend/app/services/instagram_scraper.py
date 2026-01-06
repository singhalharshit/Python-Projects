"""
Instagram Scraper Service
Fetches real Instagram data for competitor discovery
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class InstagramScraper:
    """
    Scrapes Instagram data using instaloader.
    
    Features:
    - Get user profiles (followers, posts, bio)
    - Get similar accounts (via followers/hashtags)
    - Rate limit handling
    - Caching to avoid IP bans
    """
    
    def __init__(self, cache_duration_hours: int = 24):
        self.cache_duration_hours = cache_duration_hours
        self.cache = {}
        self.last_request_time = None
        self.min_request_interval = 6  # seconds between requests
        
        # Try to import instaloader
        try:
            import instaloader
            self.L = instaloader.Instaloader(
                # ✅ Use better settings to avoid blocks
                quiet=True,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
            )
            self.available = True
            logger.info("✅ Instagram scraper initialized (instaloader)")
        except ImportError:
            self.L = None
            self.available = False
            logger.warning(
                "⚠️  instaloader not installed. "
                "Run: pip install instaloader"
            )
    
    def _rate_limit_wait(self):
        """Wait to respect rate limits"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed
                logger.debug(f"Rate limit: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if still valid"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600
            
            if age_hours < self.cache_duration_hours:
                logger.debug(f"Cache hit: {key} (age: {age_hours:.1f}h)")
                return data
        
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Cache data"""
        self.cache[key] = (data, datetime.now())
    
    def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get Instagram profile data.
        
        Args:
            username: Instagram username
        
        Returns:
            Profile dict or None
        """
        if not self.available:
            logger.warning("Instagram scraper not available")
            return None
        
        # Check cache
        cache_key = f"profile:{username}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        # ✅ Try multiple times with different approaches
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                self._rate_limit_wait()
                
                logger.info(f"Fetching Instagram profile: @{username} (attempt {attempt + 1}/{max_retries})")
                
                import instaloader
                profile = instaloader.Profile.from_username(
                    self.L.context,
                    username
                )
                
                data = {
                    'username': profile.username,
                    'full_name': profile.full_name,
                    'biography': profile.biography,
                    'followers': profile.followers,
                    'following': profile.followees,
                    'posts': profile.mediacount,
                    'profile_pic_url': profile.profile_pic_url,
                    'is_verified': profile.is_verified,
                    'is_business_account': profile.is_business_account,
                    'external_url': profile.external_url,
                    'fetched_at': datetime.now().isoformat()
                }
                
                self._set_cache(cache_key, data)
                logger.info(f"✅ Fetched @{username}: {data['followers']} followers")
                
                return data
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for @{username}: {e}")
                
                if attempt < max_retries - 1:
                    # Wait longer between retries
                    import time
                    wait_time = (attempt + 1) * 10  # 10s, 20s, 30s
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed for @{username}")
                    return None
        
        return None
    
    def find_similar_accounts(
        self,
        username: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find similar Instagram accounts.
        
        Strategy:
        1. Get target user's followers
        2. Check who those followers also follow
        3. Filter for accounts that look like creators
        
        Args:
            username: Target username
            limit: Max accounts to return
        
        Returns:
            List of similar account dicts
        """
        if not self.available:
            logger.warning("Instagram scraper not available")
            return []
        
        # Check cache
        cache_key = f"similar:{username}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            logger.info(f"Finding similar accounts to @{username}")
            
            # Get target profile
            self._rate_limit_wait()
            target_profile = instaloader.Profile.from_username(
                self.L.context,
                username
            )
            
            similar_accounts = []
            checked_count = 0
            max_followers_to_check = 10  # Only check first 10 followers
            
            # Get followers
            logger.info(f"Analyzing @{username}'s network...")
            for follower in target_profile.get_followers():
                if checked_count >= max_followers_to_check:
                    break
                
                checked_count += 1
                self._rate_limit_wait()
                
                # Check who this follower follows
                try:
                    following_count = 0
                    max_following_to_check = 5
                    
                    for following in follower.get_followees():
                        if following_count >= max_following_to_check:
                            break
                        
                        following_count += 1
                        
                        # Skip if already added or is target user
                        if following.username == username:
                            continue
                        
                        if any(a['username'] == following.username for a in similar_accounts):
                            continue
                        
                        # Filter: must be a creator
                        # (has posts, has followers, not too huge)
                        if (following.mediacount >= 20 and
                            following.followers >= 1000 and
                            following.followers <= 500000):
                            
                            similar_accounts.append({
                                'username': following.username,
                                'full_name': following.full_name,
                                'followers': following.followers,
                                'posts': following.mediacount,
                                'profile_pic_url': following.profile_pic_url,
                                'biography': following.biography
                            })
                            
                            logger.info(
                                f"  Found: @{following.username} "
                                f"({following.followers} followers)"
                            )
                            
                            if len(similar_accounts) >= limit:
                                break
                
                except Exception as inner_e:
                    logger.debug(f"Error checking follower: {inner_e}")
                    continue
                
                if len(similar_accounts) >= limit:
                    break
            
            self._set_cache(cache_key, similar_accounts)
            logger.info(
                f"✅ Found {len(similar_accounts)} similar accounts "
                f"to @{username}"
            )
            
            return similar_accounts
            
        except Exception as e:
            logger.error(f"Failed to find similar accounts: {e}")
            return []
    
    def search_by_hashtag(
        self,
        hashtag: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find creators using a specific hashtag.
        
        Args:
            hashtag: Hashtag to search (without #)
            limit: Max accounts to return
        
        Returns:
            List of creator dicts
        """
        if not self.available:
            logger.warning("Instagram scraper not available")
            return []
        
        # Check cache
        cache_key = f"hashtag:{hashtag}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            logger.info(f"Searching hashtag: #{hashtag}")
            self._rate_limit_wait()
            
            # Note: This requires login for instaloader
            # For now, return empty list
            # In production, you'd need authentication
            logger.warning("Hashtag search requires authentication")
            return []
            
        except Exception as e:
            logger.error(f"Failed to search hashtag: {e}")
            return []


# Global instance
_instagram_scraper = None


def get_instagram_scraper() -> InstagramScraper:
    """Get or create Instagram scraper instance"""
    global _instagram_scraper
    
    if _instagram_scraper is None:
        _instagram_scraper = InstagramScraper()
    
    return _instagram_scraper
