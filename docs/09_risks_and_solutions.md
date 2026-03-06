# ⚠️ Rủi Ro & Giải Pháp (Risks & Mitigations)

## Bảng tổng hợp

| # | Rủi ro | Mức độ | Xác suất | Giải pháp |
|---|--------|--------|----------|-----------|
| 1 | API rate limit từ nhà cung cấp | 🔴 Cao | Cao | Caching Redis, request queue, đa nguồn dữ liệu, tôn trọng rate limit |
| 2 | Mô hình ML dự báo không chính xác | 🔴 Cao | Cao | Ensemble models, retrain định kỳ, A/B testing, walk-forward validation |
| 3 | Dữ liệu thiếu hoặc sai lệch | 🟡 TB | TB | Data validation pipeline, multiple data sources, anomaly detection |
| 4 | Chi phí API cao khi scale | 🟡 TB | TB | Free-tier APIs trước, tối ưu request, caching aggressive |
| 5 | Overfitting mô hình | 🟡 TB | TB | Cross-validation, regularization, hold-out test set |
| 6 | Phức tạp microservice | 🟡 TB | Cao | Kubernetes orchestration, centralized logging, distributed tracing |
| 7 | Độ trễ real-time data | 🟢 Thấp | Thấp | WebSocket riêng, Redis Pub/Sub < 1ms |
| 8 | Database bottleneck | 🟡 TB | TB | TimescaleDB compression, indexing, connection pooling |
| 9 | Security breach | 🔴 Cao | Thấp | JWT, HTTPS, input validation, rate limiting, security audit |
| 10 | Service dependency failure | 🟡 TB | TB | Circuit breaker pattern, retry with backoff, fallback responses |
| 11 | **Cloud cost vượt ngân sách** | 🟡 TB | TB | Terraform bật/tắt, GCP budget alerts ($50/$100/$150), Minikube local Phase 1-2, GCP $300 free credit |
| 12 | **Migration Local → Cloud thất bại** | 🟢 Thấp | Thấp | Kustomize overlays đã test sẵn, chỉ đổi overlay (không sửa base), dự kiến chỉ mất 2-4 giờ |

## Chi tiết giải pháp

### 1. API Rate Limit
- **Vấn đề:** Yahoo Finance, Binance... giới hạn số request/phút
- **Giải pháp:**
  - Cache kết quả trong Redis (giảm 80%+ API calls)
  - Request queue với delay giữa các calls
  - Sử dụng nhiều API sources (fallback)
  - Batch requests khi có thể

### 2. Mô hình ML không chính xác
- **Vấn đề:** Thị trường tài chính inherently unpredictable
- **Giải pháp:**
  - Ensemble nhiều models → giảm variance
  - Walk-forward validation (không dùng future data)
  - Retrain định kỳ (weekly/monthly)
  - Drift detection → auto-retrain khi accuracy giảm
  - Disclaimer rõ ràng cho người dùng

### 3. Phức tạp Microservice
- **Vấn đề:** 8 services → debug khó, deploy phức tạp
- **Giải pháp:**
  - Kubernetes cho mọi môi trường (kubectl apply -k để deploy tất cả)
  - Centralized logging (ELK Stack)
  - Distributed tracing (Jaeger)
  - Health check endpoints cho mỗi service
  - Makefile / scripts tự động hóa
