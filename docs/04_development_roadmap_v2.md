# 📅 Kế Hoạch Phát Triển V2 — Local-First (Development Roadmap V2)

## Tổng quan

**Tổng thời gian: ~17 tuần (4 tháng) | Chi phí ước tính: ~3-5 triệu VNĐ**

> [!IMPORTANT]
> **Chiến lược Local-First:**
> - **Phase 1-2 (tuần 1-8):** K8s chạy trên **Minikube local** → chi phí = **$0**
> - **Phase 3 (tuần 9):** Migrate lên **GCP GKE** → chi phí = **~$50-80/tháng**
> - **Phase 4-5 (tuần 12-17):** GKE + Terraform bật/tắt → chi phí = **~$40-60/tháng**
>
> **ML Training Strategy:** Train models **local bằng Python + RTX 4060 GPU** (ngoài K8s) → log MLflow → deploy model lên K8s chỉ để **serving/inference**
>
> **Mô hình làm việc:**
> - 👤 **Bạn (DevOps/MLOps):** Hạ tầng, CI/CD, K8s, Monitoring, Deployment
> - 🤖 **AI (Dev Team):** Code services, ML models, Frontend

| Phase | Tên | Thời gian | Hạ tầng | Chi phí |
|-------|-----|-----------|---------|---------|
| 1 | Hạ tầng Local & Services Nền tảng | 4 tuần | **Minikube** | ~$0 |
| 2 | ML, MLOps & Sentiment | 4 tuần | **Minikube** | ~$0 |
| 3 | Portfolio, WebSocket & Observability | 3 tuần | **GKE Cloud** ☁️ | ~$50-80/tháng |
| 4 | Frontend Dashboard & Security | 4 tuần | GKE + Terraform bật/tắt | ~$40-60/tháng |
| 5 | Production Hardening & Go-Live | 2 tuần | GKE Production | ~$50-80/tháng |

---

## Prerequisites — Công cụ cần cài đặt

**Máy tính:** Windows, 16GB RAM, RTX 4060 GPU

### Phase 1 (bắt buộc)

| # | Tool | Lệnh cài | Vai trò |
|---|------|---------|--------|
| 1 | **Docker Desktop** | `winget install Docker.DockerDesktop` | Runtime cho Minikube |
| 2 | **Minikube** | `winget install Kubernetes.minikube` | K8s cluster local |
| 3 | **kubectl** | `winget install Kubernetes.kubectl` | Điều khiển K8s (Kustomize tích hợp sẵn) |
| 4 | **Helm** | `winget install Helm.Helm` | Cài PostgreSQL, Redis, RabbitMQ, Prometheus |
| 5 | **Terraform** | `winget install Hashicorp.Terraform` | Viết IaC modules (apply ở Phase 3) |
| 6 | **Git** | `winget install Git.Git` | Version control |

### Phase 2 (thêm cho ML Training)

| # | Tool | Cài bằng | Vai trò |
|---|------|---------|--------|
| 7 | **Python 3.11+** | `winget install Python.Python.3.11` | Training scripts |
| 8 | **CUDA Toolkit 12.x** | [nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads) | RTX 4060 GPU support |
| 9 | **PyTorch (CUDA)** | `pip install torch --index-url https://download.pytorch.org/whl/cu121` | LSTM, FinBERT |
| 10 | **Apache Airflow** | Docker Compose (xem chi tiết bên dưới) | ML pipeline orchestration |

### Phase 3 (thêm khi migrate lên cloud)

| # | Tool | Lệnh cài | Vai trò |
|---|------|---------|--------|
| 10 | **gcloud CLI** | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) | Kết nối GCP GKE |

---

## Phase 1: Hạ tầng Local & Services Nền tảng — 4 tuần

**Hạ tầng: 🖥️ Minikube trên Windows (Docker Desktop driver) | Chi phí: ~$0**

**Mục tiêu:** Setup K8s local, CI/CD pipeline, và các services nền tảng chạy trên máy cá nhân. Viết Terraform modules (chưa apply) để sẵn sàng lên cloud.

### Tuần 1 — Setup Kubernetes & IaC Nền tảng (Tiến độ thực tế)

