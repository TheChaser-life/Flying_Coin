#!/usr/bin/env python3
"""
Verify Tuần 5 — Kiểm tra toàn bộ pipeline 5.4–5.8
--------------------------------------------------
Chạy tất cả test đơn vị và end-to-end (dùng sample data, không cần DB/MLflow).

Usage:
  python ml/scripts/verify_week5.py
  python ml/scripts/verify_week5.py --verbose
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


def test_5_4_preprocessing() -> bool:
    """5.4 Data Preprocessing pipeline."""
    try:
        import pandas as pd
        import numpy as np
        from ml.pipelines.preprocessing import DataPreprocessor, PreprocessingConfig

        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        rng = np.random.default_rng(42)
        close = 100 + np.cumsum(rng.standard_normal(100) * 2)
        df = pd.DataFrame({
            "timestamp": dates,
            "open": np.roll(close, 1), "high": close + 1, "low": close - 1,
            "close": close, "volume": rng.integers(1_000_000, 10_000_000, 100).astype(float),
        })
        df.loc[0, "open"] = 100

        p = DataPreprocessor(PreprocessingConfig())
        r = p.run(df)
        assert len(r.train) > 0 and len(r.val) > 0 and len(r.test) > 0
        return True
    except Exception as e:
        print(f"  5.4 FAIL: {e}")
        return False


def test_5_5_dataset_builder() -> bool:
    """5.5 Dataset Builder."""
    try:
        import pandas as pd
        import numpy as np
        from ml.pipelines.dataset_builder import DatasetBuilder, DatasetBuilderConfig

        dates = pd.date_range("2023-01-01", periods=200, freq="D")
        rng = np.random.default_rng(42)
        close = 100 + np.cumsum(rng.standard_normal(200) * 2)
        df = pd.DataFrame({
            "timestamp": dates,
            "open": np.roll(close, 1), "high": close + 1, "low": close - 1,
            "close": close, "volume": rng.integers(1_000_000, 10_000_000, 200).astype(float),
        })
        df.loc[0, "open"] = 100

        builder = DatasetBuilder(DatasetBuilderConfig(run_preprocessing=True, output_dir="ml/outputs/verify_week5"))
        result = builder.run(market_df=df)
        assert result.preprocessed is not None
        assert "close" in result.preprocessed.train.columns
        return True
    except Exception as e:
        print(f"  5.5 FAIL: {e}")
        return False


def test_5_6_feature_engineering() -> bool:
    """5.6 Feature Engineering pipeline."""
    try:
        import pandas as pd
        import numpy as np
        from ml.pipelines.feature_engineering import (
            add_technical_indicators,
            FeatureEngineeringPipeline,
            get_feature_columns,
        )

        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        rng = np.random.default_rng(42)
        close = 100 + np.cumsum(rng.standard_normal(100) * 2)
        df = pd.DataFrame({
            "timestamp": dates,
            "open": np.roll(close, 1), "high": close + 1, "low": close - 1,
            "close": close, "volume": rng.integers(1_000_000, 10_000_000, 100).astype(float),
        })
        df.loc[0, "open"] = 100

        df = add_technical_indicators(df, indicators="full")
        assert "rsi" in df.columns and "macd" in df.columns and "sma_7" in df.columns

        pipeline = FeatureEngineeringPipeline()
        result = pipeline.run(df)
        assert len(result.feature_columns) > 0
        return True
    except Exception as e:
        print(f"  5.6 FAIL: {e}")
        return False


def test_5_7_naive_baselines() -> bool:
    """5.7 Naive Baselines."""
    try:
        import numpy as np
        import pandas as pd
        from ml.pipelines.naive_baselines import evaluate_baselines

        rng = np.random.default_rng(42)
        close = 100 + np.cumsum(rng.standard_normal(100) * 2)
        train = pd.DataFrame({"close": close[:70]})
        val = pd.DataFrame({"close": close[70:85]})
        test = pd.DataFrame({"close": close[85:]})

        metrics = evaluate_baselines(train, val, test, ma_window=7)
        assert "naive" in metrics and "ma_7" in metrics
        assert metrics["naive"].rmse >= 0 and metrics["ma_7"].directional_accuracy >= 0
        return True
    except Exception as e:
        print(f"  5.7 FAIL: {e}")
        return False


def test_5_8_arima() -> bool:
    """5.8 ARIMA baseline model."""
    try:
        import numpy as np
        import pandas as pd
        from ml.scripts.train_arima import run_arima_and_evaluate

        rng = np.random.default_rng(42)
        close = 100 + np.cumsum(rng.standard_normal(150) * 2)
        train = pd.DataFrame({"close": close[:100]})
        val = pd.DataFrame({"close": close[100:120]})
        test = pd.DataFrame({"close": close[120:]})

        metrics, fitted = run_arima_and_evaluate(train, val, test, order=(1, 1, 1))
        assert metrics.rmse >= 0 and fitted is not None
        return True
    except Exception as e:
        print(f"  5.8 FAIL: {e}")
        return False


def test_e2e_pipeline() -> bool:
    """End-to-end: Dataset Builder → Naive → ARIMA."""
    try:
        import pandas as pd
        import numpy as np
        from ml.pipelines.dataset_builder import DatasetBuilder, DatasetBuilderConfig
        from ml.pipelines.naive_baselines import evaluate_baselines
        from ml.scripts.train_arima import run_arima_and_evaluate

        dates = pd.date_range("2023-01-01", periods=300, freq="D")
        rng = np.random.default_rng(42)
        close = 100 + np.cumsum(rng.standard_normal(300) * 2)
        df = pd.DataFrame({
            "timestamp": dates,
            "open": np.roll(close, 1), "high": close + 1, "low": close - 1,
            "close": close, "volume": rng.integers(1_000_000, 10_000_000, 300).astype(float),
        })
        df.loc[0, "open"] = 100

        builder = DatasetBuilder(DatasetBuilderConfig(run_preprocessing=True, output_dir="ml/outputs/verify_week5"))
        result = builder.run(df)
        train, val, test = result.preprocessed.train, result.preprocessed.val, result.preprocessed.test

        naive_metrics = evaluate_baselines(train, val, test)
        arima_metrics, _ = run_arima_and_evaluate(train, val, test, order=(1, 1, 1))

        assert len(naive_metrics) == 2 and arima_metrics.rmse >= 0
        return True
    except Exception as e:
        print(f"  E2E FAIL: {e}")
        return False


def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    tasks = [
        ("5.4 Preprocessing", test_5_4_preprocessing),
        ("5.5 Dataset Builder", test_5_5_dataset_builder),
        ("5.6 Feature Engineering", test_5_6_feature_engineering),
        ("5.7 Naive Baselines", test_5_7_naive_baselines),
        ("5.8 ARIMA", test_5_8_arima),
        ("E2E Pipeline", test_e2e_pipeline),
    ]

    print("=" * 50)
    print("Verify Tuần 5 — Feature Engineering, MLflow & Airflow")
    print("=" * 50)

    passed = 0
    for name, fn in tasks:
        if verbose:
            print(f"\nRunning {name}...")
        ok = fn()
        status = "PASS" if ok else "FAIL"
        print(f"  {name}: {status}")
        if ok:
            passed += 1

    print("\n" + "=" * 50)
    print(f"Result: {passed}/{len(tasks)} passed")
    print("=" * 50)
    return 0 if passed == len(tasks) else 1


if __name__ == "__main__":
    sys.exit(main())
