"""
Feature Engineering Pipeline — Task 5.6
----------------------------------------
Technical Indicators: SMA, EMA, RSI, MACD, Bollinger Bands, Stochastic,
ATR, OBV, VWAP, ADX. Lưu vào dataset.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Chuẩn theo ml-mlops: SMA/EMA 7,14,21,50,200
DEFAULT_SMA_WINDOWS = [7, 14, 21, 50, 200]
DEFAULT_EMA_SPANS = [7, 14, 21, 50, 200]


def add_sma(df: pd.DataFrame, close_col: str = "close", windows: list[int] | None = None) -> pd.DataFrame:
    """Simple Moving Average."""
    windows = windows or DEFAULT_SMA_WINDOWS
    for w in windows:
        df[f"sma_{w}"] = df[close_col].rolling(window=w, min_periods=1).mean()
    return df


def add_ema(df: pd.DataFrame, close_col: str = "close", spans: list[int] | None = None) -> pd.DataFrame:
    """Exponential Moving Average."""
    spans = spans or DEFAULT_EMA_SPANS
    for s in spans:
        df[f"ema_{s}"] = df[close_col].ewm(span=s, adjust=False).mean()
    return df


def add_rsi(df: pd.DataFrame, close_col: str = "close", period: int = 14) -> pd.DataFrame:
    """RSI (Relative Strength Index)."""
    delta = df[close_col].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi"] = df["rsi"].fillna(50)
    return df


def add_macd(
    df: pd.DataFrame,
    close_col: str = "close",
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """MACD (Moving Average Convergence Divergence)."""
    ema_fast = df[close_col].ewm(span=fast, adjust=False).mean()
    ema_slow = df[close_col].ewm(span=slow, adjust=False).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return df


def add_bollinger_bands(
    df: pd.DataFrame,
    close_col: str = "close",
    period: int = 20,
    std_dev: float = 2.0,
) -> pd.DataFrame:
    """Bollinger Bands."""
    sma = df[close_col].rolling(window=period, min_periods=1).mean()
    std = df[close_col].rolling(window=period, min_periods=1).std()
    df["bb_upper"] = sma + std_dev * std
    df["bb_lower"] = sma - std_dev * std
    df["bb_mid"] = sma
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"].replace(0, np.nan)
    df["bb_width"] = df["bb_width"].fillna(0)
    return df


def add_stochastic(
    df: pd.DataFrame,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    k_period: int = 14,
    d_period: int = 3,
) -> pd.DataFrame:
    """Stochastic Oscillator (%K, %D)."""
    low_min = df[low_col].rolling(window=k_period, min_periods=1).min()
    high_max = df[high_col].rolling(window=k_period, min_periods=1).max()
    df["stoch_k"] = 100 * (df[close_col] - low_min) / (high_max - low_min).replace(0, np.nan)
    df["stoch_k"] = df["stoch_k"].fillna(50)
    df["stoch_d"] = df["stoch_k"].rolling(window=d_period, min_periods=1).mean()
    return df


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """ATR (Average True Range) — Volatility."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr"] = tr.rolling(window=period, min_periods=1).mean()
    return df


def add_obv(df: pd.DataFrame, close_col: str = "close", volume_col: str = "volume") -> pd.DataFrame:
    """OBV (On-Balance Volume)."""
    direction = np.sign(df[close_col].diff())
    direction.iloc[0] = 0
    df["obv"] = (direction * df[volume_col]).cumsum()
    return df


def add_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """VWAP (Volume Weighted Average Price) — cần typical_price * volume."""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap"] = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()
    return df


def add_adx(
    df: pd.DataFrame,
    period: int = 14,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.DataFrame:
    """ADX (Average Directional Index) — Trend strength."""
    high = df[high_col]
    low = df[low_col]
    close = df[close_col]
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)

    plus_dm = high - prev_high
    minus_dm = prev_low - low
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(window=period, min_periods=1).mean()
    plus_di = 100 * (plus_dm.rolling(window=period, min_periods=1).mean() / atr.replace(0, np.nan))
    minus_di = 100 * (minus_dm.rolling(window=period, min_periods=1).mean() / atr.replace(0, np.nan))
    plus_di = plus_di.fillna(0)
    minus_di = minus_di.fillna(0)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    dx = dx.fillna(0)
    df["adx"] = dx.rolling(window=period, min_periods=1).mean()
    df["plus_di"] = plus_di
    df["minus_di"] = minus_di
    return df


