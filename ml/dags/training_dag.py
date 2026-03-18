from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from datetime import datetime, timedelta
import os

# Configuration
GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "flying-coin-ml-datasets")
TRIGGER_URL = "http://ssh-bastion-svc.mlops.svc.cluster.local:8765"

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def check_datasets_gcs(**context):
    """Kiểm tra dataset parquet có sẵn trên GCS."""
    hook = GCSHook()
    # Đường dẫn mẫu: datasets/20260314/dataset_all.parquet
    prefix = f"datasets/{datetime.now().strftime('%Y%m%d')}/"
    files = hook.list(bucket_name=GCS_BUCKET, prefix=prefix)
    
    if not files:
        raise FileNotFoundError(f"Không tìm thấy dataset trong gs://{GCS_BUCKET}/{prefix}")
    
    print(f"Found datasets: {files}")
    # Truyền đường dẫn cho task sau qua XCom
    context['ti'].xcom_push(key='dataset_path', value=files[0])
    return files[0]


def trigger_training(endpoint: str, model_name: str, **context):
    """
    Gọi Trigger Server trên host. Payload bao gồm thông tin GCS.
    """
    import urllib.request
    import json

    dataset_path = context['ti'].xcom_pull(task_ids='check_datasets_gcs', key='dataset_path')
    
    url = f"{TRIGGER_URL}/{endpoint}"
    payload = {
        "symbol": "all",
        "gcs_bucket": GCS_BUCKET,
        "gcs_path": dataset_path
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})

    print(f"Triggering {model_name} with GCS source: gs://{GCS_BUCKET}/{dataset_path}")
    
    try:
        with urllib.request.urlopen(req, timeout=3600) as resp:
            result = json.loads(resp.read().decode())
            exit_code = result.get("exit_code", -1)
            output = result.get("output", "")

            print(f"=== {model_name} (exit_code={exit_code}) ===")
            print(output)
            
            if exit_code != 0:
                raise RuntimeError(f"{model_name} failed with exit_code={exit_code}")
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"Connection error to trigger server: {e}")
        raise


with DAG(
    "training_pipeline_v2",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ml", "training", "hybrid"],
) as dag:
    check_data = PythonOperator(
        task_id="check_datasets_gcs",
        python_callable=check_datasets_gcs,
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

    check_data >> trigger_arima >> trigger_xgboost >> trigger_lstm
