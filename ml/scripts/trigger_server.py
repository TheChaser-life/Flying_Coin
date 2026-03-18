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

import sys
# Force line buffering for stdout/stderr to ensure logs appear in antigravity
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

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


def download_from_gcs(bucket_name: str, gcs_path: str, local_dest: Path):
    """Tải file từ GCS về local."""
    try:
        from google.cloud import storage
        # Lấy project_id từ env hoặc mặc định flying-coin-489803
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "flying-coin-489803")
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        
        local_dest.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading gs://{bucket_name}/{gcs_path} to {local_dest}...")
        blob.download_to_filename(str(local_dest))
        return True
    except Exception as e:
        logger.error(f"GCS Download Error: {e}")
        return False


def run_training(script_name: str, symbol: str = "all", dataset_file: str = None) -> tuple[int, str]:
    """Chạy training script trong venv của host. Trả về (exit_code, output)."""
    script_path = ML_SCRIPTS / script_name
    if not script_path.exists():
        return 1, f"Script không tồn tại: {script_path}"

    if dataset_file:
        # Nếu có dataset_file từ GCS, dùng -i và không dùng -d
        input_file = DATASETS_DIR / dataset_file
        cmd = [
            sys.executable,
            str(script_path),
            "-i", str(input_file),
            "-s", symbol,
        ]
    else:
        cmd = [
            sys.executable,
            str(script_path),
            "-d", str(DATASETS_DIR),
            "-s", symbol,
        ]

    env = {
        **os.environ,
        "MLFLOW_TRACKING_URI": MLFLOW_URI,
        "PYTHONIOENCODING": "utf-8",
    }
    logger.info("Chạy: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3600,
            env=env,
        )
        out = (result.stdout or "") + (result.stderr or "")
        return result.returncode, out
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

    def handle_train_request(script_name):
        data = request.json or {}
        symbol = data.get("symbol", "all")
        bucket = data.get("gcs_bucket")
        gcs_path = data.get("gcs_path")
        
        dataset_file = None
        if bucket and gcs_path:
            local_name = gcs_path.split("/")[-1]
            local_dest = DATASETS_DIR / local_name
            if download_from_gcs(bucket, gcs_path, local_dest):
                dataset_file = local_name
            else:
                return jsonify({"exit_code": 1, "output": "Failed to download dataset from GCS"}), 500
        
        try:
            code, out = run_training(script_name, symbol, dataset_file)
            if code != 0:
                logger.error(f"Training failed with code {code}. Output:\n{out}")
            return jsonify({"exit_code": code, "output": out}), 200 if code == 0 else 500
        except Exception as e:
            logger.error(f"Unexpected error in handle_train_request: {e}", exc_info=True)
            return jsonify({"exit_code": 1, "output": str(e)}), 500

    @app.route("/train-arima", methods=["POST"])
    def train_arima():
        return handle_train_request("train_arima.py")

    @app.route("/train-xgboost", methods=["POST"])
    def train_xgboost():
        return handle_train_request("train_xgboost.py")

    @app.route("/train-lstm", methods=["POST"])
    def train_lstm():
        return handle_train_request("train_lstm.py")

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
