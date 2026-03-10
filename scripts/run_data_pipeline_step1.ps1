# =============================================================================
# Bước 1 — Đưa data vào DB
# =============================================================================
# Pipeline: Collectors (Yahoo/Binance) -> RabbitMQ -> Market Data Service -> PostgreSQL
#
# Yêu cầu:
#   - Minikube đang chạy
#   - Helm: postgres, rabbitmq, redis đã cài
#   - Alembic migrations đã chạy
#
# Cách dùng:
#   1. Mở 3 terminal
#   2. Terminal 1: Port-forward (chạy nền)
#   3. Terminal 2: Market Data Service (consumer)
#   4. Terminal 3: Collectors (producer)
# =============================================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "=== Bước 1: Data Pipeline vao DB ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray

# --- 1. Kiểm tra Minikube ---
Write-Host "`n[1/5] Kiem tra Minikube..." -ForegroundColor Yellow
$mk = minikube status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Minikube chua chay. Chay: minikube start" -ForegroundColor Red
    exit 1
}
Write-Host "Minikube OK" -ForegroundColor Green

# --- 2. Kiểm tra Helm releases ---
Write-Host "`n[2/5] Kiem tra Helm (postgres, rabbitmq, redis)..." -ForegroundColor Yellow
$releases = helm list -q 2>&1
if ($releases -notmatch "postgres") {
    Write-Host "PostgreSQL chua cai. Chay:" -ForegroundColor Red
    Write-Host "  helm install postgres bitnami/postgresql -f helm_values/postgres/postgres-local.yaml" -ForegroundColor White
    exit 1
}
if ($releases -notmatch "rabbitmq") {
    Write-Host "RabbitMQ chua cai. Chay:" -ForegroundColor Red
    Write-Host "  helm install rabbitmq bitnami/rabbitmq -f helm_values/rabbitmq/rabbitmq-local.yaml" -ForegroundColor White
    exit 1
}
if ($releases -notmatch "redis") {
    Write-Host "Redis chua cai. Chay:" -ForegroundColor Red
    Write-Host "  helm install redis bitnami/redis -f helm_values/redis/redis-local.yaml" -ForegroundColor White
    exit 1
}
Write-Host "PostgreSQL, RabbitMQ, Redis OK" -ForegroundColor Green

# --- 3. Port-forward (chạy nền) ---
Write-Host "`n[3/5] Bat dau port-forward (PostgreSQL 5432, RabbitMQ 5672, Redis 6379)..." -ForegroundColor Yellow
Write-Host "Chay trong terminal RIENG, giu mo:" -ForegroundColor Gray
Write-Host ""
Write-Host "  kubectl port-forward svc/postgres-postgresql 5432:5432 -n default" -ForegroundColor White
Write-Host "  kubectl port-forward svc/rabbitmq 5672:5672 -n default" -ForegroundColor White
Write-Host "  kubectl port-forward svc/redis-master 6379:6379 -n default" -ForegroundColor White
Write-Host ""
Write-Host "Hoac chay 1 lenh (PowerShell):" -ForegroundColor Gray
Write-Host '  Start-Job { kubectl port-forward svc/postgres-postgresql 5432:5432 -n default }' -ForegroundColor White
Write-Host '  Start-Job { kubectl port-forward svc/rabbitmq 5672:5672 -n default }' -ForegroundColor White
Write-Host '  Start-Job { kubectl port-forward svc/redis-master 6379:6379 -n default }' -ForegroundColor White
Write-Host ""

# --- 4. Alembic migrations ---
Write-Host "[4/5] Chay Alembic migrations (neu chua)..." -ForegroundColor Yellow
Push-Location $ProjectRoot
# $env:DATABASE_URL = "postgresql://user:password@127.0.0.1:5432/db"
alembic upgrade head 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Loi migrations. Dam bao port-forward PostgreSQL dang chay." -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location
Write-Host "Migrations OK" -ForegroundColor Green

# --- 5. Hướng dẫn chạy services ---
Write-Host "`n[5/5] Chay Market Data Service va Collectors:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Terminal 2 - Market Data Service (consumer, luu vao DB):" -ForegroundColor Cyan
Write-Host "  cd `"$ProjectRoot`"" -ForegroundColor White
Write-Host "  `$env:PYTHONPATH=`"$ProjectRoot`"" -ForegroundColor Gray
Write-Host "  pip install -r services/market-data-service/requirements.txt" -ForegroundColor Gray
Write-Host "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --app-dir services/market-data-service" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 3 - Collectors (thu thap Yahoo/Binance -> RabbitMQ):" -ForegroundColor Cyan
Write-Host "  cd `"$ProjectRoot\services\collectors`"" -ForegroundColor White
Write-Host "  pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "  python main.py" -ForegroundColor White
Write-Host ""
Write-Host "Collectors chay moi 60 giay 1 lan. Sau 2-3 phut kiem tra DB:" -ForegroundColor Gray
Write-Host "  python ml/scripts/run_dataset_builder.py --ticker AAPL -o ml/outputs/datasets" -ForegroundColor White
Write-Host ""
Write-Host "=== Hoan thanh huong dan ===" -ForegroundColor Green
