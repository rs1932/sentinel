"""
Rate limiting utilities for API endpoints
"""
from functools import wraps
from typing import Dict, Optional
import time
from collections import defaultdict, deque

from src.core.exceptions import RateLimitError


class InMemoryRateLimiter:
    """Simple in-memory rate limiter for development/testing"""
    
    def __init__(self):
        self.clients: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, key: str, calls: int, period: int) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        client_calls = self.clients[key]
        
        # Remove old calls outside the time window
        while client_calls and client_calls[0] <= now - period:
            client_calls.popleft()
        
        # Check if under limit
        if len(client_calls) < calls:
            client_calls.append(now)
            return True
        
        return False
    
    def get_reset_time(self, key: str, period: int) -> Optional[float]:
        """Get the time when rate limit will reset"""
        client_calls = self.clients.get(key)
        if not client_calls:
            return None
        
        return client_calls[0] + period


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


def rate_limit(calls: int, period: int):
    """
    Decorator for rate limiting endpoints
    
    Args:
        calls: Maximum number of calls allowed
        period: Time period in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if hasattr(arg, 'client') and hasattr(arg, 'headers'):
                    request = arg
                    break
            
            if not request:
                # Look in kwargs
                request = kwargs.get('request')
            
            if request:
                # Get client identifier (IP address)
                x_forwarded_for = request.headers.get("x-forwarded-for")
                client_ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.client.host
                
                if not rate_limiter.is_allowed(client_ip, calls, period):
                    reset_time = rate_limiter.get_reset_time(client_ip, period)
                    retry_after = int(reset_time - time.time()) if reset_time else period
                    
                    raise RateLimitError(
                        f"Rate limit exceeded. Try again in {retry_after} seconds",
                        error_code="rate_limit_exceeded"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator