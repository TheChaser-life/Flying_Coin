# 📊 Market Data Mining & Forecasting System (MDMFS)

Hệ thống thu thập, phân tích và dự báo dữ liệu thị trường tài chính — bao gồm chứng khoán, tiền điện tử và hàng hóa — sử dụng Machine Learning, NLP, và Portfolio Optimization.

> 💡 **Kiến trúc Hiện Tại (V2 - Local First):** Dự án đang được triển khai theo hướng tiếp cận tối ưu chi phí (Local-First). Hạ tầng được build và test hoàn toàn trên **Minikube** ở Phase 1 & 2 trước khi tự động deploy lên **GCP (GKE)** bắt đầu từ Phase 3 thông qua **Terraform** và **Kustomize**.

---

## 🎯 Tiến Độ & Trạng Thái Hiện Tại

- **Phase 1 (Hạ tầng Local & Services Nền tảng):** *Đang thực hiện (Tuần 2)*
  - ✅ Viết thành công Terraform modules cho GCP (Networking, K8s, Storage, RDS, Secret).
  - ✅ Khởi chạy thành công PostgreSQL, Redis, RabbitMQ qua Helm chart trên Minikube.
  - ✅ Hoàn thành Database Schema (SQLAlchemy) và Data Validation (Pydantic).
  - 🔄 Đang cấu hình Local Docker Registry và chuẩn bị kịch bản Database Migration (Alembic).

---

## 📚 Hệ Thống Tài Liệu

| # | Tài liệu | Mô tả |
|---|----------|-------|
| 1 | [Tổng Quan Dự Án](docs/01_project_overview.md) | Mục tiêu, đối tượng, phạm vi, disclaimer |
| 2 | [Kiến Trúc Hệ Thống](docs/02_system_architecture.md) | Microservices architecture, modules, database, giao tiếp |
| 3 | [Tính Năng Người Dùng & Giao Diện](docs/03_user_features.md) | Tính năng chính, user journey, mô tả UI/UX |
| 4 | [Kế Hoạch Phát Triển V2](docs/04_development_roadmap_v2.md) | **[Cập nhật mới]** 5 phases, ~17 tuần, focus vào Local-First |
| 5 | [Kế Hoạch Phát Triển V1](docs/04_development_roadmap.md) | Tham khảo kế hoạch GKE Cloud-First (cũ) |
| 6 | [Tech Stack](docs/05_tech_stack.md) | Backend, Frontend, Infrastructure, External APIs |
| 7 | [Cấu Trúc Thư Mục](docs/06_project_structure.md) | Sơ đồ sắp xếp mã nguồn, cấu hình và tài liệu |
| 8 | [API Endpoints](docs/07_api_endpoints.md) | REST APIs + WebSocket events cho tất cả services |
| 9 | [Yêu Cầu Phi Chức Năng](docs/08_non_functional_requirements.md) | Performance, security, testing strategies |
| 10 | [Rủi Ro & Giải Pháp](docs/09_risks_and_solutions.md) | Dự tính các bottleneck hệ thống và giải pháp |
| 11 | [Định Hướng Mở Rộng](docs/10_expansion_direction.md) | Thiết kế system-extendable, mở rộng scale trong tương lai |
| 12 | [Thuật Ngữ Tài Chính](docs/11_financial_glossary.md) | Bảng thuật ngữ chuyên ngành (Finance & Trading) |
| 13 | [Prerequisites](docs/12_prerequisites.md) | Các tools, dependencies cần cài đặt trên máy Local |

---

## 🏗️ Kiến Trúc Tổng Quan

```text
Client (React/Next.js)
    │
    ├── HTTP ──► API Gateway ──► Auth / Market Data / Forecast / Sentiment / Portfolio
    │
    └── WS ───► WebSocket Service ◄──── Redis Pub/Sub ◄──── All Services
```

**8 Microservices:** Auth, Market Data, Forecast, Sentiment, Portfolio, API Gateway, WebSocket (Go), Notification (Go).

## ⚙️ Tech Stack Chính

- **Backend:** Python (FastAPI, SQLAlchemy, Celery/RabbitMQ) + Go (WebSocket/Notification)
- **ML/AI:** XGBoost (GPU), LSTM (PyTorch CUDA), ARIMA, FinBERT (NLP)
- **Frontend:** React/Next.js, TradingView Charts, Tailwind CSS
- **Database & Queue:** PostgreSQL + TimescaleDB, Redis, RabbitMQ
- **Infra/DevOps:** Docker, Minikube, Kubernetes (GKE), Terraform, Kustomize, GitHub Actions
- **MLOps:** MLflow, Apache Airflow (Docker Compose-based local training)

## 📅 Timeline Tổng Thể (Local-First)

**~17 tuần (4 tháng)**, chia thành 5 phases nhằm tiết kiệm >70% chi phí Cloud:
1. **Phase 1:** Hạ tầng Local (Minikube) & Services Nền tảng
2. **Phase 2:** ML Models, MLOps, Sentiment Analysis (Train Local trên thiết bị vật lý sử dụng GPU RTX 4060)
3. **Phase 3:** Migrate lên GKE Cloud, Portfolio Service, WS & Observability
4. **Phase 4:** Frontend Dashboard, DevSecOps
5. **Phase 5:** Production Hardening & Go-Live

---

> ⚠️ **Disclaimer:** Dự án phục vụ mục đích nghiên cứu, học tập phát triển hệ thống Cloud-native Microservices và MLOps. Kết quả dự báo ML không phải lời khuyên đầu tư tài chính.
