"""
Market Service
--------------
Business logic layer for persisting and querying market data.
All DB operations use SQLAlchemy async sessions.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from shared.database.models import MarketData, Symbol, AssetClass, DataProvider

logger = logging.getLogger(__name__)


class MarketService:

    # ------------------------------------------------------------------
    # Symbol helpers
    # ------------------------------------------------------------------

    async def get_or_create_symbol(
        self,
        db: AsyncSession,
        ticker: str,
        asset_class_str: str,
        source_str: str,
    ) -> Symbol:
        result = await db.execute(
            select(Symbol).where(Symbol.ticker == ticker)
        )
        symbol = result.scalar_one_or_none()

        if symbol is None:
            try:
                asset_class = AssetClass(asset_class_str)
            except ValueError:
                asset_class = AssetClass.STOCK

            symbol = Symbol(
                ticker=ticker,
                name=ticker,
                asset_class=asset_class,
                exchange=source_str,
                is_active=True,
            )
            db.add(symbol)
            await db.flush()   # get the id without committing
            logger.info("Created new symbol: %s (%s)", ticker, asset_class.value)

        return symbol

    async def get_symbol(self, db: AsyncSession, ticker: str) -> Symbol | None:
        result = await db.execute(
            select(Symbol).where(Symbol.ticker == ticker, Symbol.is_active == True)
        )
        return result.scalar_one_or_none()

    async def list_symbols(self, db: AsyncSession) -> list[Symbol]:
        result = await db.execute(
            select(Symbol).where(Symbol.is_active == True).order_by(Symbol.ticker)
        )
        return list(result.scalars().all())

    async def register_symbol(
        self,
        db: AsyncSession,
        ticker: str,
        name: str,
        asset_class_str: str,
        exchange: str | None = None,
    ) -> Symbol:
        try:
            asset_class = AssetClass(asset_class_str.upper())
        except ValueError:
            asset_class = AssetClass.STOCK

        symbol = Symbol(
            ticker=ticker.upper(),
            name=name,
            asset_class=asset_class,
            exchange=exchange,
            is_active=True,
        )
        db.add(symbol)
        await db.flush()
        return symbol

    # ------------------------------------------------------------------
    # Market data persistence
    # ------------------------------------------------------------------

    async def upsert_market_data(
        self,
        db: AsyncSession,
        cleaned: dict[str, Any],
    ) -> MarketData | None:
        """
        Insert a cleaned market data record.
        Uses ON CONFLICT DO NOTHING to avoid duplicates
        (unique constraint: symbol_id + timestamp + source).
        """
        symbol = await self.get_or_create_symbol(
            db,
            ticker=cleaned["ticker"],
            asset_class_str=cleaned["asset_class"],
            source_str=cleaned["source"],
        )

        try:
            source = DataProvider(cleaned["source"])
        except ValueError:
            logger.warning("Unknown source '%s' — skipping", cleaned["source"])
            return None

        stmt = (
            insert(MarketData)
            .values(
                symbol_id=symbol.id,
                timestamp=cleaned["timestamp"],
                open=cleaned["open"],
                high=cleaned["high"],
                low=cleaned["low"],
                close=cleaned["close"],
                volume=cleaned["volume"],
                source=source,
            )
            .on_conflict_do_nothing(
                index_elements=["symbol_id", "timestamp", "source"]
            )
            .returning(MarketData)
        )
        result = await db.execute(stmt)
        row = result.fetchone()
        return row[0] if row else None

    # ------------------------------------------------------------------
    # Query helpers (used by API layer)
    # ------------------------------------------------------------------

    async def get_latest(
        self, db: AsyncSession, ticker: str
    ) -> MarketData | None:
        symbol = await self.get_symbol(db, ticker)
        if symbol is None:
            return None

        result = await db.execute(
            select(MarketData)
            .where(MarketData.symbol_id == symbol.id)
            .order_by(desc(MarketData.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self,
        db: AsyncSession,
        ticker: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[MarketData]:
        symbol = await self.get_symbol(db, ticker)
        if symbol is None:
            return []

        conditions = [MarketData.symbol_id == symbol.id]
        if start_date:
            conditions.append(MarketData.timestamp >= start_date)
        if end_date:
            conditions.append(MarketData.timestamp <= end_date)

        result = await db.execute(
            select(MarketData)
            .where(and_(*conditions))
            .order_by(MarketData.timestamp)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_stats(
        self,
        db: AsyncSession,
        ticker: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any] | None:
        symbol = await self.get_symbol(db, ticker)
        if symbol is None:
            return None

        conditions = [MarketData.symbol_id == symbol.id]
        if start_date:
            conditions.append(MarketData.timestamp >= start_date)
        if end_date:
            conditions.append(MarketData.timestamp <= end_date)

        result = await db.execute(
            select(
                func.count(MarketData.id).label("count"),
                func.min(MarketData.close).label("min_close"),
                func.max(MarketData.close).label("max_close"),
                func.avg(MarketData.close).label("avg_close"),
                func.min(MarketData.timestamp).label("period_start"),
                func.max(MarketData.timestamp).label("period_end"),
            ).where(and_(*conditions))
        )
        row = result.one_or_none()
        if row is None or row.count == 0:
            return None

        # First and last close for price change
        first_result = await db.execute(
            select(MarketData.close)
            .where(and_(*conditions))
            .order_by(MarketData.timestamp)
            .limit(1)
        )
        last_result = await db.execute(
            select(MarketData.close)
            .where(and_(*conditions))
            .order_by(desc(MarketData.timestamp))
            .limit(1)
        )
        first_close = first_result.scalar() or 0.0
        last_close = last_result.scalar() or 0.0
        price_change_pct = (
            (last_close - first_close) / first_close * 100 if first_close else 0.0
        )

        return {
            "ticker": ticker,
            "period_start": row.period_start,
            "period_end": row.period_end,
            "count": row.count,
            "min_close": float(row.min_close),
            "max_close": float(row.max_close),
            "avg_close": float(row.avg_close),
            "latest_close": last_close,
            "price_change_pct": round(price_change_pct, 4),
        }
