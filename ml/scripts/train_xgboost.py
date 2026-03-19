#!/usr/bin/env python3
"""
XGBoost Model — Task 6.4
------------------------
Training script (local Python + GPU) → log MLflow → so sánh với baselines.
GPU: tree_method='gpu_hist' cho RTX 4060.

Usage:
  python ml/scripts/train_xgboost.py -d ml/outputs/datasets -s all
  python ml/scripts/train_xgboost.py -d ml/outputs/datasets -s AAPL --max-depth 6
"""

from __future__ import annotations

import argparse
import os
import logging
import pickle
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from ml.pipelines.feature_engineering import get_feature_columns
from ml.pipelines.naive_baselines import BaselineMetrics, compute_metrics, evaluate_baselines

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_dataset_from_dir(data_dir: str | Path, symbol: str = "all") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load train/val/test từ thư mục dataset builder output."""
    data_dir = Path(data_dir)
    suffix = f"_{symbol}" if symbol != "all" else "_all"

    for ext in [".parquet", ".csv"]:
        train_path = data_dir / f"training_dataset{suffix}_train{ext}"
        val_path = data_dir / f"training_dataset{suffix}_val{ext}"
        test_path = data_dir / f"training_dataset{suffix}_test{ext}"
        if train_path.exists() and val_path.exists() and test_path.exists():
            if ext == ".parquet":
                train = pd.read_parquet(train_path)
                val = pd.read_parquet(val_path)
                test = pd.read_parquet(test_path)
            else:
                train = pd.read_csv(train_path)
                val = pd.read_csv(val_path)
                test = pd.read_csv(test_path)
            return train, val, test

    raise FileNotFoundError(f"Không tìm thấy dataset trong {data_dir} (suffix={suffix})")


def prepare_xy(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "close",
) -> tuple[np.ndarray, np.ndarray]:
    """
    X: features [t-lookback+1:t].
    y: target at t+1 (next close).
    """
    df = df.copy()
    df["target"] = df[target_col].shift(-1)
    df = df.dropna().reset_index(drop=True)

    cols = [c for c in feature_cols if c in df.columns]
    if not cols:
        cols = [target_col]
    X = df[cols].values.astype(np.float32)
    y = df["target"].values.astype(np.float32)
    return X, y


def run_xgboost_and_evaluate(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "close",
    use_gpu: bool = True,
    max_depth: int = 6,
    n_estimators: int = 100,
    learning_rate: float = 0.1,
) -> tuple[BaselineMetrics, object]:
    """Fit XGBoost, forecast test, return metrics và model."""
    import xgboost as xgb

    X_train, y_train = prepare_xy(train, feature_cols, target_col)
    x_val, y_val = prepare_xy(val, feature_cols, target_col)
    X_test, y_test = prepare_xy(test, feature_cols, target_col)

    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(x_val, label=y_val)
    dtest = xgb.DMatrix(X_test)

    # XGBoost 2.x: tree_method="hist" + device="cuda" (không còn gpu_hist)
    params = {
        "max_depth": max_depth,
        "n_estimators": n_estimators,
        "learning_rate": learning_rate,
        "objective": "reg:squarederror",
        "eval_metric": ["rmse", "mae"],
        "tree_method": "hist",
        "device": "cuda" if use_gpu else "cpu",
    }

    model = xgb.train(
        params,
        dtrain,
        num_boost_round=n_estimators,
        evals=[(dtrain, "train"), (dval, "val")],
        verbose_eval=False,
    )

    pred = model.predict(dtest)
    metrics = compute_metrics(y_test, pred)
    return metrics, model


def log_xgboost_to_mlflow(
    metrics: BaselineMetrics,
    symbol: str,
    feature_cols: list[str],
    params: dict,
    experiment_name: str = "forecast_models",
    model=None,
) -> None:
    """Log XGBoost run lên MLflow."""
    import mlflow

    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=f"xgboost_{symbol}"):
        mlflow.log_params({
            "model": "XGBoost",
            "symbol": symbol,
            "n_features": len(feature_cols),
            **params,
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
                with tempfile.TemporaryDirectory() as tmpdir:
                    model_path = Path(tmpdir) / "xgboost_model.json"
                    model.save_model(str(model_path))
                    meta_path = Path(tmpdir) / "feature_cols.pkl"
                    with open(meta_path, "wb") as f:
                        pickle.dump(feature_cols, f)
                    mlflow.log_artifact(str(model_path), "model")
                    mlflow.log_artifact(str(meta_path), "model")
            except Exception as e:
                logger.warning("Could not log model artifact: %s", e)
        logger.info("XGBoost: RMSE=%.4f MAE=%.4f DA=%.1f%%", metrics.rmse, metrics.mae, metrics.directional_accuracy)
        print(f"MLFLOW_RUN_ID: {mlflow.active_run().info.run_id}")


def compare_with_naive(metrics: BaselineMetrics, naive_metrics: dict) -> None:
    """In so sánh XGBoost vs naive baselines."""
    logger.info("--- So sánh với Naive Baselines ---")
    for name, m in naive_metrics.items():
        rmse_ok = "✓" if metrics.rmse < m.rmse else "✗"
        da_ok = "✓" if metrics.directional_accuracy > m.directional_accuracy else "✗"
        logger.info("  %s: XGBoost RMSE %s (%.4f vs %.4f), DA %s (%.1f%% vs %.1f%%)",
                    name, rmse_ok, metrics.rmse, m.rmse, da_ok,
                    metrics.directional_accuracy, m.directional_accuracy)


def main() -> int:
    # MLflow: mặc định localhost:5000 (tránh port 51471 cũ từ session trước)
    uri = os.environ.get("MLFLOW_TRACKING_URI", "")
    if not uri or "51471" in uri:
        os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5000"

    parser = argparse.ArgumentParser(description="XGBoost Model (GPU)")
    parser.add_argument("-d", "--data-dir", help="Thư mục dataset (train/val/test)")
    parser.add_argument("-i", "--input", help="File dataset đơn (sẽ split)")
    parser.add_argument("-s", "--symbol", default="all")
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--no-gpu", action="store_true", help="Dùng CPU thay vì GPU")
    parser.add_argument("--no-mlflow", action="store_true")
    parser.add_argument("--no-model-artifact", action="store_true")
    parser.add_argument("--experiment", default="forecast_models")
    parser.add_argument("--no-compare", action="store_true")
    args = parser.parse_args()

    if args.data_dir:
        train, val, test = load_dataset_from_dir(args.data_dir, args.symbol)
    elif args.input:
        # Đơn giản hóa: dùng load_and_split từ train_arima hoặc copy lại
        df = pd.read_parquet(args.input) if args.input.endswith(".parquet") else pd.read_csv(args.input)
        df = df.sort_values("timestamp").reset_index(drop=True)
        n = len(df)
        train_end = int(n * 0.7)
        val_end = int(n * 0.85)
        train, val, test = df.iloc[:train_end], df.iloc[train_end:val_end], df.iloc[val_end:]
    else:
        logger.error("Cần -d/--data-dir hoặc -i/--input")
        return 1

    close_col = "close"
    if "close" not in train.columns:
        if "price" in train.columns:
            logger.info("Cột 'close' không có, dùng 'price' thay thế.")
            close_col = "price"
        else:
            logger.error("Dataset thiếu cột 'close' và 'price'")
            return 1

    feature_cols = get_feature_columns(train)
    if not feature_cols:
        feature_cols = [close_col]
    # Thêm close để hỗ trợ autoregressive forecast
    if close_col not in feature_cols:
        feature_cols = [close_col] + feature_cols
    logger.info("Features: %s", feature_cols[:10] if len(feature_cols) > 10 else feature_cols)

    metrics, model = run_xgboost_and_evaluate(
        train, val, test,
        feature_cols=feature_cols,
        target_col=close_col,
        use_gpu=not args.no_gpu,
        max_depth=args.max_depth,
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate,
    )

    logger.info("XGBoost: RMSE=%.4f MAE=%.4f DA=%.1f%% MAPE=%.2f%%",
                metrics.rmse, metrics.mae, metrics.directional_accuracy, metrics.mape)

    if not args.no_compare:
        naive_metrics = evaluate_baselines(train, val, test, close_col=close_col)
        compare_with_naive(metrics, naive_metrics)

    if not args.no_mlflow:
        try:
            model_to_log = None if args.no_model_artifact else model
            log_xgboost_to_mlflow(
                metrics, args.symbol, feature_cols,
                params={"max_depth": args.max_depth, "n_estimators": args.n_estimators, "learning_rate": args.learning_rate},
                experiment_name=args.experiment,
                model=model_to_log,
            )
        except Exception as e:
            logger.warning("MLflow log failed: %s", e)

    return 0


if __name__ == "__main__":
    sys.exit(main())
