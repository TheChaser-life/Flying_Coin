# 📅 Kế Hoạch Phát Triển (Development Roadmap) — V1: Cloud-First

## Tổng quan

**Tổng thời gian: ~17 tuần (4 tháng)**

> [!NOTE]
> **Phiên bản này (V1)** sử dụng Cloud từ tuần đầu tiên. Xem **[Roadmap V2 — Local-First](./04_development_roadmap_v2.md)** để tiết kiệm ~70% chi phí bằng cách dùng Minikube local cho Phase 1-2.

> [!IMPORTANT]
> **Mô hình làm việc song song:**
> - 👤 **Bạn (DevOps/MLOps):** Hạ tầng, CI/CD, K8s, Monitoring, Deployment
> - 🤖 **AI (Dev Team):** Code services, ML models, Frontend
>
> Roadmap tuân thủ nguyên tắc: **Hạ tầng → Lưu trữ → Máy chủ → Registry → CI/CD → Ứng dụng → Giám sát**

| Phase | Tên | Thời gian | 👤 Bạn làm | 🤖 AI làm |
|-------|-----|-----------|-----------|----------|
| 1 | Hạ tầng & Services Nền tảng | 4 tuần | IaC, K8s, CI/CD, Registry | Auth, Market Data, DB Schema |
| 2 | ML, MLOps & Sentiment | 4 tuần | MLflow, MLOps Pipeline | 3 ML Models, FinBERT, Sentiment |
| 3 | Portfolio, WebSocket & Observability | 3 tuần | Prometheus, Grafana, ELK | Portfolio, WebSocket (Go), Notification (Go) |
| 4 | Frontend Dashboard & Security | 4 tuần | DevSecOps, Trivy, Vault, WAF | Frontend 8 trang, Tests |
| 5 | Production Hardening & Go-Live | 2 tuần | Blue-Green, Canary, Auto-scaling | API Docs, Bug fixes |

---

## Phase 1: Hạ tầng & Services Nền tảng — 4 tuần

**Mục tiêu:** Hạ tầng Cloud chạy hoàn toàn bằng IaC, CI/CD pipeline hoạt động, các services nền tảng deploy trên K8s.

### Tuần 1 — Nền tảng Mạng & Lưu trữ

**Thứ tự thực hiện:**

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 1.1 | Git Repository setup | 👤 Bạn | — | Tạo repo, branch strategy (main/develop/feature), protection rules |
| 1.2 | VPC & Subnets | 👤 Bạn | — | Terraform: Public Subnet (LB, Ingress) + Private Subnet (DB, Backend) |
| 1.3 | IAM Roles & Policies | 👤 Bạn | 1.2 | Terraform: quyền cho K8s nodes, services, CI/CD |
| 1.4 | Security Groups | 👤 Bạn | 1.2 | Terraform: firewall rules giữa subnets |
| 1.5 | Database Schema design | 🤖 AI | 1.1 | Thiết kế bảng: `users`, `market_data`, `symbols`, `predictions`, etc. |
| 1.6 | Shared schemas & utilities | 🤖 AI | 1.1 | Pydantic schemas, common utils, constants |

### Tuần 2 — Lưu trữ, K8s Cluster & CI/CD

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 2.1 | Object Storage (S3/GCS) | 👤 Bạn | 1.2 | Terraform: buckets cho raw data, ML artifacts, backup |
| 2.2 | Database Cluster | 👤 Bạn | 1.2, 1.3 | Terraform: PostgreSQL + TimescaleDB (RDS/Cloud SQL) |
| 2.3 | RabbitMQ & Redis | 👤 Bạn | 1.2 | Terraform: RabbitMQ (data ingestion) + Redis (cache + Pub/Sub) |
| 2.4 | Kubernetes Cluster | 👤 Bạn | 1.2, 1.3 | Terraform: EKS/GKE cluster, node pools |
| 2.5 | Container Registry | 👤 Bạn | 1.3 | Terraform: ECR/GCR cho Docker Images |
| 2.6 | K8s Namespaces & RBAC | 👤 Bạn | 2.4 | Kustomize: dev/staging/prod namespaces |
| 2.7 | CI Pipeline | 👤 Bạn | 2.5 | GitHub Actions: lint → test → build → push image |
| 2.8 | CD Pipeline (Dev) | 👤 Bạn | 2.4, 2.7 | GitHub Actions: auto-deploy lên dev khi merge |
| 2.9 | Dockerfiles | 🤖 AI | 1.1 | Multi-stage build cho mỗi service (Python + Go) |
| 2.10 | Alembic migrations | 🤖 AI | 1.5, 2.2 | Migration scripts cho database schema |

