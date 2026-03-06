# 🏗️ Kiến Trúc Hệ Thống (System Architecture)

## 1. Tổng quan kiến trúc — Microservice

Hệ thống được thiết kế theo **kiến trúc Microservice**, trong đó mỗi service đảm nhận một chức năng riêng biệt, giao tiếp thông qua:
- **REST API** (đồng bộ) — client ↔ services
- **RabbitMQ** (bất đồng bộ) — data ingestion pipeline (thu thập → xử lý dữ liệu thô)
- **Redis Pub/Sub** (real-time) — services → WebSocket → dashboard + cache

```
       External APIs (Yahoo, Binance, NewsAPI)
                      │
                      ▼
              Python Collectors
              (Market Data + News)
                      │
                      ▼
          ┌──────────────────────┐
          │     RabbitMQ         │  ← Data Ingestion Pipeline
          │  (Message Queues)    │    Persistent, reliable delivery
          └──────────┬───────────┘
                     │ Consume
                     ▼
┌────────────────────────────────────────────────────────────────────┐
│                     KUBERNETES CLUSTER                             │
│                                                                    │
│  ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  Auth  │ │ Market   │ │ Forecast │ │Sentiment │ │Portfolio │  │
│  │Service │ │  Data    │ │ Service  │ │ Service  │ │ Service  │  │
│  │(Python)│ │ (Python) │ │ (Python) │ │ (Python) │ │ (Python) │  │
│  └────────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────────┘  │
│                  │  Publish   │  Publish    │  Publish             │
│                  ▼            ▼             ▼                      │
│          ┌─────────────────────────────────────────┐               │
│          │         Redis (Pub/Sub + Cache)          │  ← Real-time │
│          └──────┬──────────┬──────────┬────────────┘    in-cluster │
│                 │          │          │                             │
│                 ▼          ▼          ▼                             │
│          ┌──────────┐ ┌──────────────┐                             │
│          │WebSocket │ │ Notification │                             │
│          │ (Go)     │ │    (Go)      │                             │
│          └────┬─────┘ └──────────────┘                             │
│               │                                                    │
│  ┌────────────┼──────────────────────────────────────────────┐      │
│  │ API Gateway│(Kong/Nginx)    Ingress + Load Balancer       │      │
│  └────────────┼──────────────────────────────────────────────┘      │
│               │                                                    │
│  Infrastructure:                                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐      │
│  │ PostgreSQL + │ │    MLflow    │ │Prometheus│ │   ELK    │      │
│  │ TimescaleDB  │ │ Model Store │ │+ Grafana │ │  Stack   │      │
│  └──────────────┘ └──────────────┘ └──────────┘ └──────────┘      │
└────────────────────────────────────────────────────────────────────┘
           │ HTTP/REST                  │ WebSocket (wss://)
           ▼                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                           │
│                     React / Next.js Frontend                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Danh sách các Microservices

| # | Service | Công nghệ | Vai trò | Giao tiếp |
|---|---------|-----------|---------|-----------|
| 1 | **API Gateway** | Kong / Nginx | Điều hướng request, rate limiting, load balancing | HTTP → các service |
| 2 | **Auth Service** | Python FastAPI | Đăng ký, đăng nhập, JWT, phân quyền (RBAC) | HTTP |
| 3 | **Market Data Service** | Python FastAPI | Thu thập & cung cấp dữ liệu thị trường | HTTP + Publish Redis |
| 4 | **Forecast Service** | Python FastAPI | Chạy mô hình ML, trả kết quả dự báo | HTTP + Publish Redis |
| 5 | **Sentiment Service** | Python FastAPI | Thu thập tin tức, chạy NLP, tính sentiment | HTTP + Publish Redis |
| 6 | **Portfolio Service** | Python FastAPI | Tối ưu danh mục, backtesting, Monte Carlo | HTTP |
| 7 | **WebSocket Service** | Go (Gorilla WebSocket) | Đẩy dữ liệu real-time đến client — goroutines xử lý hàng nghìn connections đồng thời | WebSocket + Subscribe Redis |
| 8 | **Notification Service** | Go (Gin) | Gửi email, push notification, alerts — Go concurrency model tối ưu cho fan-out I/O | Subscribe Redis |

---

## 3. Mối quan hệ Module ↔ Service

Trong hệ thống này, **1 module nghiệp vụ = 1 microservice**. Mỗi service là một ứng dụng FastAPI riêng biệt, chạy trong Docker container riêng.

```
Module (chức năng nghiệp vụ)          Service (đơn vị triển khai)
─────────────────────────────          ─────────────────────────────
Thu thập dữ liệu              ──────► Market Data Service
Dự báo ML                     ──────► Forecast Service
Phân tích tâm lý              ──────► Sentiment Service
Tối ưu danh mục               ──────► Portfolio Service
Xác thực                      ──────► Auth Service
Real-time data                ──────► WebSocket Service
Thông báo                     ──────► Notification Service
Điều hướng                    ──────► API Gateway
```

**Nguyên tắc:** Bắt đầu với 1 module = 1 service. Khi cần scale, có thể tách một module thành nhiều services nhỏ hơn (ví dụ: tách Forecast Service thành Training Service + Prediction Service).

---

## 4. Giao tiếp giữa các Services

| Kiểu | Dùng khi | Công cụ |
|------|----------|---------|
| **Đồng bộ (Sync)** | Client cần response ngay (VD: lấy dữ liệu, dự báo) | REST API qua API Gateway |
| **Bất đồng bộ — Data Pipeline** | Thu thập dữ liệu thô, cần đảm bảo không mất message | RabbitMQ (durable queues) |
| **Bất đồng bộ — Real-time** | Push updates đến dashboard, alerts | Redis Pub/Sub (low latency) |

### Phân biệt RabbitMQ vs Redis Pub/Sub

| | RabbitMQ | Redis Pub/Sub |
|---|---------|---------------|
| **Vai trò** | Message queue cho data ingestion | Real-time pub/sub + cache |
| **Vị trí** | Data ingestion layer | Trong K8s cluster |
| **Message persistence** | ✅ Durable — không mất khi consumer offline | ❌ Fire-and-forget — OK cho real-time |
| **Use case** | Collectors → Processing services | Services → WebSocket → Frontend |

### Ví dụ luồng hoàn chỉnh

```
=== Luồng 1: Data Ingestion (RabbitMQ) ===

