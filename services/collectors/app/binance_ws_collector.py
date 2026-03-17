"""
Binance WebSocket Collector
---------------------------
Subscribes to Binance's real-time WebSocket stream for live kline/ticker data.
Publishes every price tick directly to the `market.raw.crypto` RabbitMQ queue.

Stream used: wss://stream.binance.com:9443/stream?streams=<symbol>@miniTicker/...
miniTicker pushes updates every second for each symbol.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

import aiohttp
import aio_pika

from app.base_collector import RawMarketPayload, QUEUE_CRYPTO

logger = logging.getLogger(__name__)

BINANCE_WS_URL = "wss://stream.binance.com:9443/stream"


class BinanceWebSocketCollector:
    """
    Streams real-time price ticks from Binance via WebSocket.
    Publishes a RawMarketPayload for each ticker update received.

    Uses miniTicker stream — pushes full ticker stats every second.
    Fields used: c (close/last price), o (open), h (high), l (low), v (volume).
    """

    def __init__(
        self,
        rabbitmq_url: str,
        symbols: list[str],
        reconnect_delay: int = 5,
    ) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._symbols = [s.lower() for s in symbols]
        self._reconnect_delay = reconnect_delay
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._running = False

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.declare_queue(QUEUE_CRYPTO, durable=True)
        logger.info("BinanceWS | RabbitMQ connected")

    async def disconnect(self) -> None:
        self._running = False
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("BinanceWS | RabbitMQ disconnected")

    async def stream(self) -> None:
        """
        Main loop: connects to Binance WebSocket and streams price ticks.
        Automatically reconnects on disconnection.
        """
        self._running = True
        streams = "/".join(f"{s}@miniTicker" for s in self._symbols)
        url = f"{BINANCE_WS_URL}?streams={streams}"

        logger.info("BinanceWS | Connecting to: %s", url)

        while self._running:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(
                        url,
                        heartbeat=20,
                        timeout=aiohttp.ClientTimeout(total=None, connect=10),
                    ) as ws:
                        logger.info("BinanceWS | Connected — streaming %d symbols", len(self._symbols))
                        async for msg in ws:
                            if not self._running:
                                break
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                await self._handle_message(msg.data)
                            elif msg.type in (
                                aiohttp.WSMsgType.CLOSED,
                                aiohttp.WSMsgType.ERROR,
                            ):
                                logger.warning("BinanceWS | Stream closed/error: %s", msg.type)
                                break

            except asyncio.CancelledError:
                logger.info("BinanceWS | Stream cancelled")
                break
            except Exception as e:
                logger.error("BinanceWS | Connection error: %s — reconnecting in %ds", e, self._reconnect_delay)

            if self._running:
                logger.info("BinanceWS | Reconnecting in %ds...", self._reconnect_delay)
                await asyncio.sleep(self._reconnect_delay)

    async def _handle_message(self, raw: str) -> None:
        try:
            outer = json.loads(raw)
            data = outer.get("data", outer)  # combined stream wraps in {"stream":..., "data":...}

            symbol = data.get("s")  # e.g. "BTCUSDT"
            if not symbol:
                return

            close = float(data["c"])
            open_ = float(data["o"])
            high_ = float(data["h"])
            low_ = float(data["l"])
            volume = float(data["v"])

            event_time_ms = int(data.get("E", 0))
            if event_time_ms:
                ts = datetime.fromtimestamp(event_time_ms / 1000, tz=timezone.utc)
            else:
                ts = datetime.now(tz=timezone.utc)

            payload = RawMarketPayload(
                ticker=symbol,
                asset_class="CRYPTO",
                source="BINANCE",
                timestamp=ts,
                open=open_,
                high=high_,
                low=low_,
                close=close,
                volume=volume,
            )

            await self._publish(payload)
            logger.debug("BinanceWS | %s close=%.2f", symbol, close)

        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.warning("BinanceWS | Failed to parse message: %s — %s", e, raw[:200])

    async def _publish(self, payload: RawMarketPayload) -> None:
        if self._channel is None:
            raise RuntimeError("Channel not initialised — call connect() first")

        body = json.dumps(payload.to_dict()).encode()
        message = aio_pika.Message(
            body=body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )
        await self._channel.default_exchange.publish(
            message, routing_key=QUEUE_CRYPTO
        )
