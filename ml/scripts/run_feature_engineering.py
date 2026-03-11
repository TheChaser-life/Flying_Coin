#!/usr/bin/env python3
"""
Script chạy Feature Engineering pipeline — Task 5.6
----------------------------------------------------
Technical Indicators → lưu vào dataset file.

Usage:
  python ml/scripts/run_feature_engineering.py -i data/ohlcv.csv -o ml/outputs/features/dataset.parquet
  python ml/scripts/run_feature_engineering.py --ticker AAPL -o ml/outputs/features/
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import yaml

from ml.pipelines.dataset_builder import load_market_data
from ml.pipelines.feature_engineering import (
    FeatureEngineeringConfig,
    FeatureEngineeringPipeline,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_sample_data() -> pd.DataFrame:
    """Sample OHLCV để test."""
    import numpy as np
    dates = pd.date_range("2023-01-01", periods=300, freq="D")
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(300) * 2)
    open_ = np.roll(close, 1)
    open_[0] = 100
    high = np.maximum(open_, close) + np.abs(np.random.randn(300))
    low = np.minimum(open_, close) - np.abs(np.random.randn(300))
    volume = np.random.randint(1_000_000, 10_000_000, 300).astype(float)
    return pd.DataFrame({
        "timestamp": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def load_config(path: str | Path) -> FeatureEngineeringConfig:
    """Load config từ YAML."""
    with open(path) as f:
        cfg = yaml.safe_load(f)
    return FeatureEngineeringConfig(
        sma_windows=cfg.get("sma_windows", [7, 14, 21, 50, 200]),
        ema_spans=cfg.get("ema_spans", [7, 14, 21, 50, 200]),
        rsi_period=cfg.get("rsi_period", 14),
        macd_fast=cfg.get("macd_fast", 12),
        macd_slow=cfg.get("macd_slow", 26),
        macd_signal=cfg.get("macd_signal", 9),
        bb_period=cfg.get("bb_period", 20),
        bb_std=cfg.get("bb_std", 2.0),
        stoch_period=cfg.get("stoch_period", 14),
        atr_period=cfg.get("atr_period", 14),
        adx_period=cfg.get("adx_period", 14),
        include_sma=cfg.get("include_sma", True),
        include_ema=cfg.get("include_ema", True),
        include_rsi=cfg.get("include_rsi", True),
        include_macd=cfg.get("include_macd", True),
        include_bollinger=cfg.get("include_bollinger", True),
        include_stochastic=cfg.get("include_stochastic", True),
        include_atr=cfg.get("include_atr", True),
        include_obv=cfg.get("include_obv", True),
        include_vwap=cfg.get("include_vwap", True),
        include_adx=cfg.get("include_adx", True),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Feature Engineering Pipeline")
    parser.add_argument("--input", "-i", help="CSV path")
    parser.add_argument("--ticker", "-t", help="Ticker (load từ DB)")
    parser.add_argument("--symbol-id", type=int, help="Symbol ID (load từ DB)")
    parser.add_argument("--output", "-o", default="ml/outputs/features/dataset.parquet")
    parser.add_argument("--format", choices=["parquet", "csv"], default="parquet")
    parser.add_argument("--config", "-c", help="YAML config path")
    parser.add_argument("--limit", type=int, default=10000)
    args = parser.parse_args()

    if args.input:
        df = pd.read_csv(args.input)
    elif args.ticker or args.symbol_id:
        df = load_market_data(ticker=args.ticker, symbol_id=args.symbol_id, limit=args.limit)
    else:
        logger.warning("No input — using sample data")
        df = create_sample_data()

    if len(df) < 50:
        logger.error("Quá ít dữ liệu: %d rows", len(df))
        return 1

    if args.config and Path(args.config).exists():
        config = load_config(args.config)
    else:
        config = FeatureEngineeringConfig()

    pipeline = FeatureEngineeringPipeline(config)
    result = pipeline.run(df, output_path=args.output, output_format=args.format)

    logger.info("Done: %d rows, %d features", result.metadata["n_rows"], result.metadata["n_features"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
