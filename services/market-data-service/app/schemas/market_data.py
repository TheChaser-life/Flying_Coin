from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


# ---------------------------------------------------------------------------
# Symbol schemas
# ---------------------------------------------------------------------------

class SymbolCreate(BaseModel):
    ticker: str
    name: str
    asset_class: str   # STOCK | CRYPTO | FOREX | COMMODITY
    exchange: Optional[str] = None


class SymbolResponse(SymbolCreate):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Market data schemas
# ---------------------------------------------------------------------------

class MarketDataCreate(BaseModel):
    symbol_id: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str   # YAHOO | BINANCE | ...

    @field_validator("open", "high", "low", "close", "volume")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("OHLCV values must be non-negative")
        return v


class MarketDataResponse(BaseModel):
    id: int
    symbol_id: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# History query params schema (for API layer)
# ---------------------------------------------------------------------------

class HistoryQueryParams(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 500
    offset: int = 0


# ---------------------------------------------------------------------------
# Statistics schema
# ---------------------------------------------------------------------------

class SymbolStatsResponse(BaseModel):
    ticker: str
    period_start: datetime
    period_end: datetime
    count: int
    min_close: float
    max_close: float
    avg_close: float
    latest_close: float
    price_change_pct: float    # (latest - first) / first * 100