### Tuần 3 — Auth & API Gateway

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 3.1 | Kustomize overlays | 👤 Bạn | 2.6 | Base manifests + overlays (dev/staging/prod) |
| 3.2 | CD Pipeline (Staging) | 👤 Bạn | 2.8 | Deploy lên staging khi merge vào `main`, manual approval |
| 3.3 | **Auth Service** | 🤖 AI | 1.5 | Đăng ký, đăng nhập, JWT, refresh token, RBAC |
| 3.4 | **API Gateway** | 🤖 AI | — | Kong/Nginx config: routing, rate limiting, CORS |
| 3.5 | Deploy Auth + Gateway | 👤 Bạn | 3.1, 3.3, 3.4 | Viết K8s manifests, deploy lên dev, verify |

### Tuần 4 — Market Data Service

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 4.1 | **Market Data Collectors** | 🤖 AI | 2.3 | Python scripts thu thập Yahoo Finance + Binance → RabbitMQ |
| 4.2 | **Market Data Service** | 🤖 AI | 2.2, 2.3 | Consume RabbitMQ → xử lý → lưu PostgreSQL → publish Redis |
| 4.3 | **Data Pipeline** | 🤖 AI | 4.2 | Làm sạch dữ liệu, API endpoints đọc dữ liệu lịch sử |
| 4.4 | Deploy Market Data | 👤 Bạn | 4.1, 4.2, 4.3 | K8s manifests, deploy, verify data flow |
| 4.5 | Verify toàn bộ pipeline | 👤 Bạn | 4.4 | Test: Collector → RabbitMQ → Service → DB → API → Response |

**✅ Deliverable Phase 1:**

- [ ] 👤 Hạ tầng Cloud tạo bằng Terraform (VPC, DB, K8s, Registry, RabbitMQ, Redis)
- [ ] 👤 CI/CD pipeline hoạt động: push → build → deploy dev
- [ ] 👤 K8s namespaces: dev/staging/prod qua Kustomize
- [ ] 🤖 Auth Service + API Gateway chạy trên K8s
- [ ] 🤖 Market Data Service thu thập & lưu dữ liệu chứng khoán + crypto
- [ ] 🤖 API đọc dữ liệu lịch sử hoạt động

---

## Phase 2: ML, MLOps & Sentiment — 4 tuần

**Mục tiêu:** 3 mô hình ML dự báo hoạt động, MLOps pipeline tự động, Sentiment Analysis qua FinBERT.

### Tuần 5 — Feature Engineering & MLflow

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 5.1 | MLflow server trên K8s | 👤 Bạn | Phase 1 | Deploy MLflow (Helm chart), kết nối PostgreSQL backend |
| 5.2 | ML model storage (S3/GCS) | 👤 Bạn | 2.1 | Cấu hình MLflow artifact store → Object Storage |
| 5.3 | **Feature Engineering** | 🤖 AI | Phase 1 | Pipeline tính Technical Indicators: SMA, EMA, RSI, MACD, Bollinger |
| 5.4 | **ARIMA baseline model** | 🤖 AI | 5.3 | Training, evaluation, MLflow tracking |

### Tuần 6-7 — XGBoost & LSTM

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 6.1 | MLOps CI pipeline | 👤 Bạn | 5.1 | GitHub Actions: trigger train → log MLflow → validate metrics |
| 6.2 | Model Validation Gate | 👤 Bạn | 6.1 | Auto-check RMSE, MAE, Directional Accuracy trước khi promote |
| 6.3 | **XGBoost model** | 🤖 AI | 5.3 | Training, hyperparameter tuning (Optuna), evaluation |
| 6.4 | **LSTM model** | 🤖 AI | 5.3 | Training, evaluation, comparison với XGBoost |
| 6.5 | **Forecast API endpoints** | 🤖 AI | 6.3, 6.4 | API dự báo giá 7/14/30 ngày |

