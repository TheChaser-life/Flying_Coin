#!/usr/bin/env python3
"""
Script chạy Naive Baselines — Task 5.7
--------------------------------------
Naive + MA forecast → evaluate trên test set → log MLflow.

Usage:
  # Từ dataset đã build (train/val/test parquet)
  python ml/scripts/run_naive_baselines.py -d ml/outputs/datasets -s AAPL

  # Từ file đơn (sẽ split 70/15/15)
  python ml/scripts/run_naive_baselines.py -i ml/outputs/datasets/training_dataset_all.csv

  # Không log MLflow (chỉ in metrics)
  python ml/scripts/run_naive_baselines.py -d ml/outputs/datasets -s AAPL --no-mlflow
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.pipelines.naive_baselines import (
    evaluate_baselines,
    log_baselines_to_mlflow,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_dataset_from_dir(data_dir: str | Path, symbol: str = "all") -> tuple:
    """Load train/val/test từ thư mục dataset builder output."""
    data_dir = Path(data_dir)
    suffix = f"_{symbol}" if symbol != "all" else "_all"

    def _try_load(suf: str):
        for ext in [".parquet", ".csv"]:
            train_path = data_dir / f"training_dataset{suf}_train{ext}"
            val_path = data_dir / f"training_dataset{suf}_val{ext}"
            test_path = data_dir / f"training_dataset{suf}_test{ext}"
            if train_path.exists() and val_path.exists() and test_path.exists():
                import pandas as pd
                if ext == ".parquet":
                    return pd.read_parquet(train_path), pd.read_parquet(val_path), pd.read_parquet(test_path)
                return pd.read_csv(train_path), pd.read_csv(val_path), pd.read_csv(test_path)
        return None

    result = _try_load(suffix)
    if result is not None:
        return result
    # Fallback: dataset từ sample data có suffix _all
    if suffix != "_all":
        result = _try_load("_all")
        if result is not None:
            logger.warning("Không tìm thấy %s — dùng training_dataset_all_* (sample data)", suffix)
            return result
    raise FileNotFoundError(
        f"Không tìm thấy dataset trong {data_dir} (suffix={suffix}). "
        "Chạy run_dataset_builder.py trước, hoặc dùng -s all nếu đã build từ sample."
    )


def load_and_split(path: str | Path, train_ratio: float = 0.7, val_ratio: float = 0.15) -> tuple:
    """Load file đơn và split theo thời gian."""
    import pandas as pd
    path = Path(path)
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    df = df.sort_values("timestamp").reset_index(drop=True)
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    return df.iloc[:train_end], df.iloc[train_end:val_end], df.iloc[val_end:]


def main() -> int:
    parser = argparse.ArgumentParser(description="Naive Baselines")
    parser.add_argument("-d", "--data-dir", help="Thư mục dataset (train/val/test)")
    parser.add_argument("-i", "--input", help="File dataset đơn (sẽ split)")
    parser.add_argument("-s", "--symbol", default="all", help="Symbol suffix (AAPL, BTCUSDT, all)")
    parser.add_argument("--ma-window", type=int, default=7)
    parser.add_argument("--no-mlflow", action="store_true", help="Không log MLflow")
    parser.add_argument("--experiment", default="baselines")
    args = parser.parse_args()

    if args.data_dir:
        train, val, test = load_dataset_from_dir(args.data_dir, args.symbol)
    elif args.input:
        train, val, test = load_and_split(args.input)
    else:
        logger.warning("No input — tạo sample và chạy dataset builder")
        from ml.pipelines.dataset_builder import DatasetBuilder, DatasetBuilderConfig
        import pandas as pd
        import numpy as np
        dates = pd.date_range("2023-01-01", periods=300, freq="D")
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(300) * 2)
        df = pd.DataFrame({
            "timestamp": dates,
            "open": np.roll(close, 1), "high": close + 1, "low": close - 1,
            "close": close, "volume": np.random.randint(1_000_000, 10_000_000, 300).astype(float),
        })
        df.loc[0, "open"] = 100
        builder = DatasetBuilder(DatasetBuilderConfig(run_preprocessing=True, output_dir="ml/outputs/datasets_test"))
        result = builder.run(df)
        if result.preprocessed:
            train, val, test = result.preprocessed.train, result.preprocessed.val, result.preprocessed.test
        else:
            logger.error("Preprocessing required")
            return 1

    if "close" not in train.columns:
        logger.error("Dataset thiếu cột 'close'")
        return 1

    metrics = evaluate_baselines(train, val, test, ma_window=args.ma_window)

    for name, m in metrics.items():
        logger.info("%s: RMSE=%.4f MAE=%.4f DA=%.1f%% MAPE=%.2f%%", name, m.rmse, m.mae, m.directional_accuracy, m.mape)

    if not args.no_mlflow:
        try:
            log_baselines_to_mlflow(metrics, symbol=args.symbol, experiment_name=args.experiment)
        except Exception as e:
            logger.warning("MLflow log failed: %s (set MLFLOW_TRACKING_URI?)", e)

    return 0


if __name__ == "__main__":
    sys.exit(main())
