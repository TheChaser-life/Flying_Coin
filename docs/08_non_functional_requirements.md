# ✅ Yêu Cầu Phi Chức Năng & Kiểm Thử

## 1. Yêu Cầu Phi Chức Năng

| # | Yêu cầu | Mô tả | Metric |
|---|---------|-------|--------|
| 1 | **Hiệu suất** | API response nhanh | < 500ms (trừ training) |
| 2 | **Throughput** | Xử lý đồng thời | > 1000 symbols cùng lúc |
| 3 | **Real-time** | WebSocket latency | < 100ms cho price updates |
| 4 | **Khả năng mở rộng** | Mỗi service scale độc lập | Horizontal scaling |
| 5 | **Độ tin cậy** | Uptime | > 99% |
| 6 | **Fault Tolerance** | Service lỗi không ảnh hưởng service khác | Fault isolation |
| 7 | **Bảo mật** | Authentication & encryption | JWT, HTTPS, API key encryption |
| 8 | **Rate Limiting** | Chống abuse | Free: 100 req/min, Premium: 1000 req/min |
| 9 | **Quan sát** | Logging & monitoring | Centralized logs, metrics dashboards |
| 10 | **Dữ liệu** | Lưu trữ lịch sử | ≥ 5 năm mỗi tài sản |
| 11 | **Tương thích** | Cross-browser | Chrome, Firefox, Safari, Edge |
| 12 | **Responsive** | Mobile-friendly | Desktop, tablet, mobile |

---

## 2. Chiến Lược Kiểm Thử

### 2.1 Unit Testing

**Mục tiêu:** Test từng function/method riêng lẻ trong mỗi service.

| Service | Ví dụ unit tests | Tool |
|---------|-----------------|------|
| Auth | Hashing password, JWT generation/validation | pytest |
| Market Data | Parse OHLCV data, data cleaning | pytest |
| Forecast | Feature engineering, model prediction | pytest |
| Sentiment | Text preprocessing, sentiment scoring | pytest |
| Portfolio | Markowitz optimization, Sharpe calculation | pytest |
| Frontend | Component rendering, state updates | Jest + React Testing Library |

**Target coverage:** > 70%

### 2.2 Integration Testing

**Mục tiêu:** Test giao tiếp giữa các services và với database.

| Test case | Mô tả |
|-----------|-------|
| Auth → DB | Đăng ký lưu đúng vào PostgreSQL, login trả JWT đúng |
| Market Data → DB | Dữ liệu crawl lưu đúng vào TimescaleDB |
| Market Data → Redis | Giá mới publish đúng channel Redis |
| Forecast → MLflow | Model lưu và load từ MLflow đúng |
| WebSocket → Redis | Subscribe đúng channels, nhận đúng data |
| API Gateway → Services | Routing đúng service, rate limiting hoạt động |

**Tool:** pytest + httpx (async), Kubernetes dev namespace test environment

### 2.3 End-to-End (E2E) Testing

**Mục tiêu:** Test toàn bộ luồng từ frontend đến backend.

| Test case | Luồng |
|-----------|-------|
| User Registration | Frontend → API Gateway → Auth Service → DB → Email |
| View Stock Price | Frontend → Gateway → Market Data Service → DB → Response |
| Get Forecast | Frontend → Gateway → Forecast Service → ML Model → Response |
| Real-time Price | Market Data → Redis → WebSocket Service → Frontend |
| Create Alert | Frontend → Gateway → Notification Service → DB |
| Alert Trigger | Price update → Redis → Notification → Email |

**Tool:** Playwright / Cypress (frontend), pytest (backend)

### 2.4 Performance Testing

**Mục tiêu:** Đảm bảo hệ thống đáp ứng yêu cầu hiệu suất.

| Test | Metric | Tool |
|------|--------|------|
| API Response Time | < 500ms p95 | Locust / k6 |
| WebSocket Latency | < 100ms | Custom script |
| Concurrent Users | 100+ users đồng thời | Locust |
| Database Query | < 100ms cho time-range queries | pgbench |
| ML Inference | < 2s cho prediction | pytest-benchmark |

### 2.5 Security Testing

| Test | Mô tả | Tool |
|------|-------|------|
| JWT Validation | Token expired, invalid, tampered | pytest |
| SQL Injection | Input sanitization | sqlmap |
| Rate Limiting | Vượt quá limit → 429 | Custom script |
| CORS | Chỉ allowed origins | Manual |
| HTTPS | Redirect HTTP → HTTPS | SSL Labs |

### 2.6 ML Model Testing

| Test | Mô tả |
|------|-------|
| **Data Validation** | Input data đúng format, không null, trong range |
| **Model Accuracy** | RMSE, MAE, MAPE trong ngưỡng chấp nhận |
| **Directional Accuracy** | > 55% (tốt hơn random) |
| **Overfitting Check** | Train accuracy vs Test accuracy gap < 10% |
| **Drift Detection** | Model accuracy giảm → trigger retrain |
| **A/B Testing** | So sánh model mới vs model cũ trên live data |
