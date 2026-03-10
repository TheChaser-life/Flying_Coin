"""Quick test for Naive Baselines."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
from ml.pipelines.naive_baselines import evaluate_baselines, compute_metrics, naive_forecast, ma_forecast

# Sample train/val/test
np.random.seed(42)
n = 100
close = 100 + np.cumsum(np.random.randn(n) * 2)
train = pd.DataFrame({"close": close[:70]})
val = pd.DataFrame({"close": close[70:85]})
test = pd.DataFrame({"close": close[85:]})

metrics = evaluate_baselines(train, val, test, ma_window=7)
print("naive:", metrics["naive"])
print("ma_7:", metrics["ma_7"])
assert metrics["naive"].rmse >= 0
assert metrics["ma_7"].directional_accuracy >= 0
print("OK")
