# Bước 1 — Đưa data vào DB

Pipeline: **Collectors** (Yahoo/Binance) → **RabbitMQ** → **Market Data Service** → **PostgreSQL**

## Yêu cầu

- Minikube đang chạy
- Helm: `postgres`, `rabbitmq`, `redis` đã cài
- Python 3.11+ với venv

## Cách chạy (3 terminal)

### Terminal 1 — Port-forward (chạy nền, giữ mở)

```powershell
kubectl port-forward svc/postgres-postgresql 5432:5432 -n default
kubectl port-forward svc/rabbitmq 5672:5672 -n default
kubectl port-forward svc/redis-master 6379:6379 -n default
```

### Terminal 2 — Alembic migrations (chỉ 1 lần)

```powershell
cd "c:\code2\Working_Project (I'll name it later)"
$env:DATABASE_URL = "postgresql://user:testing123@127.0.0.1:5432/market_data"
alembic upgrade head
```

### Terminal 3 — Market Data Service (consumer)

```powershell
cd "c:\code2\Working_Project (I'll name it later)"
$env:PYTHONPATH = (Get-Location).Path
# Dùng asyncpg (async), không dùng postgresql:// (sync)
$env:DATABASE_URL = "postgresql+asyncpg://user:testing123@127.0.0.1:5432/market_data"
pip install -r services/market-data-service/requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --app-dir services/market-data-service
```

**Lưu ý:**
- Bắt buộc có `--app-dir services/market-data-service` để uvicorn tìm được module `app`.
- `DATABASE_URL` phải dùng `postgresql+asyncpg://` (async), không dùng `postgresql://` (sync). Nếu đã set `DATABASE_URL` cho Alembic, ghi đè lại trước khi chạy service.

### Terminal 4 — Collectors (producer)

```powershell
cd "c:\code2\Working_Project (I'll name it later)\services\collectors"
pip install -r requirements.txt
python main.py
```

Collectors chạy mỗi 60 giây. Sau 2–3 phút, kiểm tra data:

```powershell
python ml/scripts/run_dataset_builder.py --ticker AAPL -o ml/outputs/datasets
```

Nếu không lỗi và có dữ liệu → data đã vào DB ✓

## Config đã cập nhật

| Service | Thay đổi |
|---------|----------|
| Collectors | `RABBITMQ_URL`: admin:admin |
| Collectors | `YAHOO_PERIOD`: 1mo (21 ngày ~ 200 rows) |
| Collectors | `BINANCE_LIMIT`: 100 |
| Market Data Service | `DATABASE_URL`: user:testing123@.../market_data |
| Market Data Service | `RABBITMQ_URL`: admin:admin |
| Market Data Service | `REDIS_URL`: :admin@... |

## Script tự động

```powershell
.\scripts\run_data_pipeline_step1.ps1
```

Script kiểm tra Minikube, Helm, chạy migrations và in hướng dẫn.
