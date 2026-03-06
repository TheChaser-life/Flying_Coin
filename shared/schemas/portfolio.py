from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PortfolioBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class PortfolioCreate(PortfolioBase):
    user_id: int

class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class PortfolioInDBBase(PortfolioBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PortfolioResponse(PortfolioInDBBase):
    pass
