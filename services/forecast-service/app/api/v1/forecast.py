"""Forecast API — Task 6.6."""
import logging
import traceback

from fastapi import APIRouter, HTTPException

from app.core.config import config
from app.schemas.forecast import ForecastRequest, ForecastResponse
from app.services.model_loader import ForecastModelLoader

router = APIRouter(prefix="/forecast", tags=["forecast"])
logger = logging.getLogger(__name__)

_loader: ForecastModelLoader | None = None


def get_loader() -> ForecastModelLoader:
    global _loader
    if _loader is None:
        _loader = ForecastModelLoader(config.MLFLOW_TRACKING_URI)
    return _loader


@router.post(
    "/predict",
    responses={
        400: {"description": "Invalid model_type or missing features"},
        404: {"description": "Model artifact not found"},
        500: {"description": "Internal prediction error"},
    },
)
async def predict(req: ForecastRequest) -> ForecastResponse:
    """
    Dự báo 7/14/30 ngày.
    - ARIMA: không cần features (model có sẵn history).
    - XGBoost: features = 1 row [f1, f2, ...].
    - LSTM: features = seq_len rows.
    """
    loader = get_loader()
    try:
        if req.model_type == "arima":
            preds = loader.predict_arima(req.run_id, req.horizon)
        elif req.model_type == "xgboost":
            if not req.features:
                raise HTTPException(400, "XGBoost cần features (1 row)")
            preds = loader.predict_xgboost(req.run_id, req.features, req.horizon)
        elif req.model_type == "lstm":
            if not req.features:
                raise HTTPException(400, "LSTM cần features (seq_len rows)")
            preds = loader.predict_lstm(req.run_id, req.features, req.horizon)
        else:
            raise HTTPException(400, f"model_type không hỗ trợ: {req.model_type}")

        return ForecastResponse(
            predictions=preds,
            horizon=req.horizon,
            model_type=req.model_type,
            run_id=req.run_id,
        )
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Predict failed: %s\n%s", e, tb)
        raise HTTPException(500, detail=str(e))
