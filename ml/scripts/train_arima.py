#!/usr/bin/env python3
"""
ARIMA Baseline Model — Task 5.8
--------------------------------
Training script (local Python) → log MLflow → so sánh với naive baselines.

Usage:
  python ml/scripts/train_arima.py -d ml/outputs/datasets -s all
  python ml/scripts/train_arima.py -i ml/outputs/datasets/training_dataset_all.parquet
  python ml/scripts/train_arima.py --order 2 1 2  # p d q
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from ml.pipelines.naive_baselines import BaselineMetrics, compute_metrics, evaluate_baselines

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants to avoid duplicated literals (SonarQube S1192)
PARQUET_EXT = ".parquet"


def load_dataset_from_dir(data_dir: str | Path, symbol: str = "all") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load train/val/test từ thư mục dataset builder output."""
    data_dir = Path(data_dir)
    suffix = f"_{symbol}" if symbol != "all" else "_all"

    for ext in [PARQUET_EXT, ".csv"]:
        train_path = data_dir / f"training_dataset{suffix}_train{ext}"
        val_path = data_dir / f"training_dataset{suffix}_val{ext}"
        test_path = data_dir / f"training_dataset{suffix}_test{ext}"
        if train_path.exists() and val_path.exists() and test_path.exists():
            if ext == PARQUET_EXT:
                train = pd.read_parquet(train_path)
                val = pd.read_parquet(val_path)
                test = pd.read_parquet(test_path)
            else:
                train = pd.read_csv(train_path)
                val = pd.read_csv(val_path)
                test = pd.read_csv(test_path)
            return train, val, test

    raise FileNotFoundError(f"Không tìm thấy dataset trong {data_dir} (suffix={suffix})")


def load_and_split(path: str | Path, train_ratio: float = 0.7, val_ratio: float = 0.15) -> tuple:
    """Load file đơn và split theo thời gian."""
    path = Path(path)
    df = pd.read_parquet(path) if path.suffix == PARQUET_EXT else pd.read_csv(path)
    df = df.sort_values("timestamp").reset_index(drop=True)
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    return df.iloc[:train_end], df.iloc[train_end:val_end], df.iloc[val_end:]


def run_arima_and_evaluate(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    close_col: str = "close",
    order: tuple[int, int, int] = (2, 1, 2),
) -> tuple[BaselineMetrics, object]:
    """Fit ARIMA, forecast test, return metrics và fitted model."""
    from statsmodels.tsa.arima.model import ARIMA

    history = np.concatenate([train[close_col].values, val[close_col].values])
    n_test = len(test)

    model = ARIMA(history, order=order)
    try:
        fitted = model.fit()
    except Exception as e:
        logger.warning("ARIMA fit failed (%s), trying simpler order (1,1,1)", e)
        model = ARIMA(history, order=(1, 1, 1))
        fitted = model.fit()
    pred = np.asarray(fitted.forecast(steps=n_test))

    test_close = test[close_col].values
    metrics = compute_metrics(test_close, pred)
    return metrics, fitted


def log_arima_to_mlflow(
    metrics: BaselineMetrics,
    order: tuple[int, int, int],
    symbol: str,
    experiment_name: str = "forecast_models",
    model=None,
) -> None:
    """Log ARIMA run lên MLflow."""
    import mlflow

    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=f"arima_{symbol}"):
        mlflow.log_params({
            "model": "ARIMA",
            "symbol": symbol,
            "order_p": order[0],
            "order_d": order[1],
            "order_q": order[2],
        })
        mlflow.log_metrics({
            "rmse": metrics.rmse,
            "mae": metrics.mae,
            "directional_accuracy": metrics.directional_accuracy,
            "mape": metrics.mape,
        })
        mlflow.set_tag("baseline", "false")
        if model is not None:
            try:
                # Dùng log_artifact (tránh 404 /logged-models của statsmodels.log_model)
                # Load lại: mlflow.artifacts.download_artifacts(run_uri) → pickle.load(open("model/arima_model.pkl","rb"))
                import pickle
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    pkl_path = Path(tmpdir) / "arima_model.pkl"
                    with open(pkl_path, "wb") as f:
                        pickle.dump(model, f)
                    mlflow.log_artifact(str(pkl_path), "model")
            except Exception as e:
                logger.warning("Could not log model artifact: %s", e)
        logger.info("ARIMA: RMSE=%.4f MAE=%.4f DA=%.1f%%", metrics.rmse, metrics.mae, metrics.directional_accuracy)