| # | Task | Người | Tình trạng | Chi tiết |
|---|------|-------|-----------|----------|
| 1.1 | Git Repository setup | 👤 Bạn | ✅ Done | Tạo repo, branch strategy (main/develop/feature), protection rules |
| 1.2 | **Cài Docker Desktop + K8s Local** | 👤 Bạn | ✅ Done | Cài Minikube hoặc Kind, bật các addon `ingress`, `metrics-server` |
| 1.3 | **Local Docker Registry** | 👤 Bạn | ⬜ Todo | Tích hợp registry vào local cluster |
| 1.4 | **Cấu hình Helm charts** | 👤 Bạn | ✅ Done | Viết `*-local.yaml` và `*-gcp.yaml` cho **PostgreSQL**, **Redis**, **RabbitMQ**. Đã setup cơ chế chia Node Pool (`database-pool`) và Resource Limits cho Cloud. |
| 1.5 | **Quản lý Bảo mật (SecOps)** | 👤 Bạn | ✅ Done | Kịch bản tạo Secret tự động trên GCP (Auth gốc) và config `ExternalSecret` đồng bộ với Secret Manager vào K8s. |
| 1.6 | **Viết Terraform modules** | 👤 Bạn | ✅ Done | Viết hoàn chỉnh `networking`, `kubernetes`, `secrets`, `storage`, `registry` modules (GKE, VPC, Workload Identity, Service Accounts, Buckets, Artifact Registry). |
| 1.7 | **Thiết lập K8s Namespaces** | 👤 Bạn | ✅ Done | Tích hợp tạo namespaces đa tầng (`dev`, `staging`, `production`, `database`, `mlops`...) trực tiếp qua Terraform. |
| 1.8 | Khởi chạy DB & MQ (local) | 👤 Bạn | ✅ Done | Apply `helm install` 3 dịch vụ stateful (DB/MQ/Cache) vào local phục vụ dev. |
| 1.9 | Database Schema design | 🤖 AI | ✅ Done | Thiết kế bảng: `users`, `market_data`, `symbols`, `predictions`, etc. |
| 1.10 | Shared schemas & utilities | 🤖 AI | ✅ Done | Pydantic schemas, common utils, constants |

> **Chi tiết các thành phần hạ tầng cốt lõi đã hoàn thiện (Terraform & Helm):**
>
> | Lớp ứng dụng | Tài nguyên / Cấu hình | Vai trò | Tình trạng |
> |--------|---------------|---------|---------|
> | **Infrastructure (GCP)** | **networking:** VPC, Subnet, NAT, Firewall | Nền tảng mạng cho GKE | ✅ Đã code Terraform |
> | | **kubernetes:** GKE Cluster, Node pools | Cluster K8s chính trên cloud | ✅ Đã code Terraform |
> | | Kích hoạt **Workload Identity** | Cơ chế bảo mật an toàn, phi tập trung | ✅ Đã cấu hình |
> | | Lập trình **Namespaces & SA** | Không gian riêng biệt (database, dev...) | ✅ Đã cấu hình |
> | | **storage:** Cloud Storage Bucket | Lưu trữ ML Model Artifacts (MLflow) | ✅ Đã code Terraform |
> | | **registry:** Artifact Registry, IAM | Lưu Docker Image + quyền pull cho GKE | ✅ Đã code Terraform |
> | **Data Storage / Bus** | **PostgreSQL** (`-local` & `-gcp`) | Cơ sở dữ liệu quan hệ lõi | ✅ Đã viết values |
> | | **Redis** (`-local` & `-gcp`) | Caching & In-memory store | ✅ Đã viết values |
> | | **RabbitMQ** (`-local` & `-gcp`) | Message Broker (3 nodes HA) | ✅ Đã viết values |
> | **Secret Management** | **secrets:** GCP Secret Manager, IAM | Tạo & cấp quyền rỗng giữ credentials gốc | ✅ Đã code Terraform |
> | | **Bash Scripts** cho GCP Secret Manager | Tạo tự động nguồn lưu trữ credentials | ✅ Đã viết script |
> | | **External Secrets Operator** (ESO) | Fetch secret động về tài nguyên K8s | ✅ Đã cấu hình |

