"""
Naive Baselines — Task 5.7
--------------------------
Naive forecast (giá ngày mai = giá hôm nay) + MA forecast.
Log lên MLflow làm benchmark so sánh với ARIMA, XGBoost, LSTM.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BaselineMetrics:
    """Metrics đánh giá baseline."""

    rmse: float
    mae: float
    directional_accuracy: float
    mape: float = 0.0


def naive_forecast(close: pd.Series | np.ndarray) -> np.ndarray:
    """
    Naive: giá ngày mai = giá hôm nay.
    pred[t] = close[t-1]
    """
    close = np.asarray(close)
    return np.roll(close, 1)  # pred[0] = close[-1], pred[i] = close[i-1]


def ma_forecast(close: pd.Series | np.ndarray, window: int = 7) -> np.ndarray:
    """
    MA forecast: pred[t] = mean(close[t-window:t]).
    Dùng rolling mean của quá khứ.
    """
    close = pd.Series(close)
    return close.rolling(window=window, min_periods=1).mean().values


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> BaselineMetrics:
    """RMSE, MAE, Directional Accuracy, MAPE."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true = y_true[mask]
    y_pred = y_pred[mask]

    if len(y_true) == 0:
        return BaselineMetrics(rmse=0, mae=0, directional_accuracy=0, mape=0)

    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mae = np.mean(np.abs(y_true - y_pred))

    # Directional: đúng hướng tăng/giảm
    true_dir = np.sign(np.diff(y_true))
    pred_dir = np.sign(np.diff(y_pred))
    # Bỏ 0 (không đổi)
    valid = (true_dir != 0) | (pred_dir != 0)
    if valid.sum() > 0:
        da = np.mean(true_dir[valid] == pred_dir[valid]) * 100
    else:
        da = 50.0  # neutral

    # MAPE (tránh chia 0)
    denom = np.abs(y_true)
    mape = np.mean(np.where(denom > 1e-8, np.abs(y_true - y_pred) / denom, 0)) * 100

    return BaselineMetrics(rmse=float(rmse), mae=float(mae), directional_accuracy=float(da), mape=float(mape))


def evaluate_baselines(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    close_col: str = "close",
    ma_window: int = 7,
) -> dict[str, BaselineMetrics]:
    """
    Đánh giá Naive và MA forecast trên test set.

    Returns:
        {"naive": metrics, "ma_7": metrics}
    """
    train_close = train[close_col].values
    val_close = val[close_col].values
    test_close = test[close_col].values

    # Full history để predict (train + val + test)
    full = np.concatenate([train_close, val_close, test_close])
    n_train = len(train_close)
    n_val = len(val_close)
    n_test = len(test_close)
    test_start = n_train + n_val

    results = {}

    # Naive: pred[i] = full[test_start + i - 1]
    naive_pred = np.array([full[test_start + i - 1] for i in range(n_test)])
    results["naive"] = compute_metrics(test_close, naive_pred)

    # MA: pred[i] = mean(full[test_start+i-window : test_start+i])
    ma_pred = np.zeros(n_test)
    for i in range(n_test):
        start = max(0, test_start + i - ma_window)
        end = test_start + i
        ma_pred[i] = np.mean(full[start:end]) if end > start else full[end - 1]
    results[f"ma_{ma_window}"] = compute_metrics(test_close, ma_pred)

    return results


def log_baselines_to_mlflow(
    metrics: dict[str, BaselineMetrics],
    symbol: str = "unknown",
    experiment_name: str = "baselines",
) -> None:
    """Log từng baseline lên MLflow làm benchmark."""
    import mlflow

    mlflow.set_experiment(experiment_name)

    for model_name, m in metrics.items():
        with mlflow.start_run(run_name=f"{model_name}_{symbol}"):
            mlflow.log_params({"model": model_name, "symbol": symbol})
            mlflow.log_metrics({
                "rmse": m.rmse,
                "mae": m.mae,
                "directional_accuracy": m.directional_accuracy,
                "mape": m.mape,
            })
            mlflow.set_tag("baseline", "true")
        logger.info("%s: RMSE=%.4f MAE=%.4f DA=%.1f%%", model_name, m.rmse, m.mae, m.directional_accuracy)
