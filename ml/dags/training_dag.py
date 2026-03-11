"""
Training Pipeline DAG — Cách A (dataset parquet) + Cách B (train trên host)
---------------------------------------------------------------------------
- Cách A: Đọc dataset từ /opt/airflow/outputs/datasets/*.parquet
- Cách B: PythonOperator gọi Trigger Server trên host (http://host.docker.internal:8765)
          → script chạy trong venv host → dùng GPU RTX 4060
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from pathlib import Path

TRIGGER_URL = "http://host.docker.internal:8765"


def check_datasets(**context):
    """Kiểm tra dataset parquet có sẵn (Cách A)."""
    data_dir = Path("/opt/airflow/outputs/datasets")
    if not data_dir.exists():
        raise FileNotFoundError(f"Thư mục dataset không tồn tại: {data_dir}")

    parquets = list(data_dir.glob("*.parquet"))
    if not parquets:
        raise FileNotFoundError(f"Không có file parquet trong {data_dir}")

    # Cần ít nhất train/val/test cho symbol "all"
    required = ["training_dataset_all_train", "training_dataset_all_val", "training_dataset_all_test"]
    found = [p.stem for p in parquets]
    missing = [r for r in required if not any(r in f for f in found)]
    if missing:
        raise FileNotFoundError(f"Thiếu dataset: {missing}. Cần: training_dataset_all_*_train/val/test.parquet")

    print(f"OK: Tìm thấy {len(parquets)} file parquet trong {data_dir}")
    return True


def trigger_training(endpoint: str, model_name: str, **context):
    """
    Gọi Trigger Server trên host. Training chạy đồng bộ — request chờ đến khi xong.
    ARIMA: ~1-3 phút | XGBoost: ~2-5 phút | LSTM: ~5-15 phút (tùy data).
    """
    import urllib.request
    import json

    url = f"{TRIGGER_URL}/{endpoint}"
    data = json.dumps({"symbol": "all"}).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=3600) as resp:
            result = json.loads(resp.read().decode())
            exit_code = result.get("exit_code", -1)
            output = result.get("output", "")

            print(f"=== {model_name} (exit_code={exit_code}) ===")
            print(output)
            print("=" * 50)

            if exit_code != 0:
                raise RuntimeError(f"{model_name} failed with exit_code={exit_code}")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"HTTP {e.code}: {body}")
        raise
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        print("Kiểm tra: Trigger Server đang chạy? python ml/scripts/trigger_server.py")
        raise


with DAG(
    "training_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ml", "training"],
) as dag:
    check_data = PythonOperator(
        task_id="check_datasets",
        python_callable=check_datasets,
    )

    trigger_arima = PythonOperator(
        task_id="trigger_train_arima",
        python_callable=trigger_training,
        op_kwargs={"endpoint": "train-arima", "model_name": "ARIMA"},
    )

    trigger_xgboost = PythonOperator(
        task_id="trigger_train_xgboost",
        python_callable=trigger_training,
        op_kwargs={"endpoint": "train-xgboost", "model_name": "XGBoost"},
    )

    trigger_lstm = PythonOperator(
        task_id="trigger_train_lstm",
        python_callable=trigger_training,
        op_kwargs={"endpoint": "train-lstm", "model_name": "LSTM"},
    )

    # Flow: check data → arima → xgboost → lstm (arima có sẵn, xgboost/lstm cần tạo script)
    check_data >> trigger_arima >> trigger_xgboost >> trigger_lstm
