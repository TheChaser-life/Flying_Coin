"""
Dataset Builder — Task 5.5
--------------------------
JOIN market_data + technical_indicators + sentiment_scores → 1 training dataset.
Xuất ra file (parquet/csv) hoặc bảng training_datasets.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pandas as pd

from ml.pipelines.feature_engineering import FeatureEngineeringConfig, add_technical_indicators
from ml.pipelines.preprocessing import DataPreprocessor, PreprocessingConfig, PreprocessingResult

logger = logging.getLogger(__name__)


@dataclass
class DatasetBuilderConfig:
    """Cấu hình Dataset Builder."""

    # Technical indicators
    indicators: Literal["basic", "full"] = "full"
    feature_engineering_config: FeatureEngineeringConfig | None = None

    # Preprocessing
    run_preprocessing: bool = True
    preprocessing_config: PreprocessingConfig | None = None

    # Output
    output_format: Literal["parquet", "csv"] = "parquet"
    output_dir: str | Path = "ml/outputs/datasets"
    save_to_db: bool = False


@dataclass
class DatasetBuilderResult:
    """Kết quả Dataset Builder."""

    raw_df: pd.DataFrame
    preprocessed: PreprocessingResult | None = None
    output_path: Path | None = None
    metadata: dict = field(default_factory=dict)


def load_market_data(
    ticker: str | None = None,
    symbol_id: int | None = None,
    csv_path: str | Path | None = None,
    limit: int = 10000,
) -> pd.DataFrame:
    """Load market data từ PostgreSQL hoặc CSV."""
    if csv_path:
        df = pd.read_csv(csv_path)
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"CSV thiếu cột: {missing}")
        return df

    import os
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        raise ImportError("pip install sqlalchemy psycopg2-binary")

    url = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/db")
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(url)

    try:
        if symbol_id is not None:
            q = text("""
                SELECT md.timestamp, md.open, md.high, md.low, md.close, md.volume, md.symbol_id
                FROM market_data md
                WHERE md.symbol_id = :symbol_id
                ORDER BY md.timestamp
                LIMIT :limit
            """)
            df = pd.read_sql(q, engine, params={"symbol_id": symbol_id, "limit": limit})
        elif ticker:
            q = text("""
                SELECT md.timestamp, md.open, md.high, md.low, md.close, md.volume, md.symbol_id
                FROM market_data md
                JOIN symbols s ON s.id = md.symbol_id
                WHERE s.ticker = :ticker
                ORDER BY md.timestamp
                LIMIT :limit
            """)
            df = pd.read_sql(q, engine, params={"ticker": ticker.upper(), "limit": limit})
        else:
            raise ValueError("Cần ticker, symbol_id hoặc csv_path")
    except Exception as e:
        if "Connection refused" in str(e) or "could not connect" in str(e).lower():
            raise ConnectionError(
                "Không kết nối được PostgreSQL. Cần:\n"
                "  1. Minikube đang chạy: minikube status\n"
                "  2. Port-forward: kubectl port-forward svc/postgres-postgresql 5432:5432 -n default\n"
                "  3. Hoặc dùng sample data: python ml/scripts/run_dataset_builder.py (không --ticker)\n"
                f"Lỗi gốc: {e}"
            ) from e
        raise

    return df


def load_sentiment(
    ticker: str | None = None,
    symbol_id: int | None = None,
    limit: int = 50000,
) -> pd.DataFrame:
    """Load sentiment scores từ PostgreSQL, aggregate theo ngày."""
    import os
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        return pd.DataFrame()

    url = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/db")
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(url)

    if symbol_id is not None:
        q = text("""
            SELECT timestamp, sentiment_score, symbol_id
            FROM sentiments
            WHERE symbol_id = :symbol_id
            ORDER BY timestamp
            LIMIT :limit
        """)
        df = pd.read_sql(q, engine, params={"symbol_id": symbol_id, "limit": limit})
    elif ticker:
        q = text("""
            SELECT s.timestamp, s.sentiment_score, s.symbol_id
            FROM sentiments s
            JOIN symbols sym ON sym.id = s.symbol_id
            WHERE sym.ticker = :ticker
            ORDER BY s.timestamp
            LIMIT :limit
        """)
        df = pd.read_sql(q, engine, params={"ticker": ticker.upper(), "limit": limit})
    else:
        return pd.DataFrame()

    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    agg = df.groupby("date").agg({"sentiment_score": "mean"}).reset_index()
    agg.columns = ["date", "sentiment_score"]
    return agg


def join_sentiment(market_df: pd.DataFrame, sentiment_df: pd.DataFrame) -> pd.DataFrame:
    """Join sentiment vào market data theo ngày."""
    if sentiment_df.empty:
        market_df["sentiment_score"] = 0.0
        return market_df

    market_df = market_df.copy()
    market_df["timestamp"] = pd.to_datetime(market_df["timestamp"])
    market_df["date"] = market_df["timestamp"].dt.date

    merged = market_df.merge(
        sentiment_df[["date", "sentiment_score"]],
        on="date",
        how="left",
        suffixes=("", "_sent"),
    )
    merged["sentiment_score"] = merged["sentiment_score"].fillna(0.0)
    merged = merged.drop(columns=["date"], errors="ignore")
    return merged


class DatasetBuilder:
    """
    JOIN market_data + technical_indicators + sentiment_scores → training dataset.
    """

    def __init__(self, config: DatasetBuilderConfig | None = None):
        self.config = config or DatasetBuilderConfig()

    def run(
        self,
        market_df: pd.DataFrame,
        sentiment_df: pd.DataFrame | None = None,
        symbol_id: int | None = None,
        ticker: str | None = None,
    ) -> DatasetBuilderResult:
        """
        Build training dataset.

        Args:
            market_df: OHLCV DataFrame (timestamp, open, high, low, close, volume)
            sentiment_df: Optional sentiment DataFrame (date, sentiment_score). Nếu None, load từ DB nếu có symbol_id/ticker.
            symbol_id: Dùng để load sentiment từ DB nếu sentiment_df None
            ticker: Dùng để load sentiment từ DB nếu sentiment_df None
        """
        df = market_df.copy()

        # 1. Join sentiment
        if sentiment_df is not None:
            df = join_sentiment(df, sentiment_df)
        elif symbol_id is not None or ticker is not None:
            sent = load_sentiment(ticker=ticker, symbol_id=symbol_id)
            df = join_sentiment(df, sent)
        else:
            df["sentiment_score"] = 0.0

        # 2. Technical indicators
        df = add_technical_indicators(
            df,
            indicators=self.config.indicators,
            config=self.config.feature_engineering_config,
        )

        # Drop rows với NaN từ indicators (đầu chuỗi)
        df = df.dropna().reset_index(drop=True)

        if len(df) < 10:
            raise ValueError(f"Quá ít dữ liệu sau khi thêm indicators: {len(df)} rows")

        # 3. Preprocessing (optional)
        preprocessed: PreprocessingResult | None = None
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = f"_{ticker or symbol_id or 'all'}"

        if self.config.run_preprocessing:
            prep_config = self.config.preprocessing_config or PreprocessingConfig()
            prep_config.eda_output_dir = None
            preprocessor = DataPreprocessor(prep_config)
            preprocessed = preprocessor.run(df)
            # Lưu train/val/test riêng
            ext = ".parquet" if self.config.output_format == "parquet" else ".csv"
            for name, part in [("train", preprocessed.train), ("val", preprocessed.val), ("test", preprocessed.test)]:
                out_path = out_dir / f"training_dataset{suffix}_{name}{ext}"
                if self.config.output_format == "parquet":
                    part.to_parquet(out_path, index=False)
                else:
                    part.to_csv(out_path, index=False)
            out_path = out_dir / f"training_dataset{suffix}_train{ext}"
            metadata = {
                "n_train": len(preprocessed.train),
                "n_val": len(preprocessed.val),
                "n_test": len(preprocessed.test),
                "columns": list(preprocessed.train.columns),
                "symbol_id": symbol_id,
                "ticker": ticker,
            }
        else:
            if self.config.output_format == "parquet":
                out_path = out_dir / f"training_dataset{suffix}.parquet"
                df.to_parquet(out_path, index=False)
            else:
                out_path = out_dir / f"training_dataset{suffix}.csv"
                df.to_csv(out_path, index=False)
            metadata = {
                "n_rows": len(df),
                "columns": list(df.columns),
                "symbol_id": symbol_id,
                "ticker": ticker,
            }

        logger.info("Dataset built → %s", out_dir)
        return DatasetBuilderResult(
            raw_df=df,
            preprocessed=preprocessed,
            output_path=out_path,
            metadata=metadata,
        )
