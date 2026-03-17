"""
Redis Publisher
---------------
Caches the latest price and publishes price-update events on the
`price:{symbol}` channel, following the project's Redis key pattern.
"""

import json
import logging
from datetime import datetime
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisPublisher:
    def __init__(self, redis: aioredis.Redis, ttl: int = 60) -> None:
        self._redis = redis
        self._ttl = ttl

    async def publish_price(
        self,
        ticker: str,
        close: float,
        timestamp: datetime,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Cache latest price and broadcast to subscribers."""
        payload: dict[str, Any] = {
            "channel": f"price:{ticker}",
            "ticker": ticker,
            "close": close,
            "timestamp": timestamp.isoformat(),
        }
        if extra:
            payload.update(extra)

        key = f"price:{ticker}"
        json_payload = json.dumps(payload)

        pipe = self._redis.pipeline()
        pipe.set(key, json_payload, ex=self._ttl)
        pipe.publish(key, json_payload)
        await pipe.execute()

        logger.info("Redis | published price:%s close=%s", ticker, close)
