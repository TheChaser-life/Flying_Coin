# 🔗 Danh Sách API Endpoints

## Auth API (Auth Service)

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| POST | `/api/v1/auth/register` | Đăng ký tài khoản | ❌ |
| POST | `/api/v1/auth/login` | Đăng nhập → JWT token | ❌ |
| POST | `/api/v1/auth/logout` | Đăng xuất | ✅ |
| POST | `/api/v1/auth/refresh` | Refresh access token | ✅ |
| POST | `/api/v1/auth/forgot-password` | Quên mật khẩu | ❌ |
| PUT | `/api/v1/auth/reset-password` | Đặt lại mật khẩu | ❌ |
| GET | `/api/v1/auth/me` | Thông tin user hiện tại | ✅ |
| PUT | `/api/v1/auth/me` | Cập nhật profile | ✅ |

## Market Data API (Market Data Service)

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| GET | `/api/v1/market/symbols` | Danh sách tất cả symbols | ✅ |
| GET | `/api/v1/market/symbols/search?q=` | Tìm kiếm symbol | ✅ |
| GET | `/api/v1/market/{symbol}/history` | Dữ liệu lịch sử (params: timeframe, from, to) | ✅ |
| GET | `/api/v1/market/{symbol}/realtime` | Giá hiện tại | ✅ |
| GET | `/api/v1/market/{symbol}/indicators` | Chỉ báo kỹ thuật (SMA, RSI, MACD...) | ✅ |
| POST | `/api/v1/market/bulk-download` | Tải dữ liệu hàng loạt | ✅ Premium |
| GET | `/api/v1/market/summary` | Tổng quan thị trường (top gainers/losers) | ✅ |

## Forecasting API (Forecast Service)

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| POST | `/api/v1/forecast/{symbol}` | Dự báo giá (params: days, model) | ✅ |
| GET | `/api/v1/forecast/{symbol}/latest` | Dự báo mới nhất | ✅ |
| GET | `/api/v1/forecast/{symbol}/signal` | Tín hiệu MUA/GIỮ/BÁN | ✅ |
| GET | `/api/v1/models` | Danh sách mô hình ML | ✅ |
| GET | `/api/v1/models/{model_id}/performance` | Hiệu suất mô hình | ✅ |
| POST | `/api/v1/models/train` | Huấn luyện mô hình mới | ✅ Admin |
| GET | `/api/v1/models/compare` | So sánh nhiều mô hình | ✅ |

## Sentiment API (Sentiment Service)

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| GET | `/api/v1/sentiment/{symbol}` | Sentiment score hiện tại | ✅ |
| GET | `/api/v1/sentiment/{symbol}/history` | Sentiment theo thời gian | ✅ |
| GET | `/api/v1/sentiment/{symbol}/news` | Tin tức liên quan + sentiment | ✅ |
| GET | `/api/v1/sentiment/trending` | Chủ đề trending | ✅ |
| GET | `/api/v1/sentiment/fear-greed` | Fear & Greed Index | ✅ |
| GET | `/api/v1/sentiment/wordcloud/{symbol}` | Word Cloud data | ✅ |

## Portfolio API (Portfolio Service)

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| POST | `/api/v1/portfolio/optimize` | Tối ưu hóa danh mục | ✅ |
| POST | `/api/v1/portfolio/backtest` | Chạy backtest | ✅ |
| GET | `/api/v1/portfolio/efficient-frontier` | Đường biên hiệu quả | ✅ |
| POST | `/api/v1/portfolio/risk-analysis` | Phân tích rủi ro | ✅ |
| POST | `/api/v1/portfolio/monte-carlo` | Mô phỏng Monte Carlo | ✅ Premium |
| GET | `/api/v1/portfolio/strategies` | Danh sách chiến lược hỗ trợ | ✅ |

## Notification API (Notification Service)

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| POST | `/api/v1/alerts` | Tạo cảnh báo mới | ✅ |
| GET | `/api/v1/alerts` | Danh sách cảnh báo | ✅ |
| PUT | `/api/v1/alerts/{alert_id}` | Cập nhật cảnh báo | ✅ |
| DELETE | `/api/v1/alerts/{alert_id}` | Xóa cảnh báo | ✅ |
| GET | `/api/v1/alerts/history` | Lịch sử cảnh báo đã trigger | ✅ |

## WebSocket Events (WebSocket Service)

### Client → Server

| Event | Payload | Mô tả |
|-------|---------|-------|
| `subscribe` | `["price:BTC", "sentiment:AAPL"]` | Đăng ký channels |
| `unsubscribe` | `["price:BTC"]` | Hủy đăng ký |

### Server → Client

| Event | Payload | Mô tả |
|-------|---------|-------|
| `price_update` | `{symbol, price, change, volume}` | Cập nhật giá |
| `sentiment_update` | `{symbol, score, source}` | Cập nhật sentiment |
| `forecast_update` | `{symbol, prediction, confidence}` | Dự báo mới |
| `alert_triggered` | `{alert_id, message, data}` | Cảnh báo kích hoạt |
| `news_update` | `{title, source, sentiment, url}` | Tin tức mới |
| `market_summary` | `{gainers, losers, indices}` | Tổng quan thị trường |
| `fear_greed` | `{value, label}` | Fear & Greed Index |
