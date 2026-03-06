# 📊 Market Data Mining & Forecasting System (MDMFS)

## Khai Phá Dữ Liệu & Dự Báo Thị Trường

Hệ thống thu thập, phân tích và dự báo dữ liệu thị trường tài chính — bao gồm chứng khoán, tiền điện tử và hàng hóa — sử dụng Machine Learning, NLP, và Portfolio Optimization.

---

## 📚 Tài Liệu Dự Án

| # | Tài liệu | Mô tả |
|---|----------|-------|
| 1 | [Tổng Quan Dự Án](docs/01_project_overview.md) | Mục tiêu, đối tượng, phạm vi, disclaimer |
| 2 | [Kiến Trúc Hệ Thống](docs/02_system_architecture.md) | Microservice architecture, modules, services, database, giao tiếp |
| 3 | [Tính Năng Người Dùng & Giao Diện](docs/03_user_features.md) | 8 tính năng chính, user journey, mô tả UI/UX |
| 4 | [Kế Hoạch Phát Triển](docs/04_development_roadmap.md) | 5 phases, ~21 tuần, tasks chi tiết theo tuần |
| 5 | [Tech Stack](docs/05_tech_stack.md) | Backend, Frontend, Infrastructure, External APIs |
| 6 | [Cấu Trúc Thư Mục](docs/06_project_structure.md) | 8 services + frontend + shared + notebooks |
| 7 | [API Endpoints](docs/07_api_endpoints.md) | REST APIs + WebSocket events cho tất cả services |
| 8 | [Yêu Cầu Phi Chức Năng & Kiểm Thử](docs/08_non_functional_requirements.md) | Performance, security, testing strategies |
| 9 | [Rủi Ro & Giải Pháp](docs/09_risks_and_solutions.md) | 10 rủi ro chính + giải pháp chi tiết |
| 10 | [Định Hướng Mở Rộng](docs/10_expansion_direction.md) | Short/medium/long-term features, scaling |
| 11 | [Thuật Ngữ Tài Chính](docs/11_financial_glossary.md) | 80+ thuật ngữ cần biết: Price, Indicators, Portfolio, Trading, ML, NLP, Macro |

---

## 🏗️ Kiến Trúc Tổng Quan

```
Client (React/Next.js)
    │
    ├── HTTP ──► API Gateway ──► Auth / Market Data / Forecast / Sentiment / Portfolio
    │
    └── WS ───► WebSocket Service ◄──── Redis Pub/Sub ◄──── All Services
```

**8 Microservices:** API Gateway, Auth, Market Data, Forecast, Sentiment, Portfolio, WebSocket, Notification

## ⚙️ Tech Stack Chính

- **Backend:** Python, FastAPI, Celery, SQLAlchemy
- **ML/AI:** XGBoost, LSTM, ARIMA, FinBERT (NLP), PyPortfolioOpt
- **Frontend:** React/Next.js, TradingView Charts, Tailwind CSS
- **Database:** PostgreSQL + TimescaleDB, Redis
- **Infra:** Docker, Kubernetes, MLflow, Prometheus+Grafana, ELK

## 📅 Timeline

**~21 tuần (5-6 tháng)** chia thành 5 phases: Foundation → ML & Sentiment → Portfolio & WebSocket → Frontend → Polish & Deploy

---

> ⚠️ **Disclaimer:** Dự án phục vụ mục đích nghiên cứu và học tập. Kết quả dự báo không phải lời khuyên đầu tư.