> **Các Module/Tài nguyên GCP chưa viết (Dành cho Phase 3):**
> - **K8s StorageClass / PV:** Tạo Storage Class trên cloud phục vụ lưu trữ lâu dài.

### Tuần 2 — K8s Configs, Database Migration & CI/CD Templates

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 2.1 | **Local Docker Registry** | 👤 Bạn | ✅ Done | Hoàn thành task 1.3: Enable registry addon trên Minikube |
| 2.2 | **Alembic migrations** | 🤖 AI | ✅ Done | Setup Alembic, kết nối PostgreSQL local và tạo migration rải bảng |
| 2.3 | **CI/CD Pipeline (Templates)** | 👤 Bạn | ✅ Done | Tạo sẵn khung `.github/workflows/`, chuẩn bị pipeline chờ gắn code tuần 3 |
| 2.4 | **Kustomize directories** | 👤 Bạn | ✅ Done | Đã khởi tạo khung cấu trúc thư mục rỗng `base/` và `overlays/` (`local/`, `dev/`) |

### Tuần 3 — IAM (Keycloak) & API Gateway

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 3.1 | **Cài đặt Keycloak (Helm)** | 👤 Bạn | 1.8 | ✅ Đã deploy Keycloak lên Minikube |
| 3.2 | **Cấu hình Keycloak Admin** | 👤 Bạn | 3.1 | ✅ Đã tạo Realm, Client, Roles, Users test |
| 3.3 | **Cài đặt Kong Gateway (Helm)** | 👤 Bạn | 1.8 | ✅ Đã deploy Kong Ingress Controller bằng Helm |
| 3.4 | **Cấu hình Kong Routes & Plugins** | 🤖 AI | 3.3 | ✅ Đã cấu hình `ingress.yaml` và `kong-plugins.yaml` |
| 3.5 | **Tích hợp Auth (Kong + Keycloak)** | 🤖 AI | 3.2, 3.4 | ✅ KongConsumer + RS256 public key từ Keycloak. Kong JWT plugin verify qua `iss` claim + `rsa_public_key`. Strip-path `/api/v1` trước khi forward backend |
| 3.6 | **Test IAM & Gateway flow** | 👤 Bạn | 3.5 | ✅ No token→401, Valid token→200 (rate-limit+CORS headers OK), Fake token→401 |

### Tuần 4 — Market Data Service

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 4.1 | **Market Data Collectors** | 🤖 AI | 1.6 | ✅ Done — Python scripts: Yahoo Finance + Binance → RabbitMQ queues |
| 4.2 | **Market Data Service** | 🤖 AI | 1.4, 1.6 | ✅ Done — Consume RabbitMQ → xử lý → lưu PostgreSQL → publish Redis |
| 4.3 | **Data Pipeline + API** | 🤖 AI | 4.2 | ✅ Done — Làm sạch dữ liệu, API endpoints đọc dữ liệu lịch sử |
| 4.4 | **Dockerfiles (Collectors + Market Data)** | 🤖 AI | 4.1, 4.2 | ✅ Done — Multi-stage build cho Collectors + Market Data Service |
| 4.5 | **Deploy Market Data trên Cloud** | 👤 Bạn | 4.1, 4.2, 4.3, 4.4 | ✅ Done — Deploy GKE dev-gcp, fix DB schema auto-init, Redis auth |
| 4.6 | **Verify full pipeline** | 👤 Bạn | 4.5 | ✅ Done — Binance → RabbitMQ → market-data-service → PostgreSQL → Redis → API `/symbols`, `/latest`, `/history` |

**✅ Deliverable Phase 1: 100% Completed**

- [ ] 👤 Minikube cluster chạy tất cả services locally
- [ ] 👤 CI/CD pipeline hoạt động (build → push → deploy local)
- [ ] 👤 Kustomize: `overlays/local/` đang dùng + `overlays/dev/` sẵn sàng cho cloud
- [ ] 👤 Terraform modules viết xong nhưng **chưa apply** (tiết kiệm $0)
- [ ] 👤 Keycloak (IAM) chạy ổn định
- [ ] 🤖 API Gateway + Market Data Service hoạt động (đã tích hợp Keycloak)
- [ ] 🤖 Thu thập & lưu trữ dữ liệu chứng khoán + crypto

