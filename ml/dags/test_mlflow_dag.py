from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def check_mlflow():
    import os
    uri = os.environ.get("MLFLOW_TRACKING_URI", "not set")
    print(f"MLFLOW_TRACKING_URI={uri}")
    try:
        import mlflow
        mlflow.set_tracking_uri(uri)
        with mlflow.start_run(run_name="airflow_test"):
            mlflow.log_param("source", "airflow_dag")
        print("OK: MLflow connection successful")
    except Exception as e:
        print(f"Error: {e}")

with DAG(
    "test_mlflow",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
) as dag:
    PythonOperator(task_id="check_mlflow", python_callable=check_mlflow)