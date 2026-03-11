#!/usr/bin/env python3
"""
FinBERT Inference Pipeline — Task 8.3
--------------------------------------
Script chạy local (RTX 4060 GPU) → batch process news → scores.

Input: JSON/CSV file với cột text (hoặc title+content)
Output: JSON/CSV/Parquet với sentiment_score, sentiment_label

Usage:
  python ml/scripts/run_finbert.py -i ml/data/news_sample.json -o ml/outputs/sentiment_scores.csv
  python ml/scripts/run_finbert.py -i news.csv -o scores.parquet --batch-size 64 --no-gpu
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from ml.pipelines.finbert_inference import FinBERTConfig, process_news_dataframe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_news(input_path: Path) -> pd.DataFrame:
    """Load news từ JSON hoặc CSV."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"File không tồn tại: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix == ".json":
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and "data" in data:
            df = pd.DataFrame(data["data"])
        else:
            df = pd.DataFrame([data])
    elif suffix in (".csv", ".tsv"):
        sep = "\t" if suffix == ".tsv" else ","
        df = pd.read_csv(input_path, sep=sep, encoding="utf-8")
    else:
        raise ValueError(f"Định dạng không hỗ trợ: {suffix}. Dùng .json hoặc .csv")

    return df


def _ensure_text_column(df: pd.DataFrame) -> pd.DataFrame:
    """Tạo cột text từ title + content nếu chưa có."""
    if "text" in df.columns:
        return df
    if "title" in df.columns and "content" in df.columns:
        df = df.copy()
        df["text"] = (df["title"].fillna("") + " " + df["content"].fillna("")).str.strip()
        return df
    if "title" in df.columns:
        df = df.copy()
        df["text"] = df["title"].fillna("").astype(str)
        return df
    if "content" in df.columns:
        df = df.copy()
        df["text"] = df["content"].fillna("").astype(str)
        return df
    raise ValueError("Cần cột 'text' hoặc ('title','content') trong input")


def save_output(df: pd.DataFrame, output_path: Path) -> None:
    """Lưu output theo định dạng file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    suffix = output_path.suffix.lower()
    if suffix == ".json":
        records = df.to_dict(orient="records")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    elif suffix == ".parquet":
        df.to_parquet(output_path, index=False)
    else:
        df.to_csv(output_path, index=False, encoding="utf-8")

    logger.info("Đã lưu %d dòng → %s", len(df), output_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="FinBERT batch inference — phân tích sentiment tin tức tài chính",
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=Path,
        help="Input JSON/CSV file (cột text hoặc title+content)",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Output file (.json, .csv, .parquet)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size cho inference (default: 32)",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
        help="Max token length (default: 512)",
    )
    parser.add_argument(
        "--no-gpu",
        action="store_true",
        help="Chạy trên CPU (mặc định dùng GPU nếu có)",
    )
    parser.add_argument(
        "--text-column",
        type=str,
        default="text",
        help="Tên cột chứa nội dung (default: text)",
    )
    args = parser.parse_args()

    config = FinBERTConfig(
        batch_size=args.batch_size,
        max_length=args.max_length,
        use_gpu=not args.no_gpu,
    )

    df = load_news(args.input)
    if args.text_column in df.columns:
        df["text"] = df[args.text_column]
    else:
        df = _ensure_text_column(df)

    logger.info("Đang xử lý %d tin tức (device=%s)...", len(df), config.device)
    result = process_news_dataframe(df, text_column="text", config=config)
    save_output(result, args.output)

    # Thống kê nhanh
    pos = (result["sentiment_label"] == "POSITIVE").sum()
    neg = (result["sentiment_label"] == "NEGATIVE").sum()
    neu = (result["sentiment_label"] == "NEUTRAL").sum()
    logger.info("Kết quả: POSITIVE=%d, NEGATIVE=%d, NEUTRAL=%d", pos, neg, neu)

    return 0


if __name__ == "__main__":
    sys.exit(main())
