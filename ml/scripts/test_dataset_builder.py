"""Quick test for Dataset Builder."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
from ml.pipelines.dataset_builder import DatasetBuilder, DatasetBuilderConfig, join_sentiment
from ml.pipelines.feature_engineering import add_technical_indicators

# Sample OHLCV
dates = pd.date_range("2023-01-01", periods=200, freq="D")
np.random.seed(42)
close = 100 + np.cumsum(np.random.randn(200) * 2)
df = pd.DataFrame({
    "timestamp": dates,
    "open": np.roll(close, 1),
    "high": close + np.abs(np.random.randn(200)),
    "low": close - np.abs(np.random.randn(200)),
    "close": close,
    "volume": np.random.randint(1_000_000, 10_000_000, 200).astype(float),
})
df.loc[0, "open"] = 100

config = DatasetBuilderConfig(run_preprocessing=True, output_dir="ml/outputs/datasets_test")
builder = DatasetBuilder(config)
result = builder.run(market_df=df)

print(f"OK: {result.metadata}")
print(f"Output: {result.output_path}")
if result.preprocessed:
    print(f"Train: {len(result.preprocessed.train)}, Val: {len(result.preprocessed.val)}, Test: {len(result.preprocessed.test)}")