### Tuần 8 — Sentiment & MLOps hoàn thiện

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 8.1 | Model Serving pipeline | 👤 Bạn | 6.2 | CD: auto-deploy model mới từ MLflow Registry lên Forecast Service |
| 8.2 | Deploy Forecast Service | 👤 Bạn | 6.5, 8.1 | K8s manifests, deploy, verify API |
| 8.3 | **FinBERT setup** | 🤖 AI | — | FinBERT inference pipeline cho sentiment analysis |
| 8.4 | **News Collectors** | 🤖 AI | 2.3 | Thu thập tin tức từ NewsAPI & RSS → RabbitMQ |
| 8.5 | **Sentiment Service** | 🤖 AI | 8.3, 8.4 | Consume news → FinBERT → Sentiment Score → publish Redis |
| 8.6 | **Tích hợp Sentiment** | 🤖 AI | 8.5, 5.3 | Sentiment Score → Feature Engineering → improve ML models |
| 8.7 | Deploy Sentiment Service | 👤 Bạn | 8.5 | K8s manifests, deploy, verify |

**✅ Deliverable Phase 2:**

- [ ] 🤖 3 mô hình ML hoạt động (ARIMA, XGBoost, LSTM)
- [ ] 🤖 API dự báo giá 7/14/30 ngày
- [ ] 👤 MLflow tracking experiments + model registry trên K8s
- [ ] 👤 MLOps pipeline: train → validate → register → deploy model
- [ ] 🤖 FinBERT Sentiment Score từ tin tức tài chính
- [ ] 🤖 Sentiment tích hợp vào Feature Engineering

---

## Phase 3: Portfolio, WebSocket & Observability — 3 tuần

**Mục tiêu:** Tối ưu danh mục, real-time updates, và hệ thống giám sát toàn diện.

### Tuần 9-10 — Portfolio & WebSocket

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 9.1 | Prometheus + Grafana | 👤 Bạn | Phase 1 | Helm: kube-prometheus-stack, dashboards cho cluster + services |
| 9.2 | Service Monitors | 👤 Bạn | 9.1 | Cấu hình scrape metrics từ mọi service |
| 9.3 | **Portfolio Service** | 🤖 AI | Phase 1 | Markowitz optimization, Efficient Frontier, risk analysis |
| 9.4 | **Backtesting Engine** | 🤖 AI | 9.3 | Backtesting với equity curve |
| 9.5 | **WebSocket Service (Go)** | 🤖 AI | Phase 1 | Gorilla WebSocket + go-redis subscribe, fan-out messages |
| 9.6 | Deploy Portfolio + WS | 👤 Bạn | 9.3, 9.5 | K8s manifests, deploy, verify real-time |

### Tuần 11 — Notification & Logging

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 11.1 | ELK Stack | 👤 Bạn | Phase 1 | Helm: elasticsearch + logstash + kibana, log pipelines |
| 11.2 | Health Checks | 👤 Bạn | 9.6 | Readiness & Liveness probes cho tất cả deployments |
| 11.3 | Grafana ML Dashboard | 👤 Bạn | 9.1 | Dashboard cho ML model metrics (accuracy, latency, predictions) |
| 11.4 | **Notification Service (Go)** | 🤖 AI | Phase 1 | Email alerts khi trigger điều kiện (Gin + gomail) |
| 11.5 | **Real-time integration** | 🤖 AI | 9.5 | WS channels: price, sentiment, forecast, alerts, market summary |
| 11.6 | **Pub/Sub tích hợp** | 🤖 AI | 11.4, 11.5 | Redis Pub/Sub giữa tất cả services |
| 11.7 | Deploy Notification | 👤 Bạn | 11.4 | K8s manifests, deploy, verify email alerts |

**✅ Deliverable Phase 3:**

- [ ] 🤖 Markowitz portfolio optimization + backtesting
- [ ] 🤖 WebSocket (Go) real-time: price, sentiment, forecast
- [ ] 🤖 Email alerts khi trigger điều kiện
- [ ] 👤 Prometheus + Grafana dashboards (cluster + services + ML)
- [ ] 👤 ELK Stack centralized logging
- [ ] 👤 Health checks cho tất cả services

