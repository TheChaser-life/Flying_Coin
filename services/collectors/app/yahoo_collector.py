"""
Yahoo Finance Collector
-----------------------
Fetches OHLCV data for stocks (VN/US) using yfinance and publishes each
candle as a separate message to the `market.raw.stock` RabbitMQ queue.
"""

import logging
from datetime import datetime, timezone

import yfinance as yf

from app.base_collector import BaseCollector, RawMarketPayload, QUEUE_STOCK

logger = logging.getLogger(__name__)


class YahooCollector(BaseCollector):
    """Collects daily OHLCV bars from Yahoo Finance."""

    def __init__(
        self,
        rabbitmq_url: str,
        symbols: list[str],
        interval: str = "1d",
        period: str = "7d",
    ) -> None:
        super().__init__(rabbitmq_url)
        self._symbols = symbols
        self._interval = interval
        self._period = period

    async def _process_ticker(self, ticker: str) -> int:
        """Process a single ticker symbol. Returns number of candles published."""
        published = 0
        df = yf.download(
            ticker,
            period=self._period,
            interval=self._interval,
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if df.empty:
            logger.warning("No data returned for %s", ticker)
            return 0

        for ts, row in df.iterrows():
            # yfinance 1.x trả Series — dùng .iloc[0] để tránh FutureWarning
            def _scalar(v):
                return float(v.iloc[0]) if hasattr(v, "iloc") else float(v)
            open_ = _scalar(row["Open"])
            high_ = _scalar(row["High"])
            low_ = _scalar(row["Low"])
            close_ = _scalar(row["Close"])
            volume_ = _scalar(row["Volume"])

            if any(v != v for v in (open_, high_, low_, close_, volume_)):
                # NaN check — skip incomplete bars
                continue

            timestamp = ts.to_pydatetime()
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            payload = RawMarketPayload(
                ticker=ticker,
                asset_class="STOCK",
                source="YAHOO",
                timestamp=timestamp,
                open=open_,
                high=high_,
                low=low_,
                close=close_,
                volume=volume_,
            )
            await self._publish(QUEUE_STOCK, payload)
            published += 1

        logger.info("Yahoo | %s → %d candles published", ticker, len(df))
        return published

    async def collect(self) -> None:
        published = 0
        errors = 0

        for ticker in self._symbols:
            try:
                published += await self._process_ticker(ticker)
            except Exception:
                errors += 1
                logger.error("Yahoo | failed to collect %s", ticker, exc_info=True)

        logger.info(
            "Yahoo collect run finished | published=%d errors=%d", published, errors
        )

