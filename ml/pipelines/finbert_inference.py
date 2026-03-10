"""
FinBERT Inference Pipeline — Task 8.3
-------------------------------------
Batch sentiment analysis cho tin tức tài chính.
Chạy local (RTX 4060 GPU) → batch process news → scores.

Output: sentiment_score (-1.0 → +1.0), sentiment_label (POSITIVE/NEGATIVE/NEUTRAL)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd
import torch

logger = logging.getLogger(__name__)

# FinBERT labels → numeric score
LABEL_TO_SCORE = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}


@dataclass
class FinBERTConfig:
    """Config cho FinBERT inference."""

    model_name: str = "ProsusAI/finbert"
    batch_size: int = 32
    max_length: int = 512
    use_gpu: bool = True
    device: str | None = None  # auto-detect nếu None

    def __post_init__(self) -> None:
        if self.device is None:
            self.device = "cuda" if (self.use_gpu and torch.cuda.is_available()) else "cpu"
        logger.info("FinBERT device: %s", self.device)


def load_finbert_pipeline(config: FinBERTConfig | None = None) -> Any:
    """
    Load FinBERT sentiment pipeline (Hugging Face Transformers).
    Tự động dùng GPU nếu có (RTX 4060).
    """
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

    config = config or FinBERTConfig()
    logger.info("Loading FinBERT model: %s", config.model_name)

    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(config.model_name)
    model = model.to(config.device)

    pipe = pipeline(
        "sentiment-analysis",
        model=model,
        tokenizer=tokenizer,
        device=0 if config.device == "cuda" else -1,
        truncation=True,
        max_length=config.max_length,
        batch_size=config.batch_size,
    )
    return pipe


def _label_to_score(label: str, confidence: float) -> float:
    """
    Chuyển label + confidence → sentiment_score (-1.0 → +1.0).
    positive * conf → +1 * conf, negative * conf → -1 * conf, neutral → 0.
    """
    base = LABEL_TO_SCORE.get(label.lower(), 0.0)
    return base * confidence


def predict_batch(
    pipe: Any,
    texts: list[str],
    config: FinBERTConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Batch inference cho danh sách văn bản.
    Trả về list dict: sentiment_score, sentiment_label, confidence.
    """
    config = config or FinBERTConfig()
    if not texts:
        return []

    # Hugging Face pipeline trả về [{'label': 'positive', 'score': 0.99}, ...]
    # label có thể là 'positive', 'negative', 'neutral'
    results = pipe(texts, batch_size=config.batch_size)

    output = []
    for r in results:
        label = r.get("label", "neutral")
        score_raw = r.get("score", 0.5)
        sentiment_label = label.upper()
        sentiment_score = _label_to_score(label, score_raw)
        output.append(
            {
                "sentiment_score": round(sentiment_score, 4),
                "sentiment_label": sentiment_label,
                "confidence": round(score_raw, 4),
            }
        )
    return output


def process_news_dataframe(
    df: pd.DataFrame,
    text_column: str = "text",
    config: FinBERTConfig | None = None,
) -> pd.DataFrame:
    """
    Xử lý DataFrame news → thêm cột sentiment_score, sentiment_label.
    text_column: cột chứa nội dung (có thể merge title + content).
    """
    config = config or FinBERTConfig()
    if text_column not in df.columns:
        raise ValueError(f"DataFrame phải có cột '{text_column}'")

    # Chuẩn hóa text: kết hợp title + content nếu có
    texts = df[text_column].fillna("").astype(str).tolist()
    # Loại bỏ rỗng hoặc quá ngắn
    texts = [t.strip() or "No content" for t in texts]

    pipe = load_finbert_pipeline(config)
    results = predict_batch(pipe, texts, config)

    out = df.copy()
    out["sentiment_score"] = [r["sentiment_score"] for r in results]
    out["sentiment_label"] = [r["sentiment_label"] for r in results]
    out["sentiment_confidence"] = [r["confidence"] for r in results]

    return out
