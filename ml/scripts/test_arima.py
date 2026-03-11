"""Quick test for ARIMA training."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
from ml.scripts.train_arima import run_arima_and_evaluate

np.random.seed(42)
n = 150
close = 100 + np.cumsum(np.random.randn(n) * 2)
train = pd.DataFrame({"close": close[:100]})
val = pd.DataFrame({"close": close[100:120]})
test = pd.DataFrame({"close": close[120:]})

metrics, fitted = run_arima_and_evaluate(train, val, test, order=(1, 1, 1))
print(f"ARIMA: RMSE={metrics.rmse:.4f} MAE={metrics.mae:.4f} DA={metrics.directional_accuracy:.1f}%")
assert metrics.rmse >= 0
print("OK")
