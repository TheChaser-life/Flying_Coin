# 🛠️ Tech Stack

## Backend — Python Services (Auth, Market Data, Forecast, Sentiment, Portfolio)

| Thành phần | Công nghệ | Phiên bản | Lý do chọn |
|---|---|---|---|
| Ngôn ngữ | Python | 3.11+ | Hệ sinh thái ML/Data Science phong phú |
| API Framework | FastAPI | 0.100+ | Async, tự sinh docs, type checking |
| Task Queue | Celery + Redis | 5.3+ | Background tasks, scheduled jobs |
| Scheduler | Apache Airflow (Docker Compose) | 2.8+ | ML pipeline orchestration (on-demand local, 24/7 cloud) |
| ORM | SQLAlchemy | 2.0+ | Async, migration Alembic |
| Data Processing | Pandas, NumPy | — | Xử lý dữ liệu |
| ML Framework | Scikit-learn, PyTorch (CUDA), XGBoost | — | PyTorch + RTX 4060 GPU cho LSTM, FinBERT |
| NLP | Hugging Face Transformers (FinBERT), spaCy | — | Pre-trained models tài chính |
| Portfolio | PyPortfolioOpt, SciPy | — | Markowitz, Efficient Frontier |
| Model Management | MLflow | 2.0+ | Versioning, tracking |

## Backend — Go Services (WebSocket, Notification)

| Thành phần | Công nghệ | Phiên bản | Lý do chọn |
|---|---|---|---|
| Ngôn ngữ | Go (Golang) | 1.22+ | Goroutines xử lý hàng triệu concurrent connections, memory cực thấp (~4KB/goroutine) |
| WebSocket | Gorilla WebSocket / nhk/websocket | — | Native WebSocket, hiệu năng cao, không cần fallback polling |
| HTTP Framework | Gin / Echo | — | Router nhanh, middleware ecosystem tốt |
| Redis Client | go-redis | 9.0+ | Subscribe Redis Pub/Sub, fan-out messages |
| Email | gomail / AWS SES SDK | — | Gửi email alerts hiệu quả |

## Frontend

| Thành phần | Công nghệ | Phiên bản |
|---|---|---|
| Framework | React / Next.js | 18+ / 14+ |
| Charting | Lightweight Charts (TradingView), Chart.js | — |
| State Management | Zustand | — |
| HTTP Client | Axios | — |
| WebSocket | Native WebSocket API / reconnecting-websocket | — |
| UI Library | Radix UI / Shadcn UI | — |
| Styling | Tailwind CSS | 3.0+ |

## Infrastructure

| Thành phần | Công nghệ |
|---|---|
| Database | PostgreSQL 16 + TimescaleDB |
| Message Queue (Data Ingestion) | RabbitMQ 3.13+ |
| Cache & Real-time Pub/Sub | Redis 7 |
| API Gateway | Kong / Nginx |
| Containerization | Docker |
| Orchestration | Kubernetes (dev + staging + production) |
| Local K8s (Dev) | Minikube (Docker Desktop driver) |
| SSL/TLS | Cloudflare / cert-manager |

## DevOps, IaC & Observability

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| IaC | Terraform | Định nghĩa hạ tầng Cloud bằng code (VPC, DB, K8s, Storage) |
| Configuration Management | Ansible *(tùy chọn)* | Tự động cài đặt phần mềm — không bắt buộc khi dùng managed K8s (GKE/EKS) |
| CI/CD | GitHub Actions | Tự động build, test, deploy khi push code |
| Container Registry | Amazon ECR / Google Artifact Registry | Kho lưu trữ Docker Images |
| Monitoring | Prometheus + Grafana | Thu thập metrics, dashboard trực quan |
| Logging | ELK Stack (Elasticsearch, Logstash, Kibana) | Centralized logging |
| Alerting | Prometheus Alertmanager + Slack/Telegram/PagerDuty | Cảnh báo tự động khi sự cố |
| Code Quality | SonarQube | Quét lỗi, technical debt, code smells |
| Container Security | Trivy | Quét lỗ hổng bảo mật trong Docker images |
| Secret Management | HashiCorp Vault / K8s Secrets | Quản lý API keys, passwords an toàn |

## External APIs

| API | Dữ liệu | Giá |
|-----|----------|-----|
| Yahoo Finance (yfinance) | Chứng khoán US & VN | Free |
| Binance API | Crypto real-time | Free |
| CoinGecko API | Crypto metadata | Free tier |
| Alpha Vantage | Chứng khoán + Hàng hóa | Free tier |
| NewsAPI | Tin tức tài chính | Free tier |
| VNDirect API | Chứng khoán Việt Nam | Free |
