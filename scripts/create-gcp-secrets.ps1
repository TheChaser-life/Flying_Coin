# Tạo các secret cần thiết trong GCP Secret Manager cho External Secrets Operator
# Chạy: .\scripts\create-gcp-secrets.ps1
# Yêu cầu: gcloud CLI đã login và có quyền secretmanager.admin
# Biến môi trường: .env (RABBITMQ_URL, REDIS_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, MARKET_DATA_DB)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# Load .env
$envFile = Join-Path $ProjectRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"')
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } elseif ($env:PROJECT_ID) { $env:PROJECT_ID } else { "flying-coin-489803" }
$RABBITMQ_URL = $env:RABBITMQ_URL
if (-not $RABBITMQ_URL) { $RABBITMQ_URL = "amqp://admin:$($env:RABBITMQ_PASSWORD)@rabbitmq.database.svc.cluster.local:5672/" }
$REDIS_URL = $env:REDIS_URL
if (-not $REDIS_URL) { $REDIS_URL = "redis://redis-service.database.svc.cluster.local:6379/0" }
$POSTGRES_USER = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "postgres" }
$POSTGRES_PASSWORD = ($env:POSTGRES_PASSWORD -replace "`r", "" -replace "`n", "").Trim()
if (-not $POSTGRES_PASSWORD) { $POSTGRES_PASSWORD = "postgres" }
$POSTGRES_HOST = if ($env:POSTGRES_HOST) { $env:POSTGRES_HOST } else { "postgres-postgresql-primary.database.svc.cluster.local" }
$MARKET_DATA_DB = if ($env:MARKET_DATA_DB) { $env:MARKET_DATA_DB } else { "market_data" }
$MARKET_DATA_DB_URL = "postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5432/${MARKET_DATA_DB}"

Write-Host "=== Tạo secrets trong GCP Secret Manager (project: $PROJECT_ID) ===" -ForegroundColor Cyan

function Test-SecretExists {
    param([string]$Name)
    gcloud secrets describe $Name --project=$PROJECT_ID 2>$null
    return $LASTEXITCODE -eq 0
}

# 0. rabbitmq-password (cho RabbitMQ Helm chart - rabbitmq-credentials)
$RABBITMQ_PASSWORD = ($env:RABBITMQ_PASSWORD -replace "`r", "" -replace "`n", "").Trim()
if (-not $RABBITMQ_PASSWORD) { $RABBITMQ_PASSWORD = "rabbitmq" }
if (-not (Test-SecretExists "rabbitmq-password")) {
    Write-Host "Tạo rabbitmq-password..."
    $RABBITMQ_PASSWORD | gcloud secrets create rabbitmq-password --project=$PROJECT_ID --replication-policy=automatic --data-file=-
    Write-Host "  -> OK" -ForegroundColor Green
} else {
    Write-Host "rabbitmq-password đã tồn tại (thêm version mới để cập nhật...)"
    $RABBITMQ_PASSWORD | gcloud secrets versions add rabbitmq-password --project=$PROJECT_ID --data-file=-
    Write-Host "  -> Đã thêm version mới" -ForegroundColor Green
}

# 1. rabbitmq-url
if (-not (Test-SecretExists "rabbitmq-url")) {
    Write-Host "Tạo rabbitmq-url..."
    $RABBITMQ_URL | gcloud secrets create rabbitmq-url --project=$PROJECT_ID --replication-policy=automatic --data-file=-
    Write-Host "  -> OK" -ForegroundColor Green
} else {
    Write-Host "rabbitmq-url đã tồn tại"
}

# 2. redis-url
if (-not (Test-SecretExists "redis-url")) {
    Write-Host "Tạo redis-url..."
    $REDIS_URL | gcloud secrets create redis-url --project=$PROJECT_ID --replication-policy=automatic --data-file=-
    Write-Host "  -> OK" -ForegroundColor Green
} else {
    Write-Host "redis-url đã tồn tại"
}

# 3. market-data-db-url
if (-not (Test-SecretExists "market-data-db-url")) {
    Write-Host "Tạo market-data-db-url..."
    $MARKET_DATA_DB_URL | gcloud secrets create market-data-db-url --project=$PROJECT_ID --replication-policy=automatic --data-file=-
    Write-Host "  -> OK" -ForegroundColor Green
} else {
    Write-Host "market-data-db-url đã tồn tại"
}

Write-Host ""
Write-Host "=== Hoàn tất ===" -ForegroundColor Cyan
Write-Host "Chạy 'kubectl get externalsecret -n dev' để kiểm tra sync status"
Write-Host "Sau khi sync thành công: kubectl rollout restart deployment -n dev"