1. Python Collector lấy giá BTC từ Binance API
   → Đẩy raw data vào RabbitMQ queue: "market.raw.crypto"

2. Market Data Service consume từ RabbitMQ
   → Xử lý, làm sạch dữ liệu
   → Lưu PostgreSQL + TimescaleDB
   → Publish Redis: "price:BTC" = $72,500  (chuyển sang luồng real-time)

=== Luồng 2: Real-time Updates (Redis Pub/Sub) ===

3. WebSocket Service (Go) subscribe Redis "price:*"
   → Nhận "price:BTC" = $72,500
   → Đẩy đến tất cả client đang xem BTC trên dashboard

4. Notification Service (Go) subscribe Redis "price:*"
   → Nhận "price:BTC" = $72,500
   → Kiểm tra: User A đặt alert "BTC > $72,000"
   → Gửi email cho User A

5. Forecast Service subscribe Redis "price:*"
   → Nhận giá mới → Cập nhật feature → Re-predict nếu cần
```

### Sơ đồ giao tiếp chi tiết

```
  External APIs                      Client (Browser)
  (Yahoo, Binance,                        │
   NewsAPI)                               │ HTTP/REST + WebSocket
       │                                  ▼
       ▼                           ┌──────────────┐
  Python Collectors                │  API Gateway  │──── REST ────┐
       │                           └──────┬───────┘              │
       ▼                                  │                      │
 ┌────────────┐                           ▼                      ▼
 │  RabbitMQ  │ ◄── Data Ingestion  ┌──────────┐          ┌──────────┐
 │  (Queues)  │     Pipeline        │  Auth    │          │ Portfolio│
 └─────┬──────┘                     │ Service  │          │ Service  │
       │ Consume                    └──────────┘          └──────────┘
       ▼
 ┌──────────┐    Publish     ┌─────────────────────────────┐
 │ Market   │──────────────►│     Redis (Pub/Sub + Cache)  │
 │  Data    │               └──┬──────────┬───────────┬────┘
 │ Service  │                  │          │           │
 └──────────┘                  ▼          ▼           ▼
                         ┌─────────┐ ┌────────┐ ┌──────────────┐
 ┌──────────┐  Publish   │Forecast │ │Websock │ │ Notification │
 │Sentiment │───────────►│ Service │ │  (Go)  │ │    (Go)      │
 │ Service  │  (Redis)   └─────────┘ └───┬────┘ └──────────────┘
 └──────────┘                            │
                                         ▼
                                   Client (wss://)
```

---

## 5. Chi tiết từng Module / Service

### 5.1. Auth Service

- **Chức năng:** Đăng ký, đăng nhập, JWT token, phân quyền (RBAC)
- **Database:** PostgreSQL (bảng `users`)
- **Giao tiếp:** HTTP only (không publish/subscribe Redis)

### 5.2. Market Data Service

- **Chức năng:** Thu thập dữ liệu từ Yahoo Finance, Binance, Alpha Vantage, NewsAPI, Twitter/Reddit
- **Database:** PostgreSQL + TimescaleDB (bảng `market_data`, `symbols`)
- **Giao tiếp:** HTTP + Publish Redis (`price:*`, `market:summary`)

**Nguồn dữ liệu:**

| Loại thị trường | Nguồn API | Dữ liệu thu thập |
|---|---|---|
| **Chứng khoán** | Yahoo Finance API, Alpha Vantage, VNDirect API | Giá OHLCV, khối lượng, chỉ số tài chính |
| **Tiền điện tử** | Binance API, CoinGecko API, CoinMarketCap | Giá real-time, order book, volume, market cap |
| **Hàng hóa** | Alpha Vantage, Quandl | Giá vàng, dầu, nông sản, kim loại |
| **Tin tức** | NewsAPI, RSS Feeds, Google News | Tiêu đề, nội dung, thời gian đăng |
| **Mạng xã hội** | Twitter/X API, Reddit API | Bài đăng, bình luận, xu hướng |

**Tính năng:**
- ⏰ Lên lịch crawl tự động theo chu kỳ (1m, 5m, 1h, 1D)
- 📦 Lưu trữ dữ liệu thô (raw) và đã xử lý (processed)
- 🔁 Cơ chế retry khi API lỗi hoặc giới hạn rate limit
- 🧹 Pipeline làm sạch dữ liệu: xử lý missing values, outlier, chuẩn hóa

**Cấu trúc dữ liệu:**
```
market_data:
  - symbol: "AAPL"          # Mã chứng khoán
  - timestamp: datetime      # Thời gian
  - open: float              # Giá mở cửa
  - high: float              # Giá cao nhất
  - low: float               # Giá thấp nhất
  - close: float             # Giá đóng cửa
  - volume: int              # Khối lượng giao dịch
  - adjusted_close: float    # Giá đóng cửa điều chỉnh
  - market_type: enum        # stock | crypto | commodity
  - source: string           # Nguồn dữ liệu
```

### 5.3. Forecast Service

- **Chức năng:** Xây dựng & triển khai mô hình ML dự báo xu hướng giá
- **Database:** PostgreSQL (bảng `predictions`, `technical_indicators`) + MLflow
- **Giao tiếp:** HTTP + Publish Redis (`forecast:*`) + Subscribe Redis (`price:*`)

**Các mô hình ML:**

| Mô hình | Loại | Mục đích | Giai đoạn |
|---|---|---|---|
| **XGBoost** | Gradient Boosting | Dự báo ngắn hạn, directional accuracy 71% | Phase 1 (MVP) |
| **LSTM** | Deep Learning | Nắm bắt xu hướng dài hạn | Phase 1 (MVP) |
| **ARIMA** | Statistical | Baseline benchmark | Phase 1 (MVP) |
| **LightGBM** | Gradient Boosting | Tương tự XGBoost, nhanh hơn | Phase 2 |
| **Prophet** | Statistical | Phân tích mùa vụ | Phase 2 |
| **Random Forest** | Ensemble | Phân loại tín hiệu mua/bán | Phase 2 |
| **GRU** | Deep Learning | Biến thể nhẹ hơn LSTM | Phase 3 |
| **Transformer** | Deep Learning | Dự báo đa biến phức tạp | Phase 3 |
| **Ensemble Model** | Hybrid | Kết hợp nhiều mô hình | Phase 3 |

**Feature Engineering:**
```
Chỉ báo kỹ thuật (Technical Indicators):
├── Moving Averages: SMA, EMA (7, 14, 21, 50, 200 ngày)
├── Momentum: RSI, MACD, Stochastic Oscillator
├── Volatility: Bollinger Bands, ATR
├── Volume: OBV, VWAP
├── Trend: ADX, Parabolic SAR, Ichimoku Cloud
└── Custom: Price Rate of Change, Logarithmic Returns

Đặc trưng bổ sung:
├── Sentiment Score (từ Sentiment Service)
├── Tương quan giữa các tài sản
├── Dữ liệu vĩ mô: lãi suất, CPI, GDP
└── Calendar Features: ngày trong tuần, tháng, quý, ngày lễ
```

**Pipeline ML:**
```
Raw Data → Feature Engineering → Train/Validation/Test Split
    → Model Training → Hyperparameter Tuning (Optuna)
    → Model Evaluation (RMSE, MAE, MAPE, Directional Accuracy)
    → Model Registry (MLflow) → Serving (FastAPI endpoint)
```

### 5.4. Sentiment Service

- **Chức năng:** Phân tích tâm lý thị trường qua tin tức & mạng xã hội
- **Database:** PostgreSQL (bảng `sentiment_scores`, `news_articles`)
- **Giao tiếp:** HTTP + Publish Redis (`sentiment:*`, `news:latest`, `fear_greed`)

**Mô hình NLP:**

| Mô hình | Mục đích | Giai đoạn |
|---------|----------|-----------|
| **FinBERT** | Sentiment chuyên biệt tài chính (accuracy 0.88) | Phase 1 (MVP) |
| **VADER** | Phân tích sentiment nhanh, rule-based | Phase 2 |
| **Custom BERT/PhoBERT** | Tinh chỉnh cho thị trường Việt Nam | Phase 2 |
| **News Classifier** | Phân loại tin tức theo chủ đề | Phase 3 |

**Pipeline NLP:**
```
Thu thập văn bản (News, Social Media)
    → Tiền xử lý (Tokenization, Stop words, Lemmatization)
    → Phân tích Sentiment (FinBERT / VADER)
    → Tính Sentiment Score (-1.0 → +1.0, có trọng số)
    → Publish Redis → Forecast Service + WebSocket Service
```

### 5.5. Portfolio Service

- **Chức năng:** Tối ưu hóa danh mục đầu tư, backtesting
- **Database:** PostgreSQL (bảng `portfolios`)
- **Giao tiếp:** HTTP only

**Chiến lược tối ưu hóa:**

| Chiến lược | Mô tả | Giai đoạn |
|---|---|---|
| **Mean-Variance (Markowitz)** | Tối ưu Sharpe Ratio | Phase 1 (MVP) |
| **Minimum Volatility** | Giảm thiểu rủi ro | Phase 1 |
| **Maximum Sharpe Ratio** | Tối đa lợi nhuận/rủi ro | Phase 1 |
| **Risk Parity** | Phân bổ rủi ro đều | Phase 2 |
| **Black-Litterman** | Kết hợp quan điểm nhà đầu tư | Phase 3 |
| **HRP** | Phân cụm tài sản | Phase 3 |

### 5.6. WebSocket Service (Go)

- **Chức năng:** Đẩy dữ liệu real-time đến client
- **Ngôn ngữ:** Go (Golang) — Gorilla WebSocket + go-redis
- **Giao tiếp:** WebSocket (đến client) + Subscribe Redis (từ services)

Tách riêng khỏi backend Python vì:
- REST API = stateless, WebSocket = stateful → yêu cầu scale khác nhau
- Go goroutines xử lý hàng nghìn connections đồng thời với ~4KB/goroutine (vs ~8MB/thread Python)
- Fault isolation: WS lỗi không ảnh hưởng REST API
- Compile ra single binary → Docker image nhỏ (~10-20MB vs ~500MB+ Python)

**Channels:**

| Channel | Dữ liệu | Tần suất |
|---------|----------|----------|
| `price:{symbol}` | Giá real-time | 1-5 giây |
| `sentiment:{symbol}` | Sentiment score | Khi có tin mới |
| `forecast:{symbol}` | Dự báo cập nhật | Khi model chạy xong |
| `alert:{user_id}` | Cảnh báo cá nhân | Khi trigger |
| `market:summary` | Tổng quan thị trường | 30 giây |
| `news:latest` | Tin tức mới | Khi có tin |
| `fear_greed` | Fear & Greed Index | 5 phút |

### 5.7. Notification Service (Go)

- **Chức năng:** Gửi email, push notification khi điều kiện cảnh báo được kích hoạt
- **Ngôn ngữ:** Go (Golang) — Gin + gomail/AWS SES SDK
- **Database:** PostgreSQL (bảng `alerts`)
- **Giao tiếp:** Subscribe Redis (`price:*`, `sentiment:*`, `forecast:*`)
- **Lý do dùng Go:** Fan-out gửi hàng nghìn notifications cùng lúc — goroutines + channels xử lý I/O-bound tasks rất hiệu quả

---

## 6. Hệ thống Database

### 6.1 Tổng quan

| Database / Broker | Vai trò | Loại dữ liệu |
|-------------------|---------|---------------|
| **PostgreSQL + TimescaleDB** | Database chính | Dữ liệu có cấu trúc + time-series |
| **RabbitMQ** | Message Queue — Data Ingestion | Raw data từ collectors (persistent, durable queues) |
| **Redis** | Cache + Real-time Pub/Sub | Dữ liệu tạm thời + push updates đến WebSocket/dashboard |
| **MLflow Backend Store** | Model Registry | Metadata mô hình ML |

> **Lưu ý:** TimescaleDB là **extension** của PostgreSQL (không phải DB riêng). Chỉ cần cài PostgreSQL + bật extension.

### 6.2 PostgreSQL + TimescaleDB

| Bảng | Service sở hữu | Mô tả |
|------|----------------|-------|
| `users` | Auth Service | Thông tin tài khoản, preferences |
| `market_data` | Market Data Service | Giá OHLCV — *TimescaleDB hypertable* |
| `symbols` | Market Data Service | Thông tin mã chứng khoán/coin |
| `technical_indicators` | Forecast Service | SMA, EMA, RSI, MACD đã tính |
| `predictions` | Forecast Service | Kết quả dự báo |
| `sentiment_scores` | Sentiment Service | Điểm sentiment |
| `news_articles` | Sentiment Service | Tin tức đã thu thập |
| `portfolios` | Portfolio Service | Danh mục đầu tư |
| `alerts` | Notification Service | Điều kiện cảnh báo |

### 6.3 Redis

| Key pattern | TTL | Mục đích |
|-------------|-----|----------|
| `price:{symbol}` | 60s | Cache giá mới nhất |
| `forecast:{symbol}` | 1-24h | Cache kết quả dự báo |
| `sentiment:{symbol}` | 1h | Cache sentiment score |
| `ratelimit:{user_id}` | 1min/1h | Rate limiting |
| `session:{token}` | 24h | JWT token blacklist |
| `celery:*` | Tùy task | Task queue |
| `channel:*` | Realtime | Pub/Sub giữa services |
| `fear_greed:current` | 1h | Cache Fear & Greed Index |

### 6.4 MLflow

| Loại dữ liệu | Lưu ở đâu | Mô tả |
|---------------|-----------|-------|
| Experiment metadata | PostgreSQL (mlflow DB) | Tên, parameters, metrics |
| Model artifacts | File system / S3 | File .pkl, .h5, .pt |
| Model versions | PostgreSQL (mlflow DB) | Version tracking |

### 6.5 RabbitMQ

| Queue | Producer | Consumer | Mục đích |
|-------|----------|----------|----------|
| `market.raw.stock` | Market Data Collectors | Market Data Service | Dữ liệu thô chứng khoán |
| `market.raw.crypto` | Market Data Collectors | Market Data Service | Dữ liệu thô crypto |
| `market.raw.commodity` | Market Data Collectors | Market Data Service | Dữ liệu thô hàng hóa |
| `news.raw` | News Collectors | Sentiment Service | Tin tức thô cần phân tích |
| `ml.training.trigger` | Airflow / Scheduler | Forecast Service | Trigger huấn luyện model |

> **Lưu ý:** RabbitMQ queues sử dụng **durable mode** — message không bị mất khi broker restart hoặc consumer offline.

### 6.6 Sơ đồ luồng dữ liệu

```
External APIs (Yahoo, Binance, NewsAPI)
        │
        ▼
  Python Collectors
        │
        ▼
┌───────────────────┐
│    RabbitMQ       │ ← Data Ingestion (persistent queues)
│ • market.raw.*    │
│ • news.raw        │
│ • ml.training.*   │
└────────┬──────────┘
         │ Consume & Process
         ▼
┌───────────────────┐     ┌────────────────────────┐
│   PostgreSQL +    │     │     Redis              │
│   TimescaleDB     │     │  (Cache + Pub/Sub)     │ ← Real-time in K8s
│                   │     │                        │
│ • market_data  ◄──┼─────┤ • price:* (cache)      │
│ • news_articles   │     │ • sentiment:* (cache)  │
│ • sentiment_scores│     │ • channel:* (pub/sub)  │
│ • predictions     │     │ • ratelimit:*          │
│ • portfolios      │     │ • celery:*             │
│ • users           │     └──────┬─────────────────┘
│ • symbols         │            │ Pub/Sub (real-time)
│ • alerts          │            ▼
└────────┬──────────┘   ┌──────────────────┐
         │              │ WebSocket (Go)   │ → Client Dashboard
         ▼              └──────────────────┘
┌───────────────────┐
│   MLflow Store    │
│ • experiments     │
│ • model artifacts │ → File system / S3
└───────────────────┘
```
