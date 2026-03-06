# 🛠️ Tài Nguyên Cần Chuẩn Bị (Prerequisites)

## 1. Phần cứng tối thiểu

| Thành phần | Yêu cầu | Hiện có |
|-----------|---------|--------|
| **CPU** | 4 cores trở lên | ✅ |
| **RAM** | 16 GB | ✅ 16 GB |
| **GPU** | NVIDIA (CUDA support), 4GB+ VRAM | ✅ RTX 4060 (8GB VRAM) |
| **Ổ cứng trống** | ~50 GB (SSD khuyến nghị) | — |
| **Internet** | Ổn định (download Docker images, API thu thập dữ liệu) | — |

---

## 2. Phần mềm cần cài đặt

### Phase 1 — Hạ tầng & K8s (Bắt buộc)

| # | Tool | Lệnh cài | Dung lượng | Vai trò |
|---|------|---------|-----------|--------|
| 1 | **Docker Desktop** | `winget install Docker.DockerDesktop` | ~3-4 GB | Runtime cho Minikube, build Docker images |
| 2 | **Minikube** | `winget install Kubernetes.minikube` | ~100 MB | K8s cluster trên máy local |
| 3 | **kubectl** | `winget install Kubernetes.kubectl` | ~50 MB | Điều khiển K8s (Kustomize tích hợp sẵn) |
| 4 | **Helm** | `winget install Helm.Helm` | ~50 MB | Cài PostgreSQL, Redis, Prometheus bằng Helm charts |
| 5 | **Terraform** | `winget install Hashicorp.Terraform` | ~100 MB | Viết IaC modules (apply khi lên cloud Phase 3) |
| 6 | **Git** | `winget install Git.Git` | ~300 MB | Version control |

### Phase 2 — ML Training (Cài trước khi train models)

| # | Tool | Lệnh cài | Dung lượng | Vai trò |
|---|------|---------|-----------|--------|
| 7 | **Python 3.11+** | `winget install Python.Python.3.11` | ~200 MB | Training scripts, backend services |
| 8 | **CUDA Toolkit 12.x** | [nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads) | ~3-4 GB | RTX 4060 GPU support cho PyTorch |
| 9 | **PyTorch (CUDA)** | `pip install torch --index-url https://download.pytorch.org/whl/cu121` | ~3-4 GB | LSTM, FinBERT training trên GPU |
| 10 | **Apache Airflow** | Docker Compose (`docker-compose-airflow.yml`) | ~500 MB | ML pipeline orchestration (bật/tắt on-demand) |

### Phase 3 — Cloud Migration (Cài khi chuyển sang GKE)

| # | Tool | Lệnh cài | Dung lượng | Vai trò |
|---|------|---------|-----------|--------|
| 10 | **gcloud CLI** | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) | ~500 MB | Kết nối GCP, quản lý GKE cluster |

---

## 3. Tài khoản cần đăng ký

| # | Dịch vụ | Link | Mục đích | Chi phí |
|---|---------|------|----------|---------|
| 1 | **GitHub** | [github.com](https://github.com) | Source code, CI/CD (GitHub Actions) | Miễn phí |
| 2 | **Google Cloud (GCP)** | [cloud.google.com](https://cloud.google.com) | GKE, Cloud SQL, GCS (Phase 3+) | ~$50-80/tháng (có $300 free credit mới) |
| 3 | **Cloudflare** | [cloudflare.com](https://cloudflare.com) | DNS, SSL/TLS, WAF | Miễn phí (Free plan) |
| 4 | **Docker Hub** | [hub.docker.com](https://hub.docker.com) | Pull public images | Miễn phí |

### API Keys cần đăng ký

| # | API | Link | Mục đích | Chi phí |
|---|-----|------|----------|---------|
| 5 | **Yahoo Finance** (yfinance) | Không cần key | Dữ liệu chứng khoán | Miễn phí |
| 6 | **Binance API** | [binance.com/en/my/settings/api-management](https://www.binance.com/en/my/settings/api-management) | Dữ liệu crypto real-time | Miễn phí |
| 7 | **NewsAPI** | [newsapi.org](https://newsapi.org) | Thu thập tin tức tài chính | Miễn phí (100 requests/ngày) |
| 8 | **Domain name** (tùy chọn) | Namecheap, Cloudflare, etc. | Tên miền cho production | ~$10-15/năm |

---

## 4. Dung lượng ổ cứng chi tiết

### Phần cài đặt (~15 GB)

| Thành phần | Dung lượng |
|-----------|-----------|
| Docker Desktop + WSL2 | ~4 GB |
| Minikube + K8s images | ~2 GB |
| kubectl, Helm, Terraform, gcloud | ~700 MB |
| Python + CUDA + PyTorch | ~8 GB |

### Docker Images (~7 GB)

| Image | Dung lượng |
|-------|-----------|
| PostgreSQL + TimescaleDB | ~400 MB |
| Redis 7 | ~130 MB |
| RabbitMQ 3.13 | ~200 MB |
| MLflow | ~500 MB |
| Python services (Auth, Market, Forecast, Sentiment) | ~3-5 GB |
| Go services (WebSocket, Notification) | ~50 MB |
| Airflow (webserver + scheduler + metadata DB) | ~1 GB |
| Frontend (Next.js) | ~500 MB |

### Dữ liệu (~8 GB)

| Loại | Dung lượng |
|------|-----------|
| PostgreSQL data (market data 6 tháng) | ~2-3 GB |
| ML models (ARIMA + XGBoost + LSTM) | ~500 MB |
| FinBERT model weights | ~1.3 GB |
| MLflow experiment logs | ~500 MB |
| Docker build cache | ~3-5 GB |

| | Tổng |
|---|------|
| **Cài đặt + Images + Data** | **~30 GB** |
| **Khuyến nghị dành riêng** | **~50 GB** |

---

## 5. Chi phí tổng dự án (4 tháng)

| Hạng mục | Chi phí |
|---------|---------|
| Phase 1-2: Minikube local | **$0** |
| Phase 3-5: GKE Cloud (~2.5 tháng, bật/tắt) | ~$100-180 |
| Domain name (tùy chọn) | ~$10-15 |
| GCP Free Credit (tài khoản mới) | **-$300** |
| | |
| **Tổng ước tính** | **~$0-200 (~0-5 triệu VNĐ)** |

> [!TIP]
> Nếu tài khoản GCP mới, bạn được **$300 free credit** trong 90 ngày — đủ cho toàn bộ Phase 3-5. Tổng chi phí thực tế có thể = **$0**.