---

## Phase 2: ML, MLOps & Sentiment — 4 tuần

**Hạ tầng: 🖥️ Minikube Local | Chi phí: ~$0**

**Mục tiêu:** 3 mô hình ML hoạt động, MLOps pipeline, Sentiment Analysis.

> [!TIP]
> **ML Training Strategy — Airflow + Docker Compose (On-Demand):**
>
> ```
> ┌─────────────────────────────────────────────────────────┐
> │  LOCAL — Chế độ TRAINING (bật khi cần train)           │
> │                                                         │
> │  1. minikube stop (giải phóng ~8GB RAM)                │
> │  2. docker compose up airflow (Airflow ~2-3GB RAM)     │
> │  3. Airflow DAG orchestrate:                           │
> │     fetch data → features → train models → log MLflow  │
> │     • Train ARIMA, XGBoost (GPU), LSTM (GPU)           │
> │     • Dùng toàn bộ RAM còn lại + 8GB VRAM              │
> │  4. Xong → docker compose down airflow                 │
> │  5. minikube start (khôi phục services)                │
> └────────────────────────┬────────────────────────────────┘
>                          │ Register model → MLflow
>                          ▼
> ┌─────────────────────────────────────────────────────────┐
> │  MINIKUBE — Chế độ SERVING (chạy 24/7)                 │
> │                                                         │
> │  Forecast Service: load model (~200-500MB) → inference │
> │  Sentiment Service: load FinBERT → inference            │
> │  → Nhẹ, không cần GPU, chạy thoải mái trên Minikube   │
> └─────────────────────────────────────────────────────────┘
> ```
>
> **Chiến lược tiết kiệm RAM:**
> - Airflow chạy qua **Docker Compose** (ngoài Minikube), **chỉ bật khi train**
> - Khi train: `minikube stop` → giải phóng ~8GB → Airflow + training dùng toàn bộ RAM
> - Khi xong: `docker compose down` → `minikube start` → serving bình thường
> - Trên cloud (Phase 3+): Airflow chạy trên GKE 24/7, không cần bật/tắt

### Tuần 5 — Feature Engineering, MLflow & Airflow

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 5.1 | ~~**MLflow server trên Minikube**~~ ✅ | 👤 Bạn | Phase 1 | Deploy MLflow pod, backend = PostgreSQL local, artifacts = MinIO (S3-compatible, local PVC) |
| 5.2 | ~~**Training environment setup**~~ ✅ | 👤 Bạn | — | Python venv + PyTorch CUDA + MLflow client → kết nối MLflow trên Minikube (`minikube service mlflow --url`) |
| 5.3 | ~~**Airflow setup (Docker Compose)**~~ ✅ | 👤 Bạn | 5.1 | Viết `docker-compose-airflow-local.yaml` (webserver + scheduler + PostgreSQL metadata), kết nối MLflow, test DAG đơn giản |
| 5.4 | **Data Preprocessing pipeline** | 🤖 AI | Phase 1 | ✅ Done — EDA (phân phối, tương quan), xử lý missing values, outlier detection, normalization/scaling, time-series train/val/test split |
| 5.5 | **Dataset Builder** | 🤖 AI | 5.4 | ✅ Done — JOIN market_data + technical_indicators + sentiment_scores → training dataset (parquet/csv), feature_engineering.py (SMA, EMA, RSI, MACD, Bollinger Bands) |
| 5.6 | **Feature Engineering pipeline** | 🤖 AI | 5.5 | ✅ Done — SMA/EMA(7,14,21,50,200), RSI, MACD, Bollinger Bands, Stochastic, ATR, OBV, VWAP, ADX → lưu dataset |
| 5.7 | **Naive Baselines** | 🤖 AI | 5.5 | ✅ Done — Naive + MA(7) forecast, RMSE/MAE/DA/MAPE → log MLflow benchmark |
| 5.8 | **ARIMA baseline model** | 🤖 AI | 5.6, 5.7 | ✅ Done — train_arima.py: fit ARIMA(p,d,q), evaluate, log MLflow, so sánh naive |

