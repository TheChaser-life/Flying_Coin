import httpx
import pandas as pd
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from app.core.config import settings
from app.core.dependencies import DatabaseDep
from app.models.portfolio import Portfolio, Position
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioResponse, 
    OptimizationRequest, OptimizationResponse
)
from app.services.optimizer import PortfolioOptimizer

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

@router.post("", response_model=PortfolioResponse)
async def create_portfolio(payload: PortfolioCreate, db: DatabaseDep):
    db_portfolio = Portfolio(
        user_id=payload.user_id,
        name=payload.name,
        description=payload.description
    )
    db.add(db_portfolio)
    await db.commit()
    await db.refresh(db_portfolio)
    return db_portfolio

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: int, db: DatabaseDep):
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_portfolio(payload: OptimizationRequest):
    """
    Fetches historical data from Market Data Service and returns optimal weights.
    """
    print(f"DEBUG: optimize_portfolio request with tickers: {payload.tickers}, risk: {payload.risk_tolerance}")
    all_prices = {}
    
    async with httpx.AsyncClient() as client:
        for ticker in payload.tickers:
            # Try original ticker
            resp = await client.get(
                f"{settings.MARKET_DATA_SERVICE_URL}/api/v1/market-data/symbols/{ticker}/history",
                params={"limit": 100}
            )
            
            # If not found, try adding USDT (common for crypto in this system)
            if resp.status_code != 200 and not ticker.endswith("USDT"):
                alt_ticker = f"{ticker}USDT"
                resp = await client.get(
                    f"{settings.MARKET_DATA_SERVICE_URL}/api/v1/market-data/symbols/{alt_ticker}/history",
                    params={"limit": 100}
                )
                if resp.status_code == 200:
                    ticker = alt_ticker # Use the successful one
            
            if resp.status_code != 200:
                continue
            
            data = resp.json()
            if not data:
                continue
                
            prices = {item["timestamp"]: item["close"] for item in data}
            all_prices[ticker] = prices
            
    if not all_prices:
        raise HTTPException(
            status_code=400, 
            detail=f"Could not fetch market data for any of the provided tickers: {payload.tickers}. Please check if they are supported."
        )
        
    df = pd.DataFrame(all_prices).sort_index()
    df = df.ffill().dropna()
    
    if df.empty:
        raise HTTPException(status_code=400, detail="Data range issues")
        
    result = PortfolioOptimizer.optimize_markowitz(df, risk_tolerance=payload.risk_tolerance)
    return result