---

## Phase 4: Frontend Dashboard & Security — 4 tuần

**Mục tiêu:** Dashboard hoàn chỉnh, testing, DevSecOps.

### Tuần 12-13 — Frontend Core

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 12.1 | Trivy scanning | 👤 Bạn | Phase 1 | Tích hợp container image scanning vào CI pipeline |
| 12.2 | Secret Management | 👤 Bạn | Phase 1 | HashiCorp Vault hoặc K8s External Secrets Operator |
| 12.3 | **Next.js setup** | 🤖 AI | — | Project structure, design system (Shadcn), routing, dark mode |
| 12.4 | **Auth pages** | 🤖 AI | 12.3 | Đăng nhập / Đăng ký, JWT integration |
| 12.5 | **Dashboard tổng quan** | 🤖 AI | 12.3 | Tổng quan thị trường, cards, summary charts |
| 12.6 | **Analysis page** | 🤖 AI | 12.3 | Phân tích tài sản + Candlestick chart (TradingView Lightweight) |

### Tuần 14-15 — Frontend Advanced & Testing

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 14.1 | SonarQube | 👤 Bạn | Phase 1 | Code quality scanning tích hợp CI |
| 14.2 | WAF & TLS | 👤 Bạn | Phase 1 | Cloudflare WAF + cert-manager HTTPS |
| 14.3 | **Forecast page** | 🤖 AI | 12.3 | Dự báo AI + forecast chart + model comparison |
| 14.4 | **Sentiment page** | 🤖 AI | 12.3 | News Feed, Sentiment gauge, Word Cloud |
| 14.5 | **Portfolio page** | 🤖 AI | 12.3 | Danh mục + Efficient Frontier + Pie charts |
| 14.6 | **Backtesting page** | 🤖 AI | 12.3 | Equity curve, performance metrics |
| 14.7 | **WebSocket integration** | 🤖 AI | 14.3, 14.4 | Real-time data cho tất cả pages |
| 14.8 | **Unit Tests** | 🤖 AI | All services | pytest cho mỗi Python service, Go tests |
| 14.9 | **Integration Tests** | 🤖 AI | 14.8 | API Gateway → Services → DB flow |
| 14.10 | **E2E Tests** | 🤖 AI | 14.7 | Playwright: Frontend → API → DB |
| 14.11 | Deploy Frontend | 👤 Bạn | 14.7 | K8s manifests, Ingress rules, deploy |

**✅ Deliverable Phase 4:**

- [ ] 🤖 Dashboard 8 trang: Auth, Dashboard, Analysis, Forecast, Sentiment, Portfolio, Backtesting, Settings
- [ ] 🤖 Dark mode, responsive, tất cả charts tương tác
- [ ] 🤖 Real-time data via WebSocket
- [ ] 🤖 Test coverage > 70% (Unit + Integration + E2E)
- [ ] 👤 Trivy + SonarQube tích hợp CI pipeline
- [ ] 👤 Secrets an toàn (Vault/External Secrets)
- [ ] 👤 WAF + HTTPS hoạt động

---

## Phase 5: Production Hardening & Go-Live — 2 tuần

**Mục tiêu:** Production-ready với deployment strategies an toàn, alerting, auto-scaling.

### Tuần 16 — Deployment Strategies & Alerting

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 16.1 | Blue-Green Deployment | 👤 Bạn | Phase 1 | Cấu hình 2 environments, traffic switching |
| 16.2 | Canary Deployment | 👤 Bạn | 16.1 | Istio/Argo Rollouts: 5% → 25% → 50% → 100% |
| 16.3 | Auto-rollback | 👤 Bạn | 16.2, 9.1 | Prometheus metrics → auto rollback nếu error rate tăng |
| 16.4 | CD Pipeline (Prod) | 👤 Bạn | 16.1 | Production deployment pipeline + approval gates |
| 16.5 | Alerting Rules | 👤 Bạn | 9.1 | CPU > 80%, error rate > 5%, service down, latency > 2s |
| 16.6 | Alert Channels | 👤 Bạn | 16.5 | Slack + Telegram webhooks |
| 16.7 | **API Documentation** | 🤖 AI | All services | FastAPI auto-gen Swagger/OpenAPI cho mỗi service |
| 16.8 | **Bug fixes** | 🤖 AI | Phase 4 | Fix issues từ testing |