### Tuần 6-7 — XGBoost, LSTM & MLOps

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 6.3 | **Airflow Training DAG** | 🤖 AI | 5.3 | ✅ Done — DAG: check_datasets → trigger arima/xgboost/lstm (Trigger Server) |
| 6.4 | **XGBoost model** | 🤖 AI | 5.6 | ✅ Done — train_xgboost.py (GPU `tree_method='gpu_hist'`) → MLflow |
| 6.5 | **LSTM model** | 🤖 AI | 5.6 | ✅ Done — train_lstm.py (PyTorch CUDA) → MLflow |
| 6.6 | **Forecast Service (serving only)** | 🤖 AI | 6.4, 6.5 | ✅ Done — services/forecast-service: load model từ MLflow → POST /forecast/predict |

> [!NOTE]
> **6.1 MLOps CI pipeline** và **6.2 Model Validation Gate** — dời sang **Migration Checkpoint (Tuần 9)** khi triển khai lên cloud.

> [!IMPORTANT]
> **Minikube khi chạy Tuần 6-7:**
> - **6.3, 6.4, 6.5 (training):** Cần `minikube stop` trước → giải phóng ~8GB RAM cho Airflow + XGBoost/LSTM GPU. MLflow cần chạy riêng (Docker Compose hoặc `mlflow server`) vì MLflow trên Minikube sẽ tắt.
> - **6.6 (deploy Forecast Service):** Cần `minikube start` → deploy Forecast Service pod lên K8s.
> - **Workflow:** `minikube stop` → `docker compose up airflow` (+ MLflow nếu chưa có) → train → `docker compose down` → `minikube start` → deploy 6.6.

### Tuần 8 — Sentiment & Deploy ML ✅ completed

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 8.1 | ~~Model Serving pipeline~~ | 👤 Bạn | 6.6 | ✅ Done — CD: pull model từ MLflow Registry → deploy Forecast Service pod (serving mode). *Promote model thủ công trên MLflow UI cho local; 6.2 Validation Gate khi lên cloud* |
| 8.2 | ~~Deploy Forecast trên Minikube~~ | 👤 Bạn | 6.6, 8.1 | ✅ Done — K8s manifests (nhẹ — chỉ inference, không GPU), deploy, verify API |
| 8.3 | **FinBERT inference pipeline** | 🤖 AI | — | ✅ Done — ml/scripts/run_finbert.py, ml/pipelines/finbert_inference.py |
| 8.4 | **News Collectors** | 🤖 AI | 1.6 | ✅ Done — NewsAPI + RSS → news.raw queue |
| 8.5 | **Sentiment Airflow DAG** | 🤖 AI | 8.3, 6.3 | ✅ Done — ml/dags/sentiment_dag.py, fetch_news → run_finbert |
| 8.6 | **Sentiment Service (serving)** | 🤖 AI | 8.3, 8.4 | ✅ Done — services/sentiment-service, news.raw → FinBERT → Redis |
| 8.7 | **Tích hợp Sentiment** | 🤖 AI | 8.6, 5.6 | ✅ Done — Sentiment → Feature Engineering → retrain models (Airflow DAG, local GPU) |
| 8.8 | ~~Deploy Sentiment trên Minikube~~ | 👤 Bạn | 8.6 | ✅ Done — Deploy (CPU-only pod, ~1GB RAM), verify |

> [!NOTE]
> **Workflow training Phase 2 (tiết kiệm RAM):**
> 1. `minikube stop` → giải phóng ~8GB RAM
> 2. `docker compose -f docker-compose-airflow.yml up -d` → bật Airflow (~2-3GB)
> 3. Vào Airflow UI → trigger DAG training → Airflow orchestrate toàn bộ pipeline
> 4. Xem kết quả trên MLflow UI → promote model tốt nhất
> 5. `docker compose down` → tắt Airflow
> 6. `minikube start` → Forecast Service tự load model mới từ MLflow
> 7. Test API inference → ✅ Tiếp tục

**✅ Deliverable Phase 2: 100% Completed**

