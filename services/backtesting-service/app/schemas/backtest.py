from typing import List, Dict, Optional
from pydantic import BaseModel

class BacktestRequest(BaseModel):
    ticker: str
    strategy_name: str = "SMA_CROSSOVER"
    parameters: Dict = {"short_window": 20, "long_window": 50}
    initial_capital: float = 10000.0

class EquityPoint(BaseModel):
    timestamp: str
    value: float

class BacktestResult(BaseModel):
    ticker: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    equity_curve: List[EquityPoint]