### Tuần 17 — Go-Live

| # | Task | Người | Phụ thuộc | Chi tiết |
|---|------|-------|-----------|----------|
| 17.1 | Auto-scaling (HPA) | 👤 Bạn | Phase 1 | Horizontal Pod Autoscaler cho mỗi service |
| 17.2 | FinOps | 👤 Bạn | Phase 1 | Schedule tắt dev/staging cuối tuần, right-size requests |
| 17.3 | Load Testing | 👤 Bạn | 16.4 | k6/Locust stress test toàn hệ thống |
| 17.4 | **Runbooks** | 🤖 AI | — | Hướng dẫn xử lý sự cố: service down, DB full, rollback |
| 17.5 | **User Guide** | 🤖 AI | Phase 4 | Hướng dẫn sử dụng dashboard cho end-users |
| 17.6 | Production Deploy | 👤 Bạn | 16.4, 17.3 | Deploy lên production qua Blue-Green/Canary |
| 17.7 | Post-deploy Monitor | 👤 Bạn | 17.6 | Theo dõi sát 48h, sẵn sàng rollback |

**✅ Deliverable Phase 5:**

- [ ] 👤 Blue-Green & Canary deployment hoạt động
- [ ] 👤 Alerting tự động qua Slack/Telegram
- [ ] 👤 HPA auto-scaling policies
- [ ] 👤 Load test pass
- [ ] 🤖 API docs + Runbooks + User guide
- [ ] 👤 System deployed on production 🚀

---

## Tổng kết: Phân công xuyên suốt

```
         Tuần 1-4          Tuần 5-8          Tuần 9-11         Tuần 12-15        Tuần 16-17
         ──────────        ──────────        ──────────        ──────────        ──────────
👤 Bạn:  Terraform         MLflow K8s        Prometheus        Trivy             Blue-Green
         VPC/IAM           MLOps CI/CD       Grafana           SonarQube         Canary
         K8s/Registry      Model Gates       ELK Stack         Vault/WAF         Alerting
         CI/CD Pipeline    Model Serving     Health Checks     Deploy FE         Auto-scaling
         Deploy services   Deploy ML         Deploy WS/Notif                     Prod Deploy

🤖 AI:   DB Schema         Feature Eng.      Portfolio         Next.js 8 pages   API Docs
         Dockerfiles       ARIMA/XGBoost     Backtesting       WebSocket integ.  Runbooks
         Auth Service      LSTM              WebSocket (Go)    Unit/Integ Tests  Bug fixes
         API Gateway       FinBERT           Notification (Go) E2E Tests         User Guide
         Market Data       Sentiment         Pub/Sub linking
```

---

## Quy tắc làm việc

> [!TIP]
> **Mỗi tuần nên có 1 checkpoint:**
> 1. 👤 Bạn setup hạ tầng / deploy environment
> 2. 🤖 AI code service theo spec
> 3. 👤 Bạn review code
> 4. 🤖 AI fix feedback → build Docker image → push Registry
> 5. 👤 Bạn deploy lên K8s → verify → setup monitoring
> 6. ✅ Checkpoint passed → tuần tiếp theo

---

## Checklist Tổng Thể

- [x] Thiết kế kiến trúc hệ thống (Microservice)
- [ ] **Phase 1:** 👤 IaC + CI/CD | 🤖 Auth + Market Data *(tuần 1-4)*
- [ ] **Phase 2:** 👤 MLOps Pipeline | 🤖 3 ML Models + Sentiment *(tuần 5-8)*
- [ ] **Phase 3:** 👤 Monitoring + Logging | 🤖 Portfolio + WebSocket *(tuần 9-11)*
- [ ] **Phase 4:** 👤 DevSecOps | 🤖 Frontend + Tests *(tuần 12-15)*
- [ ] **Phase 5:** 👤 Deployment Strategies | 🤖 Docs *(tuần 16-17)*
