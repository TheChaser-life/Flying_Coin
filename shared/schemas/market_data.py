from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from shared.database.models import DataProvider

class MarketDataBase(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: DataProvider

class MarketDataCreate(MarketDataBase):
    symbol_id: int

class MarketDataUpdate(BaseModel):
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None

class MarketDataInDBBase(MarketDataBase):
    id: int
    symbol_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MarketDataResponse(MarketDataInDBBase):
    pass
