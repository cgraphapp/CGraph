import redis.asyncio as redis
from typing import Optional, Any
import json
import os
from datetime import timedelta

REDIS_URL = os.getenv("REDIS_URL")

class Cache:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        self.redis = await redis.from_url(
            REDIS_URL,
            encoding="utf8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.redis:
            return None
        return await self.redis.get(key)

    async def set(self, key: str, value: Any, ex: int = 3600):
        """Set value in cache"""
        if not self.redis:
            return
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.redis.setex(key, ex, str(value))

    async def delete(self, key: str):
        """Delete from cache"""
        if not self.redis:
            return
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            return False
        return await self.redis.exists(key) == 1

    async def lpush(self, key: str, *values):
        """Push to list"""
        if not self.redis:
            return
        await self.redis.lpush(key, *values)

    async def rpop(self, key: str):
        """Pop from list"""
        if not self.redis:
            return None
        return await self.redis.rpop(key)

cache = Cache()
