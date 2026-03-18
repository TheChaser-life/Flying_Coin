import httpx
import pandas as pd
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.schemas.backtest import BacktestRequest, BacktestResult
from app.services.engine import BacktestEngine

router = APIRouter(prefix="/backtest", tags=["backtesting"])

@router.post("/run", response_model=BacktestResult)
async def run_backtest(payload: BacktestRequest):
    """
    Triggers a backtest for a specific ticker and strategy.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.MARKET_DATA_SERVICE_URL}/api/v1/market-data/symbols/{payload.ticker}/history",
            params={"limit": 1000}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Could not fetch data for {payload.ticker}")
        
    data = resp.json()
    if not data:
        raise HTTPException(status_code=400, detail="Empty market data")
        
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()

    if payload.strategy_name == "SMA_CROSSOVER":
        results = BacktestEngine.run_sma_crossover(
            df, 
            short_window=payload.parameters.get("short_window", 20),
            long_window=payload.parameters.get("long_window", 50),
            initial_capital=payload.initial_capital
        )
        return {**results, "ticker": payload.ticker}
    else:
        raise HTTPException(status_code=400, detail="Unsupported strategy")