- [ ] 🤖 3 ML models trained local (ARIMA, XGBoost GPU, LSTM GPU) + registered trên MLflow
- [ ] 🤖 Forecast Service (serving only) + API dự báo 7/14/30 ngày
- [ ] 👤 MLflow tracking; promote model thủ công (local). MLOps CI + Validation Gate khi lên cloud (M.12, M.13)
- [ ] 👤 **Airflow DAGs** orchestrate training pipeline (Docker Compose on-demand)
- [ ] 🤖 FinBERT Sentiment Analysis (GPU local inference + CPU K8s serving)
- [ ] 👤 Tất cả services chạy local, **sẵn sàng migrate lên cloud**

---

## ☁️ MIGRATION CHECKPOINT — Tuần 9 (đầu Phase 3)

> [!CAUTION]
> **Đây là thời điểm chuyển từ Local → Cloud.** Dự kiến mất **3-5 giờ**.

| # | Task | Người | Thời gian | Chi tiết |
|---|------|-------|-----------|----------|
| M.1 | `terraform apply` — GKE Cluster | 👤 Bạn | ✅ Done | Tạo GKE cluster |
| M.2 | **Deploy DB & Cache on GKE** | 👤 Bạn | ✅ Done | Helm: Postgres, Redis, Rabbit. Auto-init DB schema ✅ |
| M.3 | `terraform apply` — GCR/SecretManager | 👤 Bạn | ✅ Done | Infrastructure components |
| M.4 | Migrate data (nếu cần) | 👤 Bạn | 30 phút | Task duy trì |
| M.5 | Đổi kubectl context | 👤 Bạn | ✅ Done | `gcloud container clusters get-credentials` |
| M.6 | `kubectl apply -k overlays/dev-gcp/` | 👤 Bạn | ✅ Done | Deploy Cloud overlays |
| M.7 | **Deploy Airflow trên GKE** | 👤 Bạn | ✅ Done | Helm: Apache Airflow deployed in `mlops` ns |
| M.8 | **Cấu hình Airflow cloud** | 👤 Bạn | ✅ Done | Workload Identity, DAGs (Stage 1 & 2 integration) |
| M.9 | **Setup SSH cho remote training** | 👤 Bạn | ✅ Done | Reverse Tunnel via Bastion (GatewayPorts enabled) |
| M.10 | Verify tất cả services | 👤 Bạn | ✅ Done | Collectors, Sentiment, Market-Data services OK |
| M.11 | Cập nhật CI/CD target | 👤 Bạn | ✅ Done | Deploy → GKE target |
| M.12 | **Cost-Saving & Automation** | 👤 Bạn | ✅ Done | `destroy.sh` + setup integrated with Terraform |

**Sau migration:** Airflow chạy 24/7 trên GKE, orchestrate pipeline tự động. Training vẫn chạy trên máy local (RTX 4060) qua SSH.

---

## Phase 3: Portfolio, WebSocket & Observability — 3 tuần

**Hạ tầng: ☁️ GKE Cloud | Chi phí: ~$50-80/tháng**

**Mục tiêu:** Portfolio, real-time WebSocket, và monitoring stack (cần cloud thật để test metrics/logging chính xác).

### Tuần 9-10 — Portfolio, WebSocket & Monitoring

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 9.1 | ⬆️ **Migration Local → GKE** | 👤 Bạn | Phase 2 | Xem Migration Checkpoint ở trên |
| 9.2 | Prometheus + Grafana | 👤 Bạn | 9.1 | Helm: kube-prometheus-stack trên GKE |
| 9.3 | Service Monitors | 👤 Bạn | 9.2 | Scrape metrics từ mọi service |
| 9.4 | **Portfolio Service** | 🤖 AI | Phase 1 | Markowitz, Efficient Frontier, risk analysis |
| 9.5 | **Backtesting Engine** | 🤖 AI | 9.4 | Backtesting với equity curve |
| 9.6 | **WebSocket Service (Go)** | 🤖 AI | Phase 1 | Gorilla WebSocket + go-redis, fan-out |
| 9.7 | Deploy Portfolio + WS trên GKE | 👤 Bạn | 9.4, 9.6 | K8s manifests, deploy cloud, verify |

