"""Quick test for preprocessing pipeline."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
from ml.pipelines.preprocessing import DataPreprocessor, PreprocessingConfig

dates = pd.date_range("2023-01-01", periods=100, freq="D")
np.random.seed(42)
close = 100 + np.cumsum(np.random.randn(100) * 2)
df = pd.DataFrame({
    "timestamp": dates,
    "open": np.roll(close, 1),
    "high": close + np.abs(np.random.randn(100)),
    "low": close - np.abs(np.random.randn(100)),
    "close": close,
    "volume": np.random.randint(1_000_000, 10_000_000, 100).astype(float),
})
df.loc[0, "open"] = 100

p = DataPreprocessor(PreprocessingConfig())
r = p.run(df)
print(f"OK: train={len(r.train)} val={len(r.val)} test={len(r.test)}")
