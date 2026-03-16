$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# Load .env
$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Error "Khong tim thay .env tai: $envFile"
    exit 1
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim().Trim('"')
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

# Lay password tu K8s secret (dong bo voi Postgres) thay vi .env
$POSTGRES_NAMESPACE = $env:POSTGRES_NAMESPACE
if (-not $POSTGRES_NAMESPACE) { $POSTGRES_NAMESPACE = "database" }
$secretB64 = kubectl get secret postgresql-credentials -n $POSTGRES_NAMESPACE -o jsonpath='{.data.postgres-password}' 2>$null
if (-not $secretB64) {
    $secretB64 = kubectl get secret postgres-postgresql -n $POSTGRES_NAMESPACE -o jsonpath='{.data.postgres-password}' 2>$null
}
if ($secretB64) {
    $POSTGRES_PASSWORD = ([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($secretB64))).Trim().TrimEnd("`r", "`n")
} else {
    $POSTGRES_PASSWORD = ($env:POSTGRES_PASSWORD -replace "`r", "" -replace "`n", "").Trim()
}
$AIRFLOW_DB_PASSWORD = ($env:AIRFLOW_DB_PASSWORD -replace "`r", "" -replace "`n", "").Trim()
$AIRFLOW_DB_USER = if ($env:AIRFLOW_DB_USER) { $env:AIRFLOW_DB_USER } else { "airflow" }
$MLFLOW_BACKEND_URI = $env:MLFLOW_BACKEND_URI

# Parse MLflow credentials tu MLFLOW_BACKEND_URI hoac .env
$MLFLOW_DB_USER = if ($env:MLFLOW_DB_USER) { $env:MLFLOW_DB_USER } else { "mlflow" }
$MLFLOW_DB_PASSWORD = if ($env:MLFLOW_DB_PASSWORD) { $env:MLFLOW_DB_PASSWORD } else { "mlflow_pass" }
if ($MLFLOW_BACKEND_URI -match 'postgresql://([^:]+):([^@]+)@') {
    $MLFLOW_DB_USER = $matches[1]
    $MLFLOW_DB_PASSWORD = $matches[2]
}

$POSTGRES_POD = if ($env:POSTGRES_POD) { $env:POSTGRES_POD } else { "postgres-postgresql-primary-0" }
$NAMESPACE = $POSTGRES_NAMESPACE

Write-Host "=== Init PostgreSQL ==="
Write-Host "Postgres pod: $POSTGRES_POD"
Write-Host "Databases: airflow, mlflow, market_data, portfolio"

Write-Host "Đợi Postgres pod Ready..."
kubectl wait --for=condition=Ready "pod/$POSTGRES_POD" -n $NAMESPACE --timeout=120s

# Truyen PGPASSWORD vao container qua env (kubectl exec khong tu dong pass env local)
function Run-Sql {
    param([string]$Sql)
    $Sql | kubectl exec -i -n $NAMESPACE $POSTGRES_POD -c postgresql -- env "PGPASSWORD=$POSTGRES_PASSWORD" psql -U postgres -v ON_ERROR_STOP=1
}

function Exec-Sql {
    param([string]$Sql)
    kubectl exec -n $NAMESPACE $POSTGRES_POD -c postgresql -- env "PGPASSWORD=$POSTGRES_PASSWORD" psql -U postgres -t -c $Sql
}

# Airflow — tạo user và database (idempotent)
Write-Host "Tạo airflow user và database..."
$airflowUserSql = @"
DO `$`$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='$AIRFLOW_DB_USER') THEN
    CREATE USER $AIRFLOW_DB_USER WITH PASSWORD '$AIRFLOW_DB_PASSWORD';
  END IF;
END `$`$;
"@
Run-Sql $airflowUserSql

$dbExists = Exec-Sql "SELECT 1 FROM pg_database WHERE datname='airflow'"
if (-not $dbExists) {
    Run-Sql "CREATE DATABASE airflow OWNER $AIRFLOW_DB_USER;"
}
Run-Sql "GRANT ALL PRIVILEGES ON DATABASE airflow TO $AIRFLOW_DB_USER;"
Run-Sql "`\c airflow`nGRANT ALL ON SCHEMA public TO $AIRFLOW_DB_USER;"

# MLflow — tạo user và database (idempotent), cập nhật password nếu user đã tồn tại
Write-Host "Tạo mlflow user và database..."
$mlflowUserSql = @"
DO `$`$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='$MLFLOW_DB_USER') THEN
    CREATE USER $MLFLOW_DB_USER WITH PASSWORD '$MLFLOW_DB_PASSWORD';
  ELSE
    ALTER USER $MLFLOW_DB_USER WITH PASSWORD '$MLFLOW_DB_PASSWORD';
  END IF;
END `$`$;
"@
Run-Sql $mlflowUserSql

$dbExists = Exec-Sql "SELECT 1 FROM pg_database WHERE datname='mlflow'"
if (-not $dbExists) {
    Run-Sql "CREATE DATABASE mlflow OWNER $MLFLOW_DB_USER;"
}
Run-Sql "GRANT ALL PRIVILEGES ON DATABASE mlflow TO $MLFLOW_DB_USER;"
Run-Sql "`\c mlflow`nGRANT ALL ON SCHEMA public TO $MLFLOW_DB_USER;"

# market_data — dùng postgres admin (postgres:POSTGRES_PASSWORD)
$MARKET_DATA_DB = if ($env:MARKET_DATA_DB) { $env:MARKET_DATA_DB } else { "market_data" }
Write-Host "Tạo market_data database..."
$dbExists = Exec-Sql "SELECT 1 FROM pg_database WHERE datname='$MARKET_DATA_DB'"
if (-not $dbExists) {
    Run-Sql "CREATE DATABASE $MARKET_DATA_DB OWNER postgres;"
}
Run-Sql "GRANT ALL PRIVILEGES ON DATABASE $MARKET_DATA_DB TO postgres;"

# portfolio — dùng postgres admin
Write-Host "Tạo portfolio database..."
$dbExists = Exec-Sql "SELECT 1 FROM pg_database WHERE datname='portfolio'"
if (-not $dbExists) {
    Run-Sql "CREATE DATABASE portfolio OWNER postgres;"
}
Run-Sql "GRANT ALL PRIVILEGES ON DATABASE portfolio TO postgres;"

# Automated Table Creation (Schema)
Write-Host "--- Khởi tạo Table Schema cho market_data ---"
# Thử tìm một pod bất kỳ có thể chạy SQLAlchemy init (market-data-service là tốt nhất)
$POD = kubectl get pod -n dev -l app=market-data-service --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>$null
if ($POD) {
    Write-Host "Chạy init_db qua pod $POD..."
    kubectl exec -n dev $POD -- python3 -c "
import asyncio
from app.core.database import engine
from shared.database.models import Base
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Database tables created/verified.')
asyncio.run(init_db())
"
} else {
    Write-Warning "Không tìm thấy pod market-data-service đang chạy để init tables. Bỏ qua bước này."
}

Write-Host "=== Init PostgreSQL xong ==="
Write-Host "Databases: airflow, mlflow, market_data, portfolio"