@dataclass
class FeatureEngineeringConfig:
    """Cấu hình Feature Engineering pipeline."""

    sma_windows: list[int] = field(default_factory=lambda: [7, 14, 21, 50, 200])
    ema_spans: list[int] = field(default_factory=lambda: [7, 14, 21, 50, 200])
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bb_period: int = 20
    bb_std: float = 2.0
    stoch_period: int = 14
    atr_period: int = 14
    adx_period: int = 14

    # Bật/tắt từng nhóm
    include_sma: bool = True
    include_ema: bool = True
    include_rsi: bool = True
    include_macd: bool = True
    include_bollinger: bool = True
    include_stochastic: bool = True
    include_atr: bool = True
    include_obv: bool = True
    include_vwap: bool = True
    include_adx: bool = True


@dataclass
class FeatureEngineeringResult:
    """Kết quả Feature Engineering pipeline."""

    df: pd.DataFrame
    feature_columns: list[str]
    metadata: dict = field(default_factory=dict)


def add_technical_indicators(
    df: pd.DataFrame,
    close_col: str = "close",
    indicators: Literal["all", "basic", "full"] = "all",
    config: FeatureEngineeringConfig | None = None,
) -> pd.DataFrame:
    """
    Thêm technical indicators vào DataFrame.

    - basic: SMA(7,14), EMA(7,14), RSI(14)
    - full: + MACD, Bollinger Bands, Stochastic, ATR, OBV, VWAP, ADX
    - all: full (alias)
    """
    df = df.copy()
    cfg = config or FeatureEngineeringConfig()

    if indicators in ("basic", "all", "full"):
        if cfg.include_sma:
            add_sma(df, close_col, cfg.sma_windows if indicators in ("full", "all") else [7, 14])
        if cfg.include_ema:
            add_ema(df, close_col, cfg.ema_spans if indicators in ("full", "all") else [7, 14])
        if cfg.include_rsi:
            add_rsi(df, close_col, cfg.rsi_period)
    if indicators in ("full", "all"):
        if cfg.include_macd:
            add_macd(df, close_col, cfg.macd_fast, cfg.macd_slow, cfg.macd_signal)
        if cfg.include_bollinger:
            add_bollinger_bands(df, close_col, cfg.bb_period, cfg.bb_std)
        if cfg.include_stochastic:
            add_stochastic(df, k_period=cfg.stoch_period, d_period=3)
        if cfg.include_atr:
            add_atr(df, cfg.atr_period)
        if cfg.include_obv:
            add_obv(df, close_col)
        if cfg.include_vwap:
            add_vwap(df)
        if cfg.include_adx:
            add_adx(df, cfg.adx_period)

    logger.info("Added technical indicators: %s", indicators)
    return df


def get_feature_columns(df: pd.DataFrame, exclude: list[str] | None = None) -> list[str]:
    """Lấy danh sách cột feature (bỏ OHLCV + timestamp)."""
    base = ["timestamp", "open", "high", "low", "close", "volume"]
    exclude = exclude or []
    base = base + exclude
    return [c for c in df.columns if c not in base and df[c].dtype in ("float64", "int64")]


class FeatureEngineeringPipeline:
    """
    Pipeline Feature Engineering — chạy standalone hoặc tích hợp Dataset Builder.
    Lưu kết quả vào file dataset.
    """

    def __init__(self, config: FeatureEngineeringConfig | None = None):
        self.config = config or FeatureEngineeringConfig()

    def run(
        self,
        df: pd.DataFrame,
        output_path: str | Path | None = None,
        output_format: Literal["parquet", "csv"] = "parquet",
    ) -> FeatureEngineeringResult:
        """
        Chạy pipeline: thêm tất cả indicators → lưu dataset.

        Args:
            df: OHLCV DataFrame
            output_path: Đường dẫn lưu file (nếu None thì không lưu)
            output_format: parquet hoặc csv
        """
        df = add_technical_indicators(df, indicators="full", config=self.config)
        df = df.dropna().reset_index(drop=True)

        feature_cols = get_feature_columns(df)
        metadata = {"n_rows": len(df), "n_features": len(feature_cols), "features": feature_cols}

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_format == "parquet":
                df.to_parquet(output_path, index=False)
            else:
                df.to_csv(output_path, index=False)
            metadata["output_path"] = str(output_path)
            logger.info("Feature engineering done: %d rows, %d features → %s", len(df), len(feature_cols), output_path)

        return FeatureEngineeringResult(df=df, feature_columns=feature_cols, metadata=metadata)
