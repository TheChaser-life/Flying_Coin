from pydantic import BaseModel, confloat
from typing import Optional
from datetime import datetime
from shared.database.models import ModelName

class PredictionBase(BaseModel):
    model_name: ModelName
    target_date: datetime
    predicted_value: float
    confidence_score: Optional[confloat(ge=0.0, le=1.0)] = None # type: ignore

class PredictionCreate(PredictionBase):
    symbol_id: int

class PredictionUpdate(BaseModel):
    actual_value: Optional[float] = None

class PredictionInDBBase(PredictionBase):
    id: int
    symbol_id: int
    actual_value: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PredictionResponse(PredictionInDBBase):
    pass
