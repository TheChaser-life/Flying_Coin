"""
News Consumer — Task 8.6
------------------------
Consume from news.raw queue → FinBERT inference → publish sentiment to Redis.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Awaitable

import aio_pika
import aio_pika.abc
import redis
import redis.asyncio as aioredis

from aiormq.exceptions import ChannelInvalidStateError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import config
from app.services.finbert_service import predict_sentiment

logger = logging.getLogger(__name__)

QUEUE_NEWS = "news.raw"


class NewsConsumer:
    def __init__(self, rabbitmq_url: str, redis: aioredis.Redis) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._redis = redis
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._ttl = config.REDIS_SENTIMENT_TTL

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True,
    )
    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=config.CONSUMER_PREFETCH_COUNT)
        logger.info("News consumer connected to RabbitMQ")

    async def start_consuming(self) -> None:
        if self._channel is None:
            raise RuntimeError("Consumer not connected")

        queue = await self._channel.declare_queue(QUEUE_NEWS, durable=True)
        await queue.consume(self._make_handler())
        logger.info("Consuming queue: %s", QUEUE_NEWS)
        await asyncio.Future()  # Run forever

    def _make_handler(self) -> Callable[[aio_pika.abc.AbstractIncomingMessage], Awaitable[None]]:
        async def handle(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            try:
                async with message.process(requeue=True):
                    await self._process_message(message)
            except ChannelInvalidStateError as e:
                logger.warning("Channel closed (shutdown?) — skip: %s", e)
        return handle

    async def _process_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> None:
        try:
            raw = json.loads(message.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in news message — discarding")
            return

        title = raw.get("title") or ""
        content = raw.get("content") or ""
        source = raw.get("source") or "unknown"
        symbol = raw.get("symbol") or "GENERAL"
        timestamp_str = raw.get("timestamp", "")
        url = raw.get("url") or ""

        text = f"{title}. {content}".strip()
        if not text:
            logger.warning("Empty news text — skipping")
            return

        # FinBERT inference (CPU, sync — run in executor to not block)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, predict_sentiment, text
        )

        sentiment_score = result["sentiment_score"]
        sentiment_label = result["sentiment_label"]

        payload = {
            "symbol": symbol,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "source": source,
            "timestamp": timestamp_str,
            "url": url,
            "title": title[:200],
        }

        key = f"sentiment:{symbol}"
        json_payload = json.dumps(payload)

        try:
            pipe = self._redis.pipeline()
            pipe.set(key, json_payload, ex=self._ttl)
            pipe.publish(key, json_payload)
            await pipe.execute()
        except (redis.RedisError, OSError, ConnectionError) as e:
            logger.error("Redis publish failed — message sẽ được requeue: %s", e)
            raise

        logger.info(
            "Sentiment | %s → score=%.3f label=%s",
            symbol, sentiment_score, sentiment_label,
        )

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("News consumer connection closed")
