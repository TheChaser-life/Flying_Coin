"""
Binance Collector
-----------------
Fetches OHLCV kline data for crypto symbols from the Binance REST API
and publishes each candle to the `market.raw.crypto` RabbitMQ queue.

Uses only the public endpoint — no API key required for historical klines.
"""

import logging
from datetime import datetime, timezone

import aiohttp

from app.base_collector import BaseCollector, RawMarketPayload, QUEUE_CRYPTO

logger = logging.getLogger(__name__)

KLINES_ENDPOINT = "/api/v3/klines"


class BinanceCollector(BaseCollector):
    """Collects kline bars from Binance public REST API."""

    def __init__(
        self,
        rabbitmq_url: str,
        symbols: list[str],
        base_url: str = "https://api.binance.com",
        interval: str = "1d",
        limit: int = 7,
    ) -> None:
        super().__init__(rabbitmq_url)
        self._symbols = symbols
        self._base_url = base_url.rstrip("/")
        self._interval = interval
        self._limit = limit

    async def collect(self) -> None:
        published = 0
        errors = 0

        async with aiohttp.ClientSession() as session:
            for symbol in self._symbols:
                try:
                    klines = await self._fetch_klines(session, symbol)
                    for kline in klines:
                        payload = self._parse_kline(symbol, kline)
                        if payload is not None:
                            await self._publish(QUEUE_CRYPTO, payload)
                            published += 1

                    logger.info(
                        "Binance | %s → %d candles published", symbol, len(klines)
                    )

                except Exception:
                    errors += 1
                    logger.error(
                        "Binance | failed to collect %s", symbol, exc_info=True
                    )

        logger.info(
            "Binance collect run finished | published=%d errors=%d", published, errors
        )

    async def _fetch_klines(
        self, session: aiohttp.ClientSession, symbol: str
    ) -> list[list]:
        url = f"{self._base_url}{KLINES_ENDPOINT}"
        params = {
            "symbol": symbol,
            "interval": self._interval,
            "limit": self._limit,
        }
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            return await resp.json()

    def _parse_kline(
        self, symbol: str, kline: list
    ) -> RawMarketPayload | None:
        """
        Binance kline format (index → meaning):
          0  Open time (ms)
          1  Open
          2  High
          3  Low
          4  Close
          5  Volume
          6  Close time (ms)
          ... (ignored fields)
        """
        try:
            open_time_ms: int = kline[0]
            timestamp = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc)

            open_ = float(kline[1])
            high_ = float(kline[2])
            low_ = float(kline[3])
            close_ = float(kline[4])
            volume_ = float(kline[5])

            return RawMarketPayload(
                ticker=symbol,
                asset_class="CRYPTO",
                source="BINANCE",
                timestamp=timestamp,
                open=open_,
                high=high_,
                low=low_,
                close=close_,
                volume=volume_,
            )
        except (IndexError, ValueError, TypeError):
            logger.warning("Binance | malformed kline for %s: %s", symbol, kline)
            return None
