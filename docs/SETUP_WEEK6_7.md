# Setup Tuần 6-7 — XGBoost, LSTM & MLOps

## Đã có ✅

| Thành phần | Trạng thái |
|------------|------------|
| MLflow (Docker Compose) | ✅ `ml/docker-compose-mlflow-local.yaml` |
| Airflow (Docker Compose) | ✅ `ml/docker-compose-airflow-local.yaml` |
| Feature Engineering (5.6) | ✅ `ml/pipelines/feature_engineering.py` |
| Dataset Builder (5.5) | ✅ `ml/pipelines/dataset_builder.py` |
| Pre-built datasets | ✅ `ml/outputs/datasets/*.parquet` |
| MLflow tracking URI trong Airflow | ✅ `MLFLOW_TRACKING_URI: http://mlflow:5000` |

---

## Cần setup thêm

### 1. Chạy Airflow + MLflow cùng lúc (bắt buộc)

Dùng **một file compose** `docker-compose-mlops-local.yaml` (Airflow + MLflow + DBs):

```bash
cd ml
docker compose -f docker-compose-mlops-local.yaml up -d
```

**Kiểm tra:** Vào Airflow UI → trigger DAG `test_mlflow` → task gọi MLflow phải thành công.

---

### 2. Nguồn dữ liệu cho Training DAG ✅ Đã chọn: **Cách A**

**Vấn đề:** Khi `minikube stop` (để train), PostgreSQL chứa `market_data` sẽ tắt. DAG không thể fetch trực tiếp từ DB.

**Giải pháp (chọn 1):**

| Cách | Mô tả | Khi nào dùng |
|------|-------|--------------|
| **A. Dùng dataset có sẵn** ✅ | DAG đọc từ `ml/outputs/datasets/*.parquet` (đã export trước) | Đơn giản, phù hợp dev |
| **B. Export trước khi train** | Chạy script export khi Minikube còn bật → lưu parquet → `minikube stop` → train | Cần data mới nhất |
| **C. Thêm PostgreSQL vào compose** | Thêm postgres + market-data-service vào compose training | Nặng, phức tạp |

**Đã cấu hình:** Volume `./outputs` đã mount trong `docker-compose-mlops-local.yaml`. DAG đọc parquet từ `/opt/airflow/outputs/datasets/` (trong container) hoặc `ml/outputs/datasets/` (khi chạy script trên host).

---

### 3. GPU cho XGBoost & LSTM (RTX 4060) ✅ Đã chọn: **Cách B**

**Vấn đề:** Airflow chạy trong Docker. Task training chạy **trong container** — mặc định không thấy GPU.

**Giải pháp (chọn 1):**

| Cách | Mô tả | Độ phức tạp |
|------|-------|--------------|
| **A. NVIDIA Container Toolkit** | Cài nvidia-docker, thêm `deploy.resources.reservations.devices: nvidia.com/gpu` vào airflow-scheduler | Trung bình |
| **B. Chạy training ngoài container** ✅ | DAG dùng `BashOperator` gọi script trên host (Python venv có PyTorch CUDA) | Đơn giản hơn |
| **C. DockerOperator + custom image** | Build image có CUDA + xgboost + torch, chạy task trong container riêng có GPU | Cao |

**Đã cấu hình:** DAG gọi **Trigger Server** chạy trên host qua `http://host.docker.internal:8765`. Trigger server chạy `python ml/scripts/train_xgboost.py` (hoặc `train_lstm.py`) trong venv của host — dùng được RTX 4060 GPU.

**Cách chạy Trigger Server (trên host):**
```bash
cd <project_root>
.venv\Scripts\activate   # Windows
python ml/scripts/trigger_server.py
```

---

### 4. Python dependencies trong Airflow

Hiện tại scheduler chỉ có `pip install mlflow boto3`. Để chạy XGBoost/LSTM **trong container** (nếu dùng Cách A hoặc C), cần thêm:

- `xgboost`
- `torch` (và torchvision, torchaudio — bản CUDA nếu dùng GPU trong container)
- `pandas`, `scikit-learn`, `pyarrow`, `statsmodels`

**Nếu dùng Cách B (train trên host):** Không cần — Airflow chỉ orchestrate, script chạy ngoài.

---

### 5. Forecast Service (6.6) — Load model từ MLflow

**Vấn đề:** Khi deploy Forecast Service lên Minikube, workflow là `docker compose down` (tắt Airflow + MLflow) → `minikube start`. MLflow không chạy nữa.

**Giải pháp:**

- **Model artifact** lưu tại `ml/mlruns/` (volume local). Forecast Service cần **đường dẫn artifact** hoặc **model file**.
- **Cách 1:** Forecast Service đọc `MLFLOW_TRACKING_URI` + `model_uri` — cần MLflow chạy khi serve. Có thể chạy `mlflow server` riêng (không qua compose) khi cần.
- **Cách 2:** Copy model artifact vào PVC/image khi deploy — Forecast Service load từ file, không cần MLflow server.

---

## Checklist trước khi bắt đầu Tuần 6-7

- [ ] Chạy `docker compose -f docker-compose-mlops-local.yaml up -d` và verify Airflow → MLflow
- [x] Mount `./outputs` vào Airflow (Cách A — đã có trong compose)
- [x] Quyết định: **Cách B** — train trên host (BashOperator → Trigger Server)
- [ ] Chạy Trigger Server trên host: `python ml/scripts/trigger_server.py` (port 8765)
- [ ] Đảm bảo venv host có `xgboost`, `torch` (CUDA), `mlflow`, `pandas`, v.v.

---

## Lệnh chạy nhanh (gợi ý)

```bash
# 1. Bật Airflow + MLflow
cd ml
docker compose -f docker-compose-mlops-local.yaml up -d

# 2. Kiểm tra
curl http://localhost:5000/health   # MLflow
# Mở http://localhost:8080         # Airflow (admin/admin)

# 3. Chạy Trigger Server (terminal riêng, trên host — cho Cách B)
cd <project_root>
.venv\Scripts\activate
python ml/scripts/trigger_server.py

# 4. Khi train (minikube stop trước)
minikube stop
# Trigger DAG "training_pipeline" trong Airflow UI
```
