#!/usr/bin/env python3
"""
Test FinBERT inference pipeline — Task 8.3
Chạy nhanh để verify pipeline hoạt động.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.pipelines.finbert_inference import (
    FinBERTConfig,
    load_finbert_pipeline,
    predict_batch,
    process_news_dataframe,
)
import pandas as pd


def test_predict_batch() -> None:
    """Test batch inference với vài câu mẫu."""
    config = FinBERTConfig(use_gpu=True, batch_size=4)
    pipe = load_finbert_pipeline(config)

    texts = [
        "Stocks rallied as earnings beat expectations.",
        "Company faces bankruptcy amid declining sales.",
        "Fed keeps rates unchanged at 5.25%.",
    ]
    results = predict_batch(pipe, texts, config)
    assert len(results) == 3
    for r in results:
        assert "sentiment_score" in r
        assert "sentiment_label" in r
        assert -1.0 <= r["sentiment_score"] <= 1.0
        assert r["sentiment_label"] in ("POSITIVE", "NEGATIVE", "NEUTRAL")
    print("✓ predict_batch OK:", results)


def test_process_dataframe() -> None:
    """Test process_news_dataframe với sample data."""
    df = pd.DataFrame({
        "id": [1, 2],
        "text": [
            "Markets surge on positive economic data.",
            "Bank reports significant losses.",
        ],
    })
    config = FinBERTConfig(use_gpu=True, batch_size=2)
    result = process_news_dataframe(df, config=config)
    assert "sentiment_score" in result.columns
    assert "sentiment_label" in result.columns
    assert len(result) == 2
    print("✓ process_news_dataframe OK")
    print(result[["id", "sentiment_score", "sentiment_label"]])


if __name__ == "__main__":
    print("Testing FinBERT pipeline...")
    test_predict_batch()
    test_process_dataframe()
    print("\n✅ All tests passed!")
