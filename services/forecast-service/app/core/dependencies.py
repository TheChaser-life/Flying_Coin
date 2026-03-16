import redis.asyncio as aioredis
from app.core.config import config

_redis_pool: aioredis.Redis | None = None

def get_redis_pool() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool

def get_redis() -> aioredis.Redis:
    return get_redis_pool()
