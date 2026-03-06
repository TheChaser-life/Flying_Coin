from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from shared.database.models import AssetClass

class SymbolBase(BaseModel):
    ticker: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    asset_class: AssetClass
    exchange: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

class SymbolCreate(SymbolBase):
    pass

class SymbolUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    asset_class: Optional[AssetClass] = None
    exchange: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class SymbolInDBBase(SymbolBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SymbolResponse(SymbolInDBBase):
    pass
