"""
Data Cleaner
------------
Validates and sanitises raw OHLCV payloads arriving from RabbitMQ before
they are persisted.  Returns None for records that cannot be salvaged.
"""

import logging
import math
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class DataCleaner:
    # Sanity bounds
    MIN_PRICE = 1e-8
    MAX_PRICE = 1_000_000.0
    MIN_VOLUME = 0.0
    MAX_VOLUME = 1e15

    def clean(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        """
        Validate and clean a raw market data dict.
        Returns the cleaned dict or None if the record is unusable.
        """
        try:
            ticker: str = str(raw["ticker"]).strip().upper()
            asset_class: str = str(raw.get("asset_class", "STOCK")).upper()
            source: str = str(raw.get("source", "UNKNOWN")).upper()

            timestamp = self._parse_timestamp(raw["timestamp"])
            if timestamp is None:
                return None

            open_ = self._clean_price(raw["open"], "open", ticker)
            high_ = self._clean_price(raw["high"], "high", ticker)
            low_ = self._clean_price(raw["low"], "low", ticker)
            close_ = self._clean_price(raw["close"], "close", ticker)
            volume_ = self._clean_volume(raw["volume"], ticker)

            if any(v is None for v in (open_, high_, low_, close_, volume_)):
                return None

            # OHLC consistency
            if not (low_ <= open_ <= high_ and low_ <= close_ <= high_):
                logger.warning(
                    "OHLC consistency failure for %s at %s — adjusting bounds",
                    ticker, timestamp,
                )
                high_ = max(open_, high_, low_, close_)
                low_ = min(open_, high_, low_, close_)

            return {
                "ticker": ticker,
                "asset_class": asset_class,
                "source": source,
                "timestamp": timestamp,
                "open": open_,
                "high": high_,
                "low": low_,
                "close": close_,
                "volume": volume_,
            }

        except (KeyError, TypeError, ValueError):
            logger.warning("Malformed raw payload — dropping: %s", raw, exc_info=True)
            return None

    def _parse_timestamp(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            except ValueError:
                pass
        logger.warning("Cannot parse timestamp: %s", value)
        return None

    def _clean_price(self, value: Any, field: str, ticker: str) -> float | None:
        try:
            v = float(value)
        except (TypeError, ValueError):
            logger.warning("%s | non-numeric %s: %s", ticker, field, value)
            return None

        if math.isnan(v):   # NaN
            logger.warning("%s | NaN %s", ticker, field)
            return None

        if not (self.MIN_PRICE <= v <= self.MAX_PRICE):
            logger.warning(
                "%s | %s=%s out of bounds [%s, %s]",
                ticker, field, v, self.MIN_PRICE, self.MAX_PRICE,
            )
            return None

        return round(v, 8)

    def _clean_volume(self, value: Any, ticker: str) -> float | None:
        try:
            v = float(value)
        except (TypeError, ValueError):
            logger.warning("%s | non-numeric volume: %s", ticker, value)
            return None

        if math.isnan(v):
            return None

        if not (self.MIN_VOLUME <= v <= self.MAX_VOLUME):
            logger.warning("%s | volume=%s out of bounds", ticker, v)
            return None

        return round(v, 2)
