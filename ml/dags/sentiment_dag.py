"""
Sentiment Pipeline DAG — Task 8.5
---------------------------------
Steps: fetch_news → run_finbert → sentiment scores output.
Chạy qua Trigger Server trên host (FinBERT có thể dùng GPU nếu bỏ --no-gpu).
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import urllib.request
import json

TRIGGER_URL = "http://host.docker.internal:8765"


def call_trigger(endpoint: str, **context):
    """Gọi Trigger Server trên host."""
    url = f"{TRIGGER_URL}/{endpoint}"
    data = json.dumps({}).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            result = json.loads(resp.read().decode())
            exit_code = result.get("exit_code", -1)
            output = result.get("output", "")
            print(f"=== {endpoint} (exit_code={exit_code}) ===")
            print(output[:2000])
            if exit_code != 0:
                raise RuntimeError(f"{endpoint} failed with exit_code={exit_code}")
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        print("Kiểm tra: Trigger Server đang chạy? python ml/scripts/trigger_server.py")
        raise


with DAG(
    "sentiment_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["sentiment", "nlp"],
) as dag:
    fetch_news = PythonOperator(
        task_id="fetch_news",
        python_callable=call_trigger,
        op_kwargs={"endpoint": "fetch-news"},
    )

    run_finbert = PythonOperator(
        task_id="run_finbert",
        python_callable=call_trigger,
        op_kwargs={"endpoint": "run-finbert"},
    )

    fetch_news >> run_finbert
