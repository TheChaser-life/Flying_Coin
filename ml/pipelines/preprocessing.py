"""
Data Preprocessing Pipeline — Task 5.4
--------------------------------------
EDA (phân phối, tương quan), xử lý missing values, outlier detection,
normalization/scaling, time-series train/val/test split.

Sử dụng cho: Dataset Builder (5.5), Feature Engineering (5.6), Airflow DAG.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

logger = logging.getLogger(__name__)

# OHLCV columns chuẩn cho market data
OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]
NUMERIC_COLUMNS = OHLCV_COLUMNS


@dataclass
class PreprocessingConfig:
    """Cấu hình pipeline tiền xử lý."""

    # Missing values
    missing_strategy: Literal["ffill", "bfill", "interpolate", "drop"] = "ffill"
    missing_threshold: float = 0.3  # Drop row nếu > 30% cột bị missing

    # Outlier detection
    outlier_method: Literal["iqr", "zscore", "none"] = "iqr"
    iqr_multiplier: float = 1.5
    zscore_threshold: float = 3.0

    # Scaling
    scaler: Literal["minmax", "standard", "robust", "none"] = "minmax"
    scaler_fit_on: Literal["train", "all"] = "train"  # Fit scaler trên train only

    # Time-series split
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15

    # EDA
    save_eda_report: bool = True
    eda_output_dir: str | Path | None = None


@dataclass
class PreprocessingResult:
    """Kết quả pipeline tiền xử lý."""

    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame
    scaler: MinMaxScaler | StandardScaler | RobustScaler | None = None
    eda_report: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


class DataPreprocessor:
    """
    Pipeline tiền xử lý dữ liệu OHLCV cho ML forecasting.

    Luồng: EDA → Missing values → Outlier → Split → Scaling
    """

    def __init__(self, config: PreprocessingConfig | None = None):
        self.config = config or PreprocessingConfig()
        self._scaler = None
        self._eda_report: dict = {}

    def run(
        self,
        df: pd.DataFrame,
        timestamp_col: str = "timestamp",
        target_col: str | None = "close",
    ) -> PreprocessingResult:
        """
        Chạy toàn bộ pipeline tiền xử lý.

        Args:
            df: DataFrame OHLCV (phải có timestamp, open, high, low, close, volume)
            timestamp_col: Tên cột timestamp
            target_col: Cột target (dùng cho scaling, có thể None)

        Returns:
            PreprocessingResult với train/val/test đã xử lý
        """
        df = df.copy()

        # Đảm bảo timestamp là index hoặc sort
        if timestamp_col in df.columns:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            df = df.sort_values(timestamp_col).reset_index(drop=True)

        # 1. EDA (trước khi xử lý)
        self._run_eda(df)

        # 2. Missing values
        df = self._handle_missing(df)

        # 3. Outlier detection & handling
        df = self._handle_outliers(df)

        # 4. Time-series split (trước scaling để fit scaler trên train)
        train, val, test = self._time_series_split(df)

        # 5. Normalization / Scaling
        if self.config.scaler != "none":
            train, val, test = self._scale(train, val, test)

        metadata = {
            "n_train": len(train),
            "n_val": len(val),
            "n_test": len(test),
            "missing_strategy": self.config.missing_strategy,
            "outlier_method": self.config.outlier_method,
            "scaler": self.config.scaler,
        }

        return PreprocessingResult(
            train=train,
            val=val,
            test=test,
            scaler=self._scaler,
            eda_report=self._eda_report,
            metadata=metadata,
        )

    def _run_eda(self, df: pd.DataFrame) -> None:
        """EDA: phân phối, tương quan."""
        numeric = df.select_dtypes(include=[np.number])
        if numeric.empty:
            return

        # Phân phối: stats cơ bản
        stats = numeric.describe().to_dict()
        skewness = numeric.skew().to_dict()
        self._eda_report["distribution"] = {
            "describe": stats,
            "skewness": skewness,
        }

        # Tương quan
        corr = numeric.corr()
        self._eda_report["correlation"] = corr.to_dict()
        self._eda_report["correlation_matrix"] = corr  # Giữ DataFrame để plot

        # Missing count
        missing = df.isnull().sum().to_dict()
        self._eda_report["missing_before"] = missing

        logger.info(
            "EDA: %d rows, skewness close=%.3f, corr(close,volume)=%.3f",
            len(df),
            skewness.get("close", 0),
            corr.loc["close", "volume"] if "volume" in corr.columns else 0,
        )

        # Lưu report nếu cấu hình
        if self.config.save_eda_report and self.config.eda_output_dir:
            self._save_eda_artifacts(df)

    def _save_eda_artifacts(self, df: pd.DataFrame) -> None:
        """Lưu EDA report và plots ra file."""
        out_dir = Path(self.config.eda_output_dir or "ml/outputs/eda")
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import seaborn as sns

            numeric = df.select_dtypes(include=[np.number])

            # 1. Distribution plots
            _fig, axes = plt.subplots(2, 3, figsize=(12, 8))
            axes = axes.flatten()
            for i, col in enumerate(numeric.columns[:6]):
                axes[i].hist(numeric[col].dropna(), bins=50, edgecolor="black", alpha=0.7)
                axes[i].set_title(f"{col} distribution")
            plt.tight_layout()
            plt.savefig(out_dir / "distribution.png", dpi=100)
            plt.close()

            # 2. Correlation heatmap
            corr = numeric.corr()
            plt.figure(figsize=(8, 6))
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
            plt.title("Correlation Matrix")
            plt.tight_layout()
            plt.savefig(out_dir / "correlation.png", dpi=100)
            plt.close()

            # 3. Time series close price
            if "close" in df.columns and "timestamp" in df.columns:
                plt.figure(figsize=(10, 4))
                plt.plot(df["timestamp"], df["close"])
                plt.title("Close Price Over Time")
                plt.xlabel("Timestamp")
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(out_dir / "close_timeseries.png", dpi=100)
                plt.close()

            logger.info("EDA artifacts saved to %s", out_dir)
        except ImportError:
            logger.warning("matplotlib/seaborn not installed — skipping EDA plots")
        except Exception as e:
            logger.warning("Failed to save EDA artifacts: %s", e)

    def _handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Xử lý missing values."""
        missing_count = df.isnull().sum().sum()
        if missing_count == 0:
            return df

        # Drop rows với quá nhiều missing
        thresh = int((1 - self.config.missing_threshold) * len(df.columns))
        df = df.dropna(thresh=thresh)

        numeric_cols = [c for c in OHLCV_COLUMNS if c in df.columns]
        if not numeric_cols:
            return df

        strategy = self.config.missing_strategy
        if strategy == "ffill":
            df[numeric_cols] = df[numeric_cols].ffill()
        elif strategy == "bfill":
            df[numeric_cols] = df[numeric_cols].bfill()
        elif strategy == "interpolate":
            df[numeric_cols] = df[numeric_cols].interpolate(method="linear")
        elif strategy == "drop":
            df = df.dropna(subset=numeric_cols)

        # Fallback: ffill cho bất kỳ còn lại
        df[numeric_cols] = df[numeric_cols].ffill().bfill()

        self._eda_report["missing_after"] = df.isnull().sum().to_dict()
        logger.info("Missing handled: strategy=%s, rows after=%d", strategy, len(df))
        return df

    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Phát hiện và xử lý outlier (cap/clip)."""
        if self.config.outlier_method == "none":
            return df

        numeric_cols = [c for c in OHLCV_COLUMNS if c in df.columns]
        df_out = df.copy()

        for col in numeric_cols:
            series = df_out[col]
            if self.config.outlier_method == "iqr":
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                low = q1 - self.config.iqr_multiplier * iqr
                high = q3 + self.config.iqr_multiplier * iqr
            elif self.config.outlier_method == "zscore":
                mean = series.mean()
                std = series.std()
                if std == 0:
                    continue
                low = mean - self.config.zscore_threshold * std
                high = mean + self.config.zscore_threshold * std
            else:
                continue
            df_out[col] = series.clip(lower=low, upper=high)

        logger.info("Outliers handled: method=%s", self.config.outlier_method)
        return df_out

    def _time_series_split(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Chia train/val/test theo thời gian (không shuffle)."""
        n = len(df)
        train_end = int(n * self.config.train_ratio)
        val_end = int(n * (self.config.train_ratio + self.config.val_ratio))

        train = df.iloc[:train_end].copy()
        val = df.iloc[train_end:val_end].copy()
        test = df.iloc[val_end:].copy()

        logger.info(
            "Time-series split: train=%d, val=%d, test=%d (%.1f/%.1f/%.1f)",
            len(train), len(val), len(test),
            len(train) / n * 100, len(val) / n * 100, len(test) / n * 100,
        )
        return train, val, test

    def _scale(
        self,
        train: pd.DataFrame,
        val: pd.DataFrame,
        test: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Normalization/scaling — fit trên train, transform val/test."""
        scale_cols = [c for c in OHLCV_COLUMNS if c in train.columns]
        if not scale_cols:
            return train, val, test

        if self.config.scaler == "minmax":
            self._scaler = MinMaxScaler()
        elif self.config.scaler == "standard":
            self._scaler = StandardScaler()
        elif self.config.scaler == "robust":
            self._scaler = RobustScaler()
        else:
            return train, val, test

        if self.config.scaler_fit_on == "train":
            train[scale_cols] = self._scaler.fit_transform(train[scale_cols])
            val[scale_cols] = self._scaler.transform(val[scale_cols])
            test[scale_cols] = self._scaler.transform(test[scale_cols])
        else:
            all_data = pd.concat([train[scale_cols], val[scale_cols], test[scale_cols]], axis=0)
            self._scaler.fit(all_data)
            train[scale_cols] = self._scaler.transform(train[scale_cols])
            val[scale_cols] = self._scaler.transform(val[scale_cols])
            test[scale_cols] = self._scaler.transform(test[scale_cols])

        logger.info("Scaled columns: %s (scaler=%s)", scale_cols, self.config.scaler)
        return train, val, test

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform dữ liệu mới bằng scaler đã fit (inference).
        Gọi sau khi đã run().
        """
        if self._scaler is None:
            return df
        scale_cols = [c for c in OHLCV_COLUMNS if c in df.columns]
        df = df.copy()
        df[scale_cols] = self._scaler.transform(df[scale_cols])
        return df

    def inverse_transform(self, df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        """Inverse transform để lấy giá gốc (sau predict)."""
        if self._scaler is None:
            return df
        cols = columns or [c for c in OHLCV_COLUMNS if c in df.columns]
        df = df.copy()
        df[cols] = self._scaler.inverse_transform(df[cols])
        return df
