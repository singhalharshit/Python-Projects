"""
Redis Cache Service
"""
import logging
import json
import os
from typing import Optional, Any
from datetime import timedelta
import redis

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based caching for recommendations and signals.
    
    Features:
    - Recommendation caching (24h TTL)
    - Signal caching
    - User preference caching
    - Automatic serialization/deserialization
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if self.redis_client is None:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def cache_recommendation(
        self,
        user_id: str,
        decision: dict,
        ttl: int = 86400  # 24 hours
    ):
        """
        Cache daily recommendation.
        
        Args:
            user_id: User ID
            decision: DailyDecision dict
            ttl: Time to live in seconds (default 24h)
        """
        if not self.is_available():
            logger.warning("Redis not available, skipping cache")
            return
        
        try:
            from datetime import date
            
            key = f"recommendation:{user_id}:{date.today()}"
            value = json.dumps(decision)
            
            self.redis_client.setex(key, ttl, value)
            
            logger.info(f"Cached recommendation for {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to cache recommendation: {e}")
    
    def get_cached_recommendation(
        self,
        user_id: str
    ) -> Optional[dict]:
        """
        Get cached recommendation.
        
        Args:
            user_id: User ID
        
        Returns:
            DailyDecision dict or None
        """
        if not self.is_available():
            return None
        
        try:
            from datetime import date
            
            key = f"recommendation:{user_id}:{date.today()}"
            value = self.redis_client.get(key)
            
            if value:
                logger.info(f"Cache hit for {user_id}")
                return json.loads(value)
            
            logger.info(f"Cache miss for {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached recommendation: {e}")
            return None
    
    def cache_signals(
        self,
        niche_id: str,
        signals: list,
        ttl: int = 7200  # 2 hours
    ):
        """
        Cache signals for a niche.
        
        Args:
            niche_id: Niche ID
            signals: List of signal dicts
            ttl: Time to live in seconds (default 2h)
        """
        if not self.is_available():
            return
        
        try:
            key = f"signals:{niche_id}"
            value = json.dumps(signals)
            
            self.redis_client.setex(key, ttl, value)
            
            logger.info(f"Cached {len(signals)} signals for niche {niche_id}")
            
        except Exception as e:
            logger.error(f"Failed to cache signals: {e}")
    
    def get_cached_signals(self, niche_id: str) -> Optional[list]:
        """
        Get cached signals.
        
        Args:
            niche_id: Niche ID
        
        Returns:
            List of signal dicts or None
        """
        if not self.is_available():
            return None
        
        try:
            key = f"signals:{niche_id}"
            value = self.redis_client.get(key)
            
            if value:
                return json.loads(value)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached signals: {e}")
            return None
    
    def cache_user_preference(
        self,
        user_id: str,
        preference_vector: list,
        ttl: int = 86400  # 24 hours
    ):
        """
        Cache user preference vector.
        
        Args:
            user_id: User ID
            preference_vector: Preference vector as list
            ttl: Time to live in seconds
        """
        if not self.is_available():
            return
        
        try:
            key = f"preference:{user_id}"
            value = json.dumps(preference_vector)
            
            self.redis_client.setex(key, ttl, value)
            
        except Exception as e:
            logger.error(f"Failed to cache preference: {e}")
    
    def get_cached_preference(self, user_id: str) -> Optional[list]:
        """
        Get cached preference vector.
        
        Args:
            user_id: User ID
        
        Returns:
            Preference vector as list or None
        """
        if not self.is_available():
            return None
        
        try:
            key = f"preference:{user_id}"
            value = self.redis_client.get(key)
            
            if value:
                return json.loads(value)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached preference: {e}")
            return None
    
    def invalidate_user_cache(self, user_id: str):
        """
        Invalidate all cache entries for a user.
        
        Args:
            user_id: User ID
        """
        if not self.is_available():
            return
        
        try:
            # Find all keys for this user
            pattern = f"*:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.is_available():
            return {
                'status': 'unavailable',
                'connected': False
            }
        
        try:
            info = self.redis_client.info()
            
            return {
                'status': 'available',
                'connected': True,
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_keys': self.redis_client.dbsize()
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# Global instance
_cache_service = None


def get_cache_service() -> CacheService:
    """Get global cache service instance"""
    global _cache_service
    
    if _cache_service is None:
        _cache_service = CacheService()
    
    return _cache_service
