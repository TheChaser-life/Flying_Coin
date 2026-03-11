#!/usr/bin/env python3
"""
Script chạy Data Preprocessing pipeline — Task 5.4
--------------------------------------------------
Có thể load từ CSV hoặc PostgreSQL.

Usage:
  # Từ CSV (sample data)
  python ml/scripts/run_preprocessing.py --input data/sample_ohlcv.csv --output-dir ml/outputs/preprocessed

  # Từ PostgreSQL (cần DATABASE_URL)
  python ml/scripts/run_preprocessing.py --ticker AAPL --symbol-id 1 --output-dir ml/outputs/preprocessed

  # Chỉ EDA, không split
  python ml/scripts/run_preprocessing.py --input data/sample.csv --eda-only
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import yaml

from ml.pipelines.preprocessing import DataPreprocessor, PreprocessingConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_from_csv(path: str) -> pd.DataFrame:
    """Load OHLCV từ CSV."""
    df = pd.read_csv(path)
    required = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV thiếu cột: {missing}")
    return df


def load_from_db(ticker: str | None = None, symbol_id: int | None = None, limit: int = 10000) -> pd.DataFrame:
    """Load OHLCV từ PostgreSQL qua SQLAlchemy sync."""
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        raise ImportError("Cần sqlalchemy và psycopg2: pip install sqlalchemy psycopg2-binary")

    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/market_db",
    )
    # asyncpg -> psycopg2 cho sync
    url = url.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(url)
    if symbol_id is not None:
        query = text("""
            SELECT md.timestamp, md.open, md.high, md.low, md.close, md.volume
            FROM market_data md
            WHERE md.symbol_id = :symbol_id
            ORDER BY md.timestamp
            LIMIT :limit
        """)
        df = pd.read_sql(query, engine, params={"symbol_id": symbol_id, "limit": limit})
    elif ticker:
        query = text("""
            SELECT md.timestamp, md.open, md.high, md.low, md.close, md.volume
            FROM market_data md
            JOIN symbols s ON s.id = md.symbol_id
            WHERE s.ticker = :ticker
            ORDER BY md.timestamp
            LIMIT :limit
        """)
        df = pd.read_sql(query, engine, params={"ticker": ticker.upper(), "limit": limit})
    else:
        raise ValueError("Cần --ticker hoặc --symbol-id")

    return df


def create_sample_data() -> pd.DataFrame:
    """Tạo sample OHLCV để test khi không có data."""
    import numpy as np
    dates = pd.date_range("2023-01-01", periods=500, freq="D")
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(500) * 2)
    open_ = np.roll(close, 1)
    open_[0] = 100
    high = np.maximum(open_, close) + np.abs(np.random.randn(500))
    low = np.minimum(open_, close) - np.abs(np.random.randn(500))
    volume = np.random.randint(1_000_000, 10_000_000, 500).astype(float)
    return pd.DataFrame({
        "timestamp": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description="Data Preprocessing Pipeline")
    parser.add_argument("--input", "-i", help="Đường dẫn CSV")
    parser.add_argument("--ticker", "-t", help="Ticker symbol (load từ DB)")
    parser.add_argument("--symbol-id", type=int, help="Symbol ID (load từ DB)")
    parser.add_argument("--output-dir", "-o", default="ml/outputs/preprocessed", help="Thư mục output")
    parser.add_argument("--config", "-c", help="Đường dẫn YAML config")
    parser.add_argument("--eda-only", action="store_true", help="Chỉ chạy EDA, không split")
    parser.add_argument("--sample", action="store_true", help="Dùng sample data (500 rows)")
    parser.add_argument("--limit", type=int, default=10000, help="Số dòng tối đa khi load từ DB")
    args = parser.parse_args()

    # Load data
    if args.sample:
        df = create_sample_data()
        logger.info("Using sample data: %d rows", len(df))
    elif args.input:
        df = load_from_csv(args.input)
        logger.info("Loaded from CSV: %d rows", len(df))
    elif args.ticker or args.symbol_id:
        df = load_from_db(ticker=args.ticker, symbol_id=args.symbol_id, limit=args.limit)
        logger.info("Loaded from DB: %d rows", len(df))
    else:
        logger.warning("No input — using sample data")
        df = create_sample_data()

    if len(df) < 10:
        logger.error("Quá ít dữ liệu (%d rows). Cần ít nhất 10 rows.", len(df))
        return 1

    # Config
    config = PreprocessingConfig()
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            cfg = yaml.safe_load(f)
        config = PreprocessingConfig(
            missing_strategy=cfg.get("missing", {}).get("strategy", "ffill"),
            missing_threshold=cfg.get("missing", {}).get("threshold", 0.3),
            outlier_method=cfg.get("outlier", {}).get("method", "iqr"),
            iqr_multiplier=cfg.get("outlier", {}).get("iqr_multiplier", 1.5),
            zscore_threshold=cfg.get("outlier", {}).get("zscore_threshold", 3.0),
            scaler=cfg.get("scaling", {}).get("scaler", "minmax"),
            scaler_fit_on=cfg.get("scaling", {}).get("fit_on", "train"),
            train_ratio=cfg.get("split", {}).get("train_ratio", 0.7),
            val_ratio=cfg.get("split", {}).get("val_ratio", 0.15),
            test_ratio=cfg.get("split", {}).get("test_ratio", 0.15),
            save_eda_report=cfg.get("eda", {}).get("save_report", True),
            eda_output_dir=cfg.get("eda", {}).get("output_dir"),
        )

    config.eda_output_dir = args.output_dir

    # Run pipeline
    preprocessor = DataPreprocessor(config)

    if args.eda_only:
        preprocessor._run_eda(df)
        if config.save_eda_report and config.eda_output_dir:
            preprocessor._save_eda_artifacts(df)
        logger.info("EDA report saved to %s", config.eda_output_dir)
        return 0

    result = preprocessor.run(df)

    # Save outputs
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result.train.to_csv(out_dir / "train.csv", index=False)
    result.val.to_csv(out_dir / "val.csv", index=False)
    result.test.to_csv(out_dir / "test.csv", index=False)

    logger.info(
        "Preprocessing done: train=%d, val=%d, test=%d → %s",
        len(result.train), len(result.val), len(result.test),
        out_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
