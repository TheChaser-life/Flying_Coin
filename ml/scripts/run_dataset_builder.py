#!/usr/bin/env python3
"""
Script chạy Dataset Builder — Task 5.5
----------------------------------------
JOIN market_data + technical_indicators + sentiment_scores → training dataset.

Usage:
  # Từ PostgreSQL (ticker)
  python ml/scripts/run_dataset_builder.py --ticker AAPL -o ml/outputs/datasets

  # Từ PostgreSQL (symbol_id)
  python ml/scripts/run_dataset_builder.py --symbol-id 1 -o ml/outputs/datasets

  # Từ CSV
  python ml/scripts/run_dataset_builder.py -i data/ohlcv.csv -o ml/outputs/datasets

  # Không chạy preprocessing (chỉ join + indicators)
  python ml/scripts/run_dataset_builder.py --ticker BTCUSDT --no-preprocess
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from ml.pipelines.dataset_builder import DatasetBuilder, DatasetBuilderConfig, load_market_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_sample_data():
    """Sample OHLCV để test khi không có DB."""
    import numpy as np
    dates = pd.date_range("2023-01-01", periods=500, freq="D")
    rng = np.random.default_rng(42)
    close = 100 + np.cumsum(rng.standard_normal(500) * 2)
    open_ = np.roll(close, 1)
    open_[0] = 100
    high = np.maximum(open_, close) + np.abs(rng.standard_normal(500))
    low = np.minimum(open_, close) - np.abs(rng.standard_normal(500))
    volume = rng.integers(1_000_000, 10_000_000, 500).astype(float)
    return pd.DataFrame({
        "timestamp": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description="Dataset Builder")
    parser.add_argument("--ticker", "-t", help="Ticker symbol (load từ DB)")
    parser.add_argument("--symbol-id", type=int, help="Symbol ID (load từ DB)")
    parser.add_argument("--input", "-i", help="Đường dẫn CSV")
    parser.add_argument("--output-dir", "-o", default="ml/outputs/datasets")
    parser.add_argument("--format", choices=["parquet", "csv"], default="parquet")
    parser.add_argument("--no-preprocess", action="store_true", help="Không chạy preprocessing")
    parser.add_argument("--indicators", choices=["basic", "full"], default="full")
    parser.add_argument("--limit", type=int, default=10000)
    parser.add_argument("--fallback-sample", action="store_true", help="Khi DB trả về 0 rows → dùng sample data")
    args = parser.parse_args()

    # Load market data
    if args.input:
        df = load_market_data(csv_path=args.input)
    elif args.ticker or args.symbol_id:
        df = load_market_data(ticker=args.ticker, symbol_id=args.symbol_id, limit=args.limit)
        if len(df) < 50 and args.fallback_sample:
            logger.warning("DB trả về %d rows cho %s — dùng sample data", len(df), args.ticker or args.symbol_id)
            df = create_sample_data()
    else:
        logger.warning("No input — using sample data")
        df = create_sample_data()

    if len(df) < 50:
        logger.error(
            "Quá ít dữ liệu (%d rows). Cần ít nhất 50 để tính indicators.\n"
            "  • Chạy collectors (Yahoo/Binance) để thu thập data cho ticker\n"
            "  • Hoặc dùng sample: python ml/scripts/run_dataset_builder.py (bỏ --ticker)\n"
            "  • Hoặc thêm --fallback-sample để dùng sample khi DB rỗng",
            len(df),
        )
        return 1

    config = DatasetBuilderConfig(
        indicators=args.indicators,
        run_preprocessing=not args.no_preprocess,
        output_format=args.format,
        output_dir=args.output_dir,
    )

    builder = DatasetBuilder(config)
    result = builder.run(
        market_df=df,
        symbol_id=args.symbol_id,
        ticker=args.ticker,
    )

    logger.info("Done: %s", result.metadata)
    return 0


if __name__ == "__main__":
    sys.exit(main())