### Tuần 11 — Notification, ELK & Logging

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 11.1 | ELK Stack | 👤 Bạn | 9.1 | Helm: elasticsearch + logstash + kibana |
| 11.2 | Health Checks | 👤 Bạn | 9.7 | Readiness & Liveness probes cho tất cả services |
| 11.3 | Grafana ML Dashboard | 👤 Bạn | 9.2 | Dashboard cho ML model metrics |
| 11.4 | **Notification Service (Go)** | 🤖 AI | Phase 1 | Email alerts (Gin + gomail) |
| 11.5 | **Real-time integration** | 🤖 AI | 9.6 | WS channels: price, sentiment, forecast, alerts |
| 11.6 | **Pub/Sub tích hợp** | 🤖 AI | 11.4, 11.5 | Redis Pub/Sub giữa tất cả services |
| 11.7 | Deploy Notification trên GKE | 👤 Bạn | 11.4 | Deploy, verify email alerts |
| 11.8 | **Terraform bật/tắt script** | 👤 Bạn | 9.1 | Script tự động destroy/apply GKE ngoài giờ làm việc |

**✅ Deliverable Phase 3:**

- [ ] 🤖 Portfolio + Backtesting + WebSocket + Notification hoạt động
- [ ] 👤 Toàn bộ hệ thống chạy trên GKE Cloud
- [ ] 👤 Prometheus + Grafana + ELK monitoring/logging
- [ ] 👤 Terraform bật/tắt script tiết kiệm chi phí

---

## Phase 4: Frontend Dashboard & Security — 4 tuần

**Hạ tầng: ☁️ GKE + Terraform bật/tắt | Chi phí: ~$40-60/tháng**

### Tuần 12-13 — Frontend Core

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 12.1 | Trivy scanning | 👤 Bạn | Phase 1 | Container image scanning tích hợp CI |
| 12.2 | Secret Management | 👤 Bạn | Phase 1 | HashiCorp Vault / K8s External Secrets |
| 12.3 | **Next.js setup** | 🤖 AI | — | Project, Shadcn UI, routing, dark mode |
| 12.4 | **Auth integration** | 🤖 AI | 12.3 | Tích hợp NextAuth/Auth.js với Keycloak OIDC |
| 12.5 | **Dashboard tổng quan** | 🤖 AI | 12.3 | Market summary, cards, charts |
| 12.6 | **Analysis page** | 🤖 AI | 12.3 | Candlestick chart (TradingView) |

### Tuần 14-15 — Frontend Advanced & Testing

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 14.1 | SonarQube | 👤 Bạn | Phase 1 | Code quality scanning |
| 14.2 | WAF & TLS | 👤 Bạn | Phase 1 | Cloudflare WAF + cert-manager |
| 14.3 | **Forecast page** | 🤖 AI | 12.3 | AI forecast chart + model comparison |
| 14.4 | **Sentiment page** | 🤖 AI | 12.3 | News Feed, Sentiment gauge, Word Cloud |
| 14.5 | **Portfolio page** | 🤖 AI | 12.3 | Efficient Frontier + Pie charts |
| 14.6 | **Backtesting page** | 🤖 AI | 12.3 | Equity curve, metrics |
| 14.7 | **WebSocket integration** | 🤖 AI | 14.3, 14.4 | Real-time cho tất cả pages |
| 14.8 | **Unit + Integration Tests** | 🤖 AI | All services | pytest + Go tests |
| 14.9 | **E2E Tests** | 🤖 AI | 14.7 | Playwright |
| 14.10 | Deploy Frontend trên GKE | 👤 Bạn | 14.7 | Ingress rules, deploy |

**✅ Deliverable Phase 4:**

- [ ] 🤖 8 trang dashboard + real-time + tests
- [ ] 👤 DevSecOps: Trivy + SonarQube + Vault + WAF

---

## Phase 5: Production Hardening & Go-Live — 2 tuần

**Hạ tầng: ☁️ GKE Production | Chi phí: ~$50-80/tháng**

