"""
RabbitMQ Consumer
-----------------
Subscribes to `market.raw.stock` and `market.raw.crypto` queues,
cleans each message, persists to PostgreSQL and publishes to Redis.
"""

import asyncio
import json
import logging
from typing import Callable, Awaitable

import aio_pika
import aio_pika.abc
import redis.asyncio as aioredis
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import config
from app.core.database import AsyncSessionLocal
from app.services.data_cleaner import DataCleaner
from app.services.market_service import MarketService
from app.services.redis_publisher import RedisPublisher

logger = logging.getLogger(__name__)

QUEUES = ["market.raw.stock", "market.raw.crypto"]

_cleaner = DataCleaner()
_market_service = MarketService()


class MarketDataConsumer:
    def __init__(self, rabbitmq_url: str, redis: aioredis.Redis) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._redis = redis
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._publisher = RedisPublisher(redis, ttl=config.REDIS_PRICE_TTL)

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True,
    )
    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=config.CONSUMER_PREFETCH_COUNT)
        logger.info("Consumer connected to RabbitMQ")

    async def start_consuming(self) -> None:
        if self._channel is None:
            raise RuntimeError("Consumer not connected")

        tasks: list[asyncio.Task] = []
        for queue_name in QUEUES:
            queue = await self._channel.declare_queue(queue_name, durable=True)
            task = asyncio.create_task(
                queue.consume(self._make_handler()),
                name=f"consumer:{queue_name}",
            )
            tasks.append(task)
            logger.info("Consuming queue: %s", queue_name)

        # Keep tasks alive; cancellation propagates via the caller
        await asyncio.gather(*tasks)

    def _make_handler(self) -> Callable[[aio_pika.abc.AbstractIncomingMessage], Awaitable[None]]:
        async def handle(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            async with message.process(requeue=True):
                await self._process_message(message)
        return handle

    async def _process_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> None:
        try:
            raw = json.loads(message.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in message body — discarding")
            return

        cleaned = _cleaner.clean(raw)
        if cleaned is None:
            logger.warning("Message failed cleaning — discarding: %s", raw)
            return

        async with AsyncSessionLocal() as db:
            try:
                record = await _market_service.upsert_market_data(db, cleaned)
                await db.commit()
            except Exception:
                await db.rollback()
                logger.error(
                    "DB error processing %s @ %s",
                    cleaned.get("ticker"), cleaned.get("timestamp"),
                    exc_info=True,
                )
                raise   # re-raise so aio-pika requeues the message

        if record is not None:
            await self._publisher.publish_price(
                ticker=cleaned["ticker"],
                close=cleaned["close"],
                timestamp=cleaned["timestamp"],
                extra={
                    "open": cleaned["open"],
                    "high": cleaned["high"],
                    "low": cleaned["low"],
                    "volume": cleaned["volume"],
                    "source": cleaned["source"],
                },
            )

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("Consumer connection closed")
