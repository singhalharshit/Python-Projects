"""
Circuit breaker pattern, rate limiting, and graceful degradation utilities
"""
import time
import asyncio
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failure threshold exceeded, requests fail fast
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = None,
        timeout: int = None
    ):
        self.name = name
        self.failure_threshold = failure_threshold or settings.CIRCUIT_BREAKER_THRESHOLD
        self.timeout = timeout or settings.CIRCUIT_BREAKER_TIMEOUT
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        # Check if we should transition from OPEN to HALF_OPEN
        if self.state == "OPEN":
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).seconds > self.timeout:
                logger.info(f"Circuit breaker {self.name}: OPEN -> HALF_OPEN")
                self.state = "HALF_OPEN"
            else:
                logger.warning(f"Circuit breaker {self.name} is OPEN, failing fast")
                raise CircuitBreakerOpen(f"Circuit breaker {self.name} is open")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset if we were in HALF_OPEN
            if self.state == "HALF_OPEN":
                logger.info(f"Circuit breaker {self.name}: HALF_OPEN -> CLOSED")
                self.state = "CLOSED"
                self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            logger.error(f"Circuit breaker {self.name} failure {self.failure_count}/{self.failure_threshold}: {e}")
            
            # Transition to OPEN if threshold exceeded
            if self.failure_count >= self.failure_threshold:
                logger.error(f"Circuit breaker {self.name}: CLOSED -> OPEN")
                self.state = "OPEN"
            
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Async version of call"""
        
        if self.state == "OPEN":
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).seconds > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpen(f"Circuit breaker {self.name} is open")
        
        try:
            result = await func(*args, **kwargs)
            
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e


class RateLimiter:
    """
    Token bucket rate limiter for API calls
    """
    
    def __init__(self, calls_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self.tokens = calls_per_minute
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until a token is available"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Refill tokens based on elapsed time
            self.tokens = min(
                self.calls_per_minute,
                self.tokens + (elapsed * self.calls_per_minute / 60)
            )
            self.last_update = now
            
            if self.tokens < 1:
                # Wait until next token is available
                wait_time = (1 - self.tokens) * 60 / self.calls_per_minute
                await asyncio.sleep(wait_time)
                self.tokens = 1
            
            self.tokens -= 1
    
    def acquire_sync(self):
        """Synchronous version of acquire"""
        now = time.time()
        elapsed = now - self.last_update
        
        self.tokens = min(
            self.calls_per_minute,
            self.tokens + (elapsed * self.calls_per_minute / 60)
        )
        self.last_update = now
        
        if self.tokens < 1:
            wait_time = (1 - self.tokens) * 60 / self.calls_per_minute
            time.sleep(wait_time)
            self.tokens = 1
        
        self.tokens -= 1


# Global circuit breakers for each data source
circuit_breakers = {
    "reddit": CircuitBreaker("reddit"),
    "youtube": CircuitBreaker("youtube"),
    "github": CircuitBreaker("github"),
    "hackernews": CircuitBreaker("hackernews"),
    "rss": CircuitBreaker("rss"),
}

# Global rate limiters
rate_limiters = {
    "reddit": RateLimiter(60),  # 60 requests per minute
    "youtube": RateLimiter(10),  # Conservative for quota management
}


def with_circuit_breaker(source: str):
    """Decorator to wrap function with circuit breaker"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            breaker = circuit_breakers.get(source)
            if not breaker:
                return func(*args, **kwargs)
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


def with_rate_limit(source: str):
    """Decorator to wrap function with rate limiting"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = rate_limiters.get(source)
            if limiter and settings.RATE_LIMIT_ENABLED:
                limiter.acquire_sync()
            return func(*args, **kwargs)
        return wrapper
    return decorator