### Tuần 16 — Deployment Strategies & Alerting

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 16.1 | Blue-Green Deployment | 👤 Bạn | Phase 3 | Traffic switching giữa 2 environments |
| 16.2 | Canary Deployment | 👤 Bạn | 16.1 | Argo Rollouts: 5% → 25% → 50% → 100% |
| 16.3 | Auto-rollback | 👤 Bạn | 16.2 | Prometheus → auto rollback khi error tăng |
| 16.4 | CD Pipeline (Prod) | 👤 Bạn | 16.1 | Production pipeline + approval gates |
| 16.5 | Alerting Rules | 👤 Bạn | 9.2 | CPU, error rate, service down |
| 16.6 | Alert Channels | 👤 Bạn | 16.5 | Slack + Telegram webhooks |
| 16.7 | **API Documentation** | 🤖 AI | All | Swagger/OpenAPI auto-gen |
| 16.8 | **Bug fixes** | 🤖 AI | Phase 4 | Fix issues |

### Tuần 17 — Go-Live

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 17.1 | Auto-scaling (HPA) | 👤 Bạn | Phase 3 | Scale pods khi load tăng |
| 17.2 | FinOps | 👤 Bạn | Phase 3 | Tắt dev/staging cuối tuần, right-size |
| 17.3 | Load Testing | 👤 Bạn | 16.4 | k6/Locust stress test |
| 17.4 | **Runbooks** | 🤖 AI | — | Hướng dẫn xử lý sự cố |
| 17.5 | **User Guide** | 🤖 AI | Phase 4 | Hướng dẫn sử dụng |
| 17.6 | **Production Deploy** | 👤 Bạn | 16.4, 17.3 | Blue-Green/Canary deploy 🚀 |
| 17.7 | Post-deploy Monitor | 👤 Bạn | 17.6 | Theo dõi 48h |

**✅ Deliverable Phase 5:**

- [ ] 👤 Blue-Green/Canary + Alerting + Auto-scaling
- [ ] 🤖 API Docs + Runbooks + User Guide
- [ ] 👤 **System LIVE on Production** 🚀

---

## Tổng kết Chi phí theo Phase

```
Phase 1 (tuần 1-4)     Phase 2 (tuần 5-8)     MIGRATE      Phase 3-5 (tuần 9-17)
─────────────────────   ─────────────────────   ─────────    ──────────────────────
🖥️ Minikube Local       🖥️ Minikube Local       → ☁️ GKE     ☁️ GKE Cloud
💰 $0/tháng              💰 $0-15/tháng          2-4 giờ      💰 $40-80/tháng

Tổng 4 tháng: ~$100-180 (~2.6-4.6 triệu VNĐ)
```

---

## So sánh V1 vs V2

| | V1 (Cloud từ đầu) | V2 (Local-First) ⭐ |
|---|---|---|
| **Chi phí 4 tháng** | ~$456-600 (GCP) | **~$100-180** |
| **VNĐ** | ~12-15 triệu | **~2.6-4.6 triệu** |
| **Tiết kiệm** | — | **~70%** |
| **Rủi ro migration** | Không | Rất thấp (Kustomize overlays) |
| **Học DevOps** | Tốt | **Tuyệt vời** — học thêm local K8s + migration |
| **Thời gian setup** | Chậm hơn (chờ cloud provision) | Nhanh hơn (Minikube tức thì) |

---

## Checklist Tổng Thể

- [x] Thiết kế kiến trúc hệ thống (Microservice)
- [ ] **Phase 1:** 👤 Minikube + CI/CD + Keycloak | 🤖 Gateway + Market Data *(tuần 1-4, $0)*
- [ ] **Phase 2:** 👤 MLOps local | 🤖 3 ML Models + Sentiment *(tuần 5-8, ~$0-15)*
- [ ] ⬆️ **Migration:** Local → GKE Cloud *(~2-4 giờ)*
- [ ] **Phase 3:** 👤 Monitoring + Logging trên cloud | 🤖 Portfolio + WS *(tuần 9-11)*
- [ ] **Phase 4:** 👤 DevSecOps | 🤖 Frontend + Tests *(tuần 12-15)*
- [ ] **Phase 5:** 👤 Deployment Strategies | 🤖 Docs *(tuần 16-17)*
