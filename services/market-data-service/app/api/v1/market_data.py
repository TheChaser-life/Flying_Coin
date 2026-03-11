"""
Market Data API — v1
---------------------
Provides:
  GET  /symbols                    List all active symbols
  POST /symbols                    Register a new symbol
  GET  /symbols/{ticker}/latest    Latest OHLCV bar
  GET  /symbols/{ticker}/history   Paginated historical OHLCV
  GET  /symbols/{ticker}/stats     Aggregated statistics
"""

import json
import logging
from datetime import datetime
from typing import Annotated, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_redis
from app.schemas.market_data import (
    MarketDataResponse,
    SymbolCreate,
    SymbolResponse,
    SymbolStatsResponse,
)
from app.services.market_service import MarketService

router = APIRouter(prefix="/symbols", tags=["market-data"])
_service = MarketService()
logger = logging.getLogger(__name__)


@router.get("", response_model=list[SymbolResponse])
async def list_symbols(
    db: AsyncSession = Depends(get_db),
):
    """Return all active symbols."""
    symbols = await _service.list_symbols(db)
    return symbols


@router.post("", response_model=SymbolResponse, status_code=status.HTTP_201_CREATED)
async def register_symbol(
    payload: SymbolCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new symbol for data collection."""
    symbol = await _service.register_symbol(
        db,
        ticker=payload.ticker,
        name=payload.name,
        asset_class_str=payload.asset_class,
        exchange=payload.exchange,
    )
    return symbol


@router.get("/{ticker}/latest", response_model=MarketDataResponse)
async def get_latest(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Return the latest OHLCV bar for a symbol.
    Checks Redis cache first; falls back to PostgreSQL.
    """
    ticker = ticker.upper()

    # Cache-first
    cached = await redis.get(f"price:{ticker}")
    if cached:
        try:
            data = json.loads(cached)
            # Enrich with additional fields if stored
            return {
                "id": -1,
                "symbol_id": -1,
                "timestamp": data.get("timestamp"),
                "open": data.get("open", data.get("close")),
                "high": data.get("high", data.get("close")),
                "low": data.get("low", data.get("close")),
                "close": data["close"],
                "volume": data.get("volume", 0.0),
                "source": data.get("source", "CACHE"),
                "created_at": data.get("timestamp"),
            }
        except (KeyError, json.JSONDecodeError):
            logger.warning("Corrupted Redis cache for %s — falling back to DB", ticker)

    record = await _service.get_latest(db, ticker)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No market data found for symbol '{ticker}'",
        )
    return record


@router.get("/{ticker}/history", response_model=list[MarketDataResponse])
async def get_history(
    ticker: str,
    start_date: Annotated[Optional[datetime], Query(description="ISO 8601 start datetime")] = None,
    end_date: Annotated[Optional[datetime], Query(description="ISO 8601 end datetime")] = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
):
    """
    Return paginated historical OHLCV bars for a symbol.

    - **ticker**: symbol ticker, e.g. `AAPL`, `BTCUSDT`
    - **start_date / end_date**: optional ISO 8601 datetime filter
    - **limit**: max records per page (default 500, max 5000)
    - **offset**: pagination offset
    """
    ticker = ticker.upper()

    symbol = await _service.get_symbol(db, ticker)
    if symbol is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol '{ticker}' not found",
        )

    records = await _service.get_history(
        db,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return records


@router.get("/{ticker}/stats", response_model=SymbolStatsResponse)
async def get_stats(
    ticker: str,
    start_date: Annotated[Optional[datetime], Query()] = None,
    end_date: Annotated[Optional[datetime], Query()] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Return aggregated statistics for a symbol over an optional time window.
    Includes min/max/avg close, record count, and period price change %.
    """
    ticker = ticker.upper()
    stats = await _service.get_stats(db, ticker, start_date, end_date)
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for symbol '{ticker}'",
        )
    return stats
