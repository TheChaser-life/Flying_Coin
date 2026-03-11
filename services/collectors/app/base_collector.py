import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import aio_pika

logger = logging.getLogger(__name__)

QUEUE_STOCK = "market.raw.stock"
QUEUE_CRYPTO = "market.raw.crypto"


class RawMarketPayload:
    """Standardised message format sent to RabbitMQ."""

    __slots__ = (
        "ticker", "asset_class", "source",
        "timestamp", "open", "high", "low", "close", "volume",
    )

    def __init__(
        self,
        ticker: str,
        asset_class: str,
        source: str,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ) -> None:
        self.ticker = ticker
        self.asset_class = asset_class
        self.source = source
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "asset_class": self.asset_class,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


class BaseCollector(ABC):
    """Abstract base for all market-data collectors."""

    def __init__(self, rabbitmq_url: str) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._connection: aio_pika.abc.AbstractConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        for queue_name in (QUEUE_STOCK, QUEUE_CRYPTO):
            await self._channel.declare_queue(queue_name, durable=True)

        logger.info("RabbitMQ connection established")

    async def disconnect(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("RabbitMQ connection closed")

    async def _publish(self, queue_name: str, payload: RawMarketPayload) -> None:
        if self._channel is None:
            raise RuntimeError("Channel not initialised — call connect() first")

        body = json.dumps(payload.to_dict()).encode()
        message = aio_pika.Message(
            body=body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )
        await self._channel.default_exchange.publish(
            message, routing_key=queue_name
        )
        logger.debug(
            "Published %s | %s → %s",
            payload.ticker,
            payload.timestamp.date(),
            queue_name,
        )

    @abstractmethod
    async def collect(self) -> None:
        """Fetch data from the external source and publish to RabbitMQ."""
