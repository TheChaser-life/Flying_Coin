"""Forecast API schemas."""
from typing import Literal

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    """Request body cho /forecast."""

    ticker: str = Field(..., description="Mã chứng khoán (ví dụ: BTCUSDT)")
    model_type: Literal["arima", "xgboost", "lstm"] = "xgboost"
    run_id: str = Field(..., description="MLflow run_id (ví dụ: 8c05617d32f2492a8be281bd4c56e6d6)")
    horizon: Literal[7, 14, 30] = 7
    features: list[list[float]] | None = Field(
        default=None,
        description="XGBoost: 1 row. LSTM: seq_len rows. ARIMA: bỏ qua (model có sẵn history).",
    )


class ForecastResponse(BaseModel):
    """Response từ /forecast."""

    predictions: list[float]
    horizon: int
    model_type: str
    run_id: str
