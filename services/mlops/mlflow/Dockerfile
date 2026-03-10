FROM ghcr.io/mlflow/mlflow:v2.19.0

# psycopg2-binary: PostgreSQL driver for backend store
# boto3: S3/MinIO artifact store (local)
# google-cloud-storage: GCS artifact store (GCP)
RUN pip install --no-cache-dir \
    psycopg2-binary \
    boto3 \
    google-cloud-storage
