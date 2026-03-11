#!/usr/bin/env python3
"""
Trigger Server — Cách B (train trên host)
-----------------------------------------
HTTP server chạy trên host, nhận request từ Airflow (trong Docker) để trigger
training script. Script chạy trong venv của host → dùng được GPU (RTX 4060).

Usage:
  python ml/scripts/trigger_server.py
  # Listen trên http://0.0.0.0:8765

Airflow gọi: curl -X POST http://host.docker.internal:8765/train-xgboost
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

# Project root (2 levels up from ml/scripts/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ML_SCRIPTS = PROJECT_ROOT / "ml" / "scripts"
DATASETS_DIR = PROJECT_ROOT / "ml" / "outputs" / "datasets"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# MLflow chạy trong Docker, expose port 5000. Từ host cần dùng localhost:5000
MLFLOW_URI = "http://localhost:5000"


def run_training(script_name: str, symbol: str = "all") -> tuple[int, str]:
    """Chạy training script trong venv của host. Trả về (exit_code, output)."""
    script_path = ML_SCRIPTS / script_name
    if not script_path.exists():
        return 1, f"Script không tồn tại: {script_path}"

    cmd = [
        sys.executable,
        str(script_path),
        "-d", str(DATASETS_DIR),
        "-s", symbol,
    ]
    env = {
        **os.environ,
        "MLFLOW_TRACKING_URI": MLFLOW_URI,
        "PYTHONIOENCODING": "utf-8",  # Tránh lỗi charmap với emoji (🏃) trong output MLflow
    }
    logger.info("Chạy: %s (MLFLOW_TRACKING_URI=%s)", " ".join(cmd), MLFLOW_URI)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3600,  # 1 giờ
            env=env,
        )
        out = (result.stdout or "") + (result.stderr or "")
        return result.returncode, out
    except subprocess.TimeoutExpired:
        return 1, "Timeout (quá 1 giờ)"
    except Exception as e:
        return 1, str(e)


def create_app():
    """Tạo Flask app cho trigger server."""
    try:
        from flask import Flask, jsonify, request
    except ImportError:
        raise ImportError("Cần cài flask: pip install flask")

    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "message": "Trigger server running"})

    @app.route("/train-arima", methods=["POST"])
    def train_arima():
        symbol = request.json.get("symbol", "all") if request.is_json else "all"
        code, out = run_training("train_arima.py", symbol)
        return jsonify({"exit_code": code, "output": out}), 200 if code == 0 else 500

    @app.route("/train-xgboost", methods=["POST"])
    def train_xgboost():
        symbol = request.json.get("symbol", "all") if request.is_json else "all"
        code, out = run_training("train_xgboost.py", symbol)
        return jsonify({"exit_code": code, "output": out}), 200 if code == 0 else 500

    @app.route("/train-lstm", methods=["POST"])
    def train_lstm():
        symbol = request.json.get("symbol", "all") if request.is_json else "all"
        code, out = run_training("train_lstm.py", symbol)
        return jsonify({"exit_code": code, "output": out}), 200 if code == 0 else 500

    @app.route("/fetch-news", methods=["POST"])
    def fetch_news():
        """Fetch news batch (Task 8.5) → ml/outputs/news_batch.json."""
        output = str(PROJECT_ROOT / "ml" / "outputs" / "news_batch.json")
        cmd = [sys.executable, str(ML_SCRIPTS / "fetch_news_batch.py")]
        env = {**os.environ, "NEWS_BATCH_OUTPUT": output, "PYTHONPATH": str(PROJECT_ROOT)}
        try:
            result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, env=env)
            out = (result.stdout or "") + (result.stderr or "")
            return jsonify({"exit_code": result.returncode, "output": out}), 200
        except Exception as e:
            return jsonify({"exit_code": 1, "output": str(e)}), 500

    @app.route("/run-finbert", methods=["POST"])
    def run_finbert():
        """Chạy FinBERT batch inference (Task 8.5). Input/Output từ ml/outputs/."""
        data = request.json or {}
        input_path = data.get("input") or str(PROJECT_ROOT / "ml" / "outputs" / "news_batch.json")
        output_path = data.get("output") or str(PROJECT_ROOT / "ml" / "outputs" / "sentiment_scores_batch.json")
        cmd = [
            sys.executable,
            str(ML_SCRIPTS / "run_finbert.py"),
            "-i", input_path,
            "-o", output_path,
            "--no-gpu",  # Trigger server thường chạy CPU; dùng GPU khi chạy trực tiếp
        ]
        try:
            result = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=1800,
                env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
            )
            out = (result.stdout or "") + (result.stderr or "")
            return jsonify({"exit_code": result.returncode, "output": out}), 200
        except subprocess.TimeoutExpired:
            return jsonify({"exit_code": 1, "output": "Timeout 30 phút"}), 500
        except Exception as e:
            return jsonify({"exit_code": 1, "output": str(e)}), 500

    return app


def main():
    app = create_app()
    logger.info("Trigger Server chạy tại http://0.0.0.0:8765")
    logger.info("Endpoints: POST /train-arima, /train-xgboost, /train-lstm, /run-finbert")
    app.run(host="0.0.0.0", port=8765, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
