# /backend/app/caching/cache_manager.py
"""
Multi-level caching: In-memory → Redis → Database
"""

from functools import wraps
import asyncio
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Cache hierarchy:
    1. In-process memory cache (L1) - fastest, shared per instance
    2. Redis cache (L2) - shared across instances, distributed
    3. Database (L3) - source of truth, slowest
    """
    
    def __init__(self):
        self.l1_cache = {}  # In-memory
        self.redis = None  # Initialized later
    
    async def get(self, key: str, ttl: int = 3600):
        """
        Get from cache with fallback
        """
        
        # L1: Check in-memory
        if key in self.l1_cache:
            logger.debug(f"Cache hit (L1): {key}")
            return self.l1_cache[key]['value']
        
        # L2: Check Redis
        if self.redis:
            cached = await self.redis.get(key)
            if cached:
                logger.debug(f"Cache hit (L2): {key}")
                # Store in L1 for next time
                self.l1_cache[key] = {
                    'value': cached,
                    'ttl': ttl
                }
                return cached
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        level: str = "both"  # 'l1', 'l2', 'both'
    ):
        """
        Set cache at specified level
        """
        
        if level in ['l1', 'both']:
            self.l1_cache[key] = {
                'value': value,
                'ttl': ttl,
                'set_at': datetime.utcnow()
            }
        
        if level in ['l2', 'both'] and self.redis:
            await self.redis.setex(key, ttl, value)
    
    async def invalidate(self, pattern: str):
        """Invalidate cache keys matching pattern"""
        
        # L1: In-memory
        keys_to_delete = [k for k in self.l1_cache.keys() if pattern in k]
        for k in keys_to_delete:
            del self.l1_cache[k]
        
        # L2: Redis
        if self.redis:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                for key in keys:
                    await self.redis.delete(key)
                if cursor == 0:
                    break

# Cache decorator
cache_manager = CacheManager()

def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
            
            # Try cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator

# Usage
@cached(ttl=3600, key_prefix="user")
async def get_user(user_id: str):
    user = await db.get(User, user_id)
    return user