def compare_with_naive(arima_metrics: BaselineMetrics, naive_metrics: dict) -> None:
    """In so sánh ARIMA vs naive baselines."""
    logger.info("--- So sánh với Naive Baselines ---")
    for name, m in naive_metrics.items():
        rmse_ok = "✓" if arima_metrics.rmse < m.rmse else "✗"
        da_ok = "✓" if arima_metrics.directional_accuracy > m.directional_accuracy else "✗"
        logger.info("  %s: ARIMA RMSE %s (%.4f vs %.4f), DA %s (%.1f%% vs %.1f%%)",
                    name, rmse_ok, arima_metrics.rmse, m.rmse, da_ok,
                    arima_metrics.directional_accuracy, m.directional_accuracy)


def create_sample_dataset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Tạo sample dataset qua Dataset Builder."""
    from ml.pipelines.dataset_builder import DatasetBuilder, DatasetBuilderConfig

    dates = pd.date_range("2023-01-01", periods=300, freq="D")
    rng = np.random.default_rng(42)
    close = 100 + np.cumsum(rng.standard_normal(300) * 2)
    df = pd.DataFrame({
        "timestamp": dates,
        "open": np.roll(close, 1), "high": close + 1, "low": close - 1,
        "close": close, "volume": rng.integers(1_000_000, 10_000_000, 300).astype(float),
    })
    df.loc[0, "open"] = 100

    builder = DatasetBuilder(DatasetBuilderConfig(run_preprocessing=True, output_dir="ml/outputs/datasets_test"))
    result = builder.run(df)
    if not result.preprocessed:
        raise RuntimeError("Preprocessing required")
    return result.preprocessed.train, result.preprocessed.val, result.preprocessed.test


def main() -> int:
    parser = argparse.ArgumentParser(description="ARIMA Baseline Model")
    parser.add_argument("-d", "--data-dir", help="Thư mục dataset (train/val/test)")
    parser.add_argument("-i", "--input", help="File dataset đơn (sẽ split)")
    parser.add_argument("-s", "--symbol", default="all")
    parser.add_argument("--order", nargs=3, type=int, default=[2, 1, 2], metavar=("p", "d", "q"))
    parser.add_argument("--no-mlflow", action="store_true")
    parser.add_argument("--no-model-artifact", action="store_true", help="Không log model artifact")
    parser.add_argument("--experiment", default="forecast_models",
                        help="Experiment name. Dùng tên mới (vd: forecast_models_v2) nếu experiment cũ có artifact_location=s3://")
    parser.add_argument("--no-compare", action="store_true", help="Không so sánh với naive")
    args = parser.parse_args()

    if args.data_dir:
        train, val, test = load_dataset_from_dir(args.data_dir, args.symbol)
    elif args.input:
        train, val, test = load_and_split(args.input)
    else:
        logger.warning("No input — tạo sample dataset")
        train, val, test = create_sample_dataset()

    close_col = "close"
    if "close" not in train.columns:
        if "price" in train.columns:
            logger.info("Cột 'close' không có, dùng 'price' thay thế.")
            close_col = "price"
        else:
            logger.error("Dataset thiếu cột 'close' và 'price'")
            return 1

    order = tuple(args.order)
    if len(order) != 3:
        logger.error("--order cần 3 số (p d q)")
        return 1

    # Fit & evaluate
    arima_metrics, fitted = run_arima_and_evaluate(train, val, test, close_col=close_col, order=order)
    logger.info("ARIMA(%d,%d,%d): RMSE=%.4f MAE=%.4f DA=%.1f%% MAPE=%.2f%%",
                order[0], order[1], order[2], arima_metrics.rmse, arima_metrics.mae,
                arima_metrics.directional_accuracy, arima_metrics.mape)

    # So sánh với naive
    if not args.no_compare:
        naive_metrics = evaluate_baselines(train, val, test, close_col=close_col)
        compare_with_naive(arima_metrics, naive_metrics)

    # Log MLflow
    if not args.no_mlflow:
        try:
            model_to_log = None if args.no_model_artifact else fitted
            log_arima_to_mlflow(arima_metrics, order, args.symbol, args.experiment, model=model_to_log)
        except Exception as e:
            logger.warning("MLflow log failed: %s", e)

    return 0


if __name__ == "__main__":
    sys.exit(main())
