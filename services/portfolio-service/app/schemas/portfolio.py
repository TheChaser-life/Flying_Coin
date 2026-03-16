from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class PositionBase(BaseModel):
    ticker: str
    quantity: float
    average_price: float

class PositionCreate(PositionBase):
    pass

class PositionResponse(PositionBase):
    id: int
    portfolio_id: int
    
    model_config = ConfigDict(from_attributes=True)

class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    user_id: str

class PortfolioResponse(PortfolioBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    positions: List[PositionResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class OptimizationRequest(BaseModel):
    tickers: List[str]
    risk_tolerance: float = 0.5  # 0 to 1

class OptimizationResponse(BaseModel):
    weights: dict
    expected_return: float
    volatility: float
    sharpe_ratio: float
