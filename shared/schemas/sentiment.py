from pydantic import BaseModel, Field, confloat
from typing import Optional
from datetime import datetime

class SentimentBase(BaseModel):
    source: str = Field(..., max_length=255)
    timestamp: datetime
    sentiment_score: confloat(ge=-1.0, le=1.0) # type: ignore
    sentiment_label: Optional[str] = Field(None, max_length=50)
    text_snippet: Optional[str] = Field(None, max_length=1000)

class SentimentCreate(SentimentBase):
    symbol_id: int

class SentimentUpdate(BaseModel):
    pass

class SentimentInDBBase(SentimentBase):
    id: int
    symbol_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SentimentResponse(SentimentInDBBase):
    pass
