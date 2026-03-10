"""
Base News Collector
------------------
Abstract base for news collectors. Publishes to `news.raw` RabbitMQ queue.
Payload format compatible with FinBERT pipeline and Sentiment Service.
"""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import aio_pika

logger = logging.getLogger(__name__)

QUEUE_NEWS = "news.raw"


class RawNewsPayload:
    """Standardised news message format for RabbitMQ → Sentiment Service."""

    __slots__ = ("id", "title", "content", "source", "symbol", "timestamp", "url")

    def __init__(
        self,
        title: str,
        content: str,
        source: str,
        symbol: str | None = None,
        timestamp: datetime | None = None,
        url: str | None = None,
        id_: str | None = None,
    ) -> None:
        self.title = title or ""
        self.content = content or ""
        self.source = source or "unknown"
        self.symbol = symbol or "GENERAL"
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.url = url or ""
        self.id = id_ or self._generate_id()

    def _generate_id(self) -> str:
        raw = f"{self.source}:{self.title}:{self.timestamp.isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "url": self.url,
        }


class BaseNewsCollector(ABC):
    """Abstract base for news collectors (NewsAPI, RSS)."""

    def __init__(self, rabbitmq_url: str) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._connection: aio_pika.abc.AbstractConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)
        await self._channel.declare_queue(QUEUE_NEWS, durable=True)
        logger.info("News collector RabbitMQ connection established")

    async def disconnect(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("News collector RabbitMQ connection closed")

    async def _publish(self, payload: RawNewsPayload) -> None:
        if self._channel is None:
            raise RuntimeError("Channel not initialised — call connect() first")

        body = json.dumps(payload.to_dict()).encode()
        message = aio_pika.Message(
            body=body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )
        await self._channel.default_exchange.publish(
            message, routing_key=QUEUE_NEWS
        )
        logger.debug("Published news | %s | %s → %s", payload.source, payload.symbol, QUEUE_NEWS)

    @abstractmethod
    async def collect(self) -> None:
        """Fetch news from external source and publish to RabbitMQ."""
