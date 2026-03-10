# Hướng dẫn thêm MLflow vào Docker Compose (Training mode)

Khi `minikube stop`, MLflow trên Minikube tắt. Cần chạy MLflow riêng để training scripts (XGBoost, LSTM) log được.

---

## 1. Cấu trúc cần có

```
ml/
├── docker-compose-airflow-local.yaml   # Hiện tại: Airflow + postgres
└── docker-compose-mlflow-local.yaml    # Mới: MLflow + postgres + minio (hoặc đơn giản hơn)
```

**Hai cách:**

- **Cách A (đơn giản):** MLflow + 1 postgres (backend) + artifact lưu local `./mlruns`
- **Cách B (đầy đủ):** MLflow + postgres + MinIO (S3-compatible, giống K8s)

---

## 2. Cách A — Đơn giản (khuyến nghị cho local)

### Services cần thêm

| Service | Image | Port | Mục đích |
|---------|-------|------|----------|
| `mlflow-db` | `postgres:15-alpine` | 5434:5432 | Backend store (experiments, runs) |
| `mlflow` | `ghcr.io/mlflow/mlflow:v2.19.0` | 5000:5000 | MLflow tracking server |

### Biến môi trường MLflow

```yaml
MLFLOW_BACKEND_STORE_URI: "postgresql://mlflow:mlflow@mlflow-db:5432/mlflow"
MLFLOW_DEFAULT_ARTIFACT_ROOT: "file:/mlflow/artifacts"  # hoặc ./mlruns nếu mount volume
```

### Volume cho artifacts

```yaml
volumes:
  - ./mlruns:/mlflow/artifacts
```

### Lệnh chạy MLflow

```bash
mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri "${MLFLOW_BACKEND_STORE_URI}" \
  --default-artifact-root "/mlflow/artifacts"
```

### Init database `mlflow`

Postgres cần database `mlflow` và user. Dùng `init` script hoặc `environment`:

```yaml
POSTGRES_USER: mlflow
POSTGRES_PASSWORD: mlflow
POSTGRES_DB: mlflow
```

---

## 3. Cách B — Đầy đủ (Postgres + MinIO)

### Services

| Service | Image | Port | Mục đích |
|---------|-------|------|----------|
| `mlflow-db` | `postgres:15-alpine` | 5434:5432 | Backend store |
| `mlflow-minio` | `minio/minio:latest` | 9000, 9001 | Artifact store (S3) |
| `mlflow` | `ghcr.io/mlflow/mlflow:v2.19.0` | 5000:5000 | Tracking server |

### Biến môi trường MLflow

```yaml
MLFLOW_BACKEND_STORE_URI: "postgresql://mlflow:mlflow@mlflow-db:5432/mlflow"
MLFLOW_DEFAULT_ARTIFACT_ROOT: "s3://mlflow/"
MLFLOW_S3_ENDPOINT_URL: "http://mlflow-minio:9000"
AWS_ACCESS_KEY_ID: "admin"
AWS_SECRET_ACCESS_KEY: "admintesting123"
```

### MinIO

- Command: `minio server /data --console-address :9001`
- Tạo bucket `mlflow` bằng `mc` (minio client) trong init container hoặc job

---

## 4. Tích hợp với Airflow

Sau khi thêm MLflow vào compose, cập nhật **Airflow** để trỏ tới MLflow trong cùng network:

```yaml
# Trong airflow-webserver và airflow-scheduler
MLFLOW_TRACKING_URI: "http://mlflow:5000"   # thay vì host.docker.internal:60185
```

**Điều kiện:** Airflow và MLflow phải cùng Docker network (cùng file compose hoặc `external` network).

---

## 5. Gợi ý cấu trúc file

### Option 1: Một file compose (Airflow + MLflow)

Thêm vào `docker-compose-airflow-local.yaml`:

- Service `mlflow-db` (nếu dùng postgres riêng cho MLflow)
- Service `mlflow`
- Cập nhật `MLFLOW_TRACKING_URI` của Airflow → `http://mlflow:5000`

### Option 2: Hai file compose

- `docker-compose-airflow-local.yaml` — Airflow
- `docker-compose-mlflow-local.yaml` — MLflow + postgres (+ minio)

Chạy: `docker compose -f mlflow.yaml -f airflow.yaml up -d`

Cần khai báo `networks` chung để Airflow và MLflow giao tiếp.

---

## 6. Thứ tự khởi động

1. `mlflow-db` (postgres) — healthcheck
2. `mlflow` — `depends_on: mlflow-db`
3. Airflow — `depends_on` postgres (airflow) + có thể `depends_on: mlflow` nếu cần

---

## 7. Kiểm tra

```bash
# Sau khi docker compose up
curl http://localhost:5000/health
# Hoặc mở http://localhost:5000
```

Training script: `export MLFLOW_TRACKING_URI=http://localhost:5000`
