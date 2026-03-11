# Kiểm tra Tuần 5 — Feature Engineering, MLflow & Airflow

## Trạng thái tasks

| # | Task | Trạng thái | Người |
|---|------|------------|-------|
| 5.1 | MLflow server trên Minikube | ✅ Done | 👤 |
| 5.2 | Training environment setup | ✅ Done | 👤 |
| 5.3 | Airflow setup (Docker Compose) | ✅ Done | 👤 |
| 5.4 | Data Preprocessing pipeline | ✅ Done | 🤖 |
| 5.5 | Dataset Builder | ✅ Done | 🤖 |
| 5.6 | Feature Engineering pipeline | ✅ Done | 🤖 |
| 5.7 | Naive Baselines | ✅ Done | 🤖 |
| 5.8 | ARIMA baseline model | ✅ Done | 🤖 |

**→ Tất cả 8 tasks Tuần 5 đã hoàn thành.**

---

## Cách kiểm tra

### 1. Kiểm tra nhanh (không cần DB/MLflow)

Chạy script verify tổng hợp:

```bash
cd "c:\code2\Working_Project (I'll name it later)"
python ml/scripts/verify_week5.py
```

Script sẽ test:
- 5.4 Preprocessing
- 5.5 Dataset Builder
- 5.6 Feature Engineering
- 5.7 Naive Baselines
- 5.8 ARIMA
- E2E Pipeline (full flow)

Kết quả mong đợi: `6/6 passed`

### 2. Kiểm tra từng component

```bash
# 5.4
python ml/scripts/test_preprocessing.py

# 5.5
python ml/scripts/test_dataset_builder.py

# 5.6 (chạy feature engineering với sample)
python ml/scripts/run_feature_engineering.py

# 5.7
python ml/scripts/test_naive_baselines.py

# 5.8
python ml/scripts/test_arima.py
```

### 3. Kiểm tra với MLflow (cần MLflow server chạy)

```bash
# Set MLflow URI (nếu dùng Minikube)
# $env:MLFLOW_TRACKING_URI = "http://localhost:30500"  # PowerShell
# export MLFLOW_TRACKING_URI=http://localhost:30500   # Bash

# Chạy naive baselines → log MLflow
python ml/scripts/run_naive_baselines.py

# Chạy ARIMA → log MLflow
python ml/scripts/train_arima.py
```

### 4. Kiểm tra với dữ liệu thật (PostgreSQL)

**Cần:** Minikube chạy + PostgreSQL đã deploy + port-forward:

```powershell
# 1. Kiểm tra Minikube
minikube status

# 2. Port-forward PostgreSQL (chạy trong terminal riêng, để chạy nền)
kubectl port-forward svc/postgres-postgresql 5432:5432 -n default

# 3. Chạy Dataset Builder (terminal khác)
python ml/scripts/run_dataset_builder.py --ticker AAPL -o ml/outputs/datasets

# Naive + ARIMA từ dataset đã build
python ml/scripts/run_naive_baselines.py -d ml/outputs/datasets -s AAPL
python ml/scripts/train_arima.py -d ml/outputs/datasets -s AAPL
```

**Nếu không có DB:** Bỏ `--ticker` để dùng sample data:
```powershell
python ml/scripts/run_dataset_builder.py
```

### 5. Kiểm tra Airflow DAG (5.3)

```bash
cd ml
docker compose -f docker-compose-airflow-local.yaml up -d
# Mở http://localhost:8080 → trigger DAG "test_mlflow"
```

---

## Cài đặt dependencies (nếu chưa có)

```bash
pip install -r ml/requirements.txt
# PyTorch CUDA (optional, cho LSTM sau):
# pip install torch --index-url https://download.pytorch.org/whl/cu121
```
