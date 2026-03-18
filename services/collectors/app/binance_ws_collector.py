"""
Binance WebSocket Collector
---------------------------
Subscribes to Binance's real-time WebSocket stream for live ticker data.
Publishes DIRECTLY to Redis pub/sub channels — bypasses RabbitMQ and PostgreSQL.

This is intentional: tick data (every second) is for real-time display only.
Historical candle data (1D) from the REST collector goes to PostgreSQL for ML training.

Stream: wss://stream.binance.com:9443/stream?streams=<symbol>@miniTicker/...
miniTicker pushes updates every second for each subscribed symbol.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

import aiohttp
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

BINANCE_WS_URL = "wss://stream.binance.com:9443/stream"
REDIS_PRICE_TTL = 60  # seconds — latest price cached in Redis


class BinanceWebSocketCollector:
    """
    Streams real-time price ticks from Binance via WebSocket.
    Publishes each tick directly to Redis pub/sub on channel `price:{SYMBOL}`.

    Does NOT write to PostgreSQL — tick data is ephemeral and for real-time
    dashboard use only. ML training uses daily candles from the REST collector.
    """

    def __init__(
        self,
        redis_url: str,
        symbols: list[str],
        reconnect_delay: int = 5,
    ) -> None:
        self._redis_url = redis_url
        self._symbols = [s.lower() for s in symbols]
        self._symbols_upper = [s.upper() for s in symbols]
        self._reconnect_delay = reconnect_delay
        self._redis: aioredis.Redis | None = None
        self._running = False

    async def connect(self) -> None:
        self._redis = aioredis.from_url(
            self._redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        # Verify connection
        await self._redis.ping()
        logger.info("BinanceWS | Redis connected at %s", self._redis_url)

    async def disconnect(self) -> None:
        self._running = False
        if self._redis:
            await self._redis.aclose()
            self._redis = None
        logger.info("BinanceWS | Redis disconnected")

    async def stream(self) -> None:
        """
        Main loop: connects to Binance WebSocket and streams price ticks.
        Publishes each tick to Redis. Automatically reconnects on disconnection.
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
                        logger.info(
                            "BinanceWS | Connected — streaming %d symbols: %s",
                            len(self._symbols_upper),
                            self._symbols_upper,
                        )
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
                logger.error(
                    "BinanceWS | Connection error: %s — reconnecting in %ds",
                    e, self._reconnect_delay,
                )

            if self._running:
                await asyncio.sleep(self._reconnect_delay)

    async def _handle_message(self, raw: str) -> None:
        if self._redis is None:
            return
        try:
            outer = json.loads(raw)
            # Combined stream format: {"stream": "btcusdt@miniTicker", "data": {...}}
            data = outer.get("data", outer)

            symbol = data.get("s")  # e.g. "BTCUSDT"
            if not symbol:
                return

            close = float(data["c"])
            open_ = float(data["o"])
            high_ = float(data["h"])
            low_ = float(data["l"])
            volume = float(data["v"])

            event_time_ms = int(data.get("E", 0))
            ts = (
                datetime.fromtimestamp(event_time_ms / 1000, tz=timezone.utc)
                if event_time_ms
                else datetime.now(tz=timezone.utc)
            )

            channel = f"price:{symbol}"
            payload = json.dumps({
                "channel": channel,
                "ticker": symbol,
                "close": close,
                "open": open_,
                "high": high_,
                "low": low_,
                "volume": volume,
                "source": "BINANCE_WS",
                "timestamp": ts.isoformat(),
            })

            # Publish to Redis pub/sub AND cache latest price with TTL
            pipe = self._redis.pipeline()
            pipe.set(channel, payload, ex=REDIS_PRICE_TTL)
            pipe.publish(channel, payload)
            await pipe.execute()

            logger.debug("BinanceWS | published %s close=%.2f", symbol, close)

        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.warning("BinanceWS | Failed to parse message: %s — %s", e, raw[:200])
