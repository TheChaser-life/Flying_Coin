"""
FinBERT Service — CPU inference only
------------------------------------
Load ProsusAI/finbert once at startup, run inference on news text.
"""

import logging
from typing import Any

import threading
from typing import Any

logger = logging.getLogger(__name__)

LABEL_TO_SCORE = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}

_pipeline: Any = None
_load_lock = threading.Lock()


def get_finbert_pipeline():
    """Lazy load FinBERT pipeline (CPU)."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    with _load_lock:
        if _pipeline is not None:
            return _pipeline
        try:
            from transformers.pipelines import pipeline
        except ImportError:
            from transformers import pipeline

        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        
        model_name = "ProsusAI/finbert"
        logger.info("Loading FinBERT (CPU) explicitly...")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        # Disable low_cpu_mem_usage to avoid 'meta' device initialization 
        # which can cause "Tensor.item() cannot be called on meta tensors" errors
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, 
            low_cpu_mem_usage=False,
            device_map=None
        )
        model.to("cpu")
        
        _pipeline = pipeline(
            "sentiment-analysis",
            model=model,
            tokenizer=tokenizer,
            truncation=True,
            max_length=512,
            device=-1, # Force CPU device in pipeline
        )
        logger.info("FinBERT loaded on CPU")
    return _pipeline


def predict_sentiment(text: str) -> dict[str, float | str]:
    """
    Run FinBERT on single text. Returns sentiment_score (-1..1), sentiment_label.
    """
    if not text or not text.strip():
        return {"sentiment_score": 0.0, "sentiment_label": "NEUTRAL"}

    pipe = get_finbert_pipeline()
    result = pipe(text[:2000], truncation=True)[0]
    label = result.get("label", "neutral").lower()
    score_raw = result.get("score", 0.5)
    base = LABEL_TO_SCORE.get(label, 0.0)
    sentiment_score = round(base * score_raw, 4)
    sentiment_label = label.upper()

    return {
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
    }
