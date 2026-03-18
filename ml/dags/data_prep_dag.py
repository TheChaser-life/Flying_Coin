import os
import pandas as pd
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from sqlalchemy import create_engine
import pyarrow.parquet as pq
import pyarrow as pa

# Configuration from Environment Variables
GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "flying-coin-ml-datasets")
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "flying-coin-489803")
# Connection synced via ExternalSecrets (airflow-secrets)
# Note: ExternalSecret template mapping: market-data-db-url
# In Airflow pods, we can read this from environment or a file.
# The Official Airflow Chart doesn't automatically export all keys to env.
# We'll use a hack to read from Secret volume if mounted, or assume env if we added it.
# For now, let's assume we can fetch it via a Hook or a simple helper if we know the location.
DB_URL_SECRET_PATH = "/opt/airflow/secrets/market-data-db-url"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def extract_and_upload_to_gcs(symbol="all", **context):
    """Trích xuất dữ liệu từ Postgres, chuyển sang Parquet và đẩy lên GCS."""
    
    # Lấy DB URL từ Secret (đã được mount vào Pod nếu cấu hình extraVolumes/extraVolumeMounts)
    # Nếu chưa mount, ta sẽ dùng giá trị mặc định hoặc báo lỗi.
    db_url = os.getenv("MARKET_DATA_DB_URL")
    if not db_url and os.path.exists(DB_URL_SECRET_PATH):
        with open(DB_URL_SECRET_PATH, 'r') as f:
            db_url = f.read().strip()
    
    if not db_url:
        # Fallback to standard connection if possible
        db_url = "postgresql://postgres:postgres@postgres-postgresql-primary.database.svc.cluster.local:5432/market_data"
        print(f"Warning: Using fallback DB URL: {db_url}")

    # Chuyển asyncpg sang psycopg2 nếu cần (Airflow/Pandas dùng sync driver)
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(db_url)
    
    # Query join với bảng symbols để có tên symbol
    query = """
    SELECT m.timestamp, m.close as price, s.ticker as symbol
    FROM market_data m
    JOIN symbols s ON m.symbol_id = s.id
    """
    if symbol != "all":
        query += f" WHERE s.ticker = '{symbol}'"
    
    print(f"Extracting data for {symbol}...")
    df = pd.read_sql(query, engine)
    
    if df.empty:
        print("No data found!")
        return
    
    # Tiền xử lý đơn giản: Tính Moving Average 5 chu kỳ
    df = df.sort_values(['symbol', 'timestamp'])
    df['ma5'] = df.groupby('symbol')['price'].transform(lambda x: x.rolling(window=5).mean())
    
    # Lưu ra file Parquet tạm thời
    temp_path = f"/tmp/dataset_{symbol}.parquet"
    df.to_parquet(temp_path, index=False)
    
    # Upload lên GCS
    gcs_hook = GCSHook()
    destination_path = f"datasets/{datetime.now().strftime('%Y%m%d')}/dataset_{symbol}.parquet"
    
    print(f"Uploading to gs://{GCS_BUCKET}/{destination_path}...")
    gcs_hook.upload(
        bucket_name=GCS_BUCKET,
        object_name=destination_path,
        filename=temp_path
    )
    
    # Cleanup
    os.remove(temp_path)
    print("Done!")

with DAG(
    "data_preparation_v1",
    default_args=default_args,
    description="Sync datasets from Postgres to GCS",
    schedule_interval="@daily",
    catchup=False,
    tags=["mlops", "hybrid"],
) as dag:

    prepare_all = PythonOperator(
        task_id="extract_market_data_all",
        python_callable=extract_and_upload_to_gcs,
        op_kwargs={"symbol": "all"},
    )
