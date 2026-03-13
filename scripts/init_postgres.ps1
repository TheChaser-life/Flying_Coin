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
$secretB64 = kubectl get secret postgresql-credentials -n database -o jsonpath='{.data.postgres-password}' 2>$null
if (-not $secretB64) {
    $secretB64 = kubectl get secret postgres-postgresql -n database -o jsonpath='{.data.postgres-password}' 2>$null
}
if ($secretB64) {
    $POSTGRES_PASSWORD = ([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($secretB64))).Trim().TrimEnd("`r", "`n")
} else {
    $POSTGRES_PASSWORD = ($env:POSTGRES_PASSWORD -replace "`r", "" -replace "`n", "").Trim()
}
$AIRFLOW_DB_PASSWORD = ($env:AIRFLOW_DB_PASSWORD -replace "`r", "" -replace "`n", "").Trim()
$MLFLOW_BACKEND_URI = $env:MLFLOW_BACKEND_URI

# Parse MLflow credentials
$MLFLOW_DB_USER = "mlflow"
$MLFLOW_DB_PASSWORD = "mlflow_pass"
if ($MLFLOW_BACKEND_URI -match 'postgresql://([^:]+):([^@]+)@') {
    $MLFLOW_DB_USER = $matches[1]
    $MLFLOW_DB_PASSWORD = $matches[2]
}

$POSTGRES_POD = "postgres-postgresql-primary-0"
$NAMESPACE = "database"

Write-Host "=== Init PostgreSQL ==="
Write-Host "Postgres pod: $POSTGRES_POD"
Write-Host "Databases: airflow, mlflow"

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

# Airflow
Write-Host "Tạo airflow user và database..."
$airflowUserSql = @"
DO `$`$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='airflow') THEN
    CREATE USER airflow WITH PASSWORD '$AIRFLOW_DB_PASSWORD';
  END IF;
END `$`$;
"@
Run-Sql $airflowUserSql

$dbExists = Exec-Sql "SELECT 1 FROM pg_database WHERE datname='airflow'"
if (-not $dbExists) {
    Run-Sql "CREATE DATABASE airflow OWNER airflow;"
}
Run-Sql "GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;"
Run-Sql "`\c airflow`nGRANT ALL ON SCHEMA public TO airflow;"

# MLflow
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

Write-Host "=== Init PostgreSQL xong ==="
Write-Host "Databases: airflow, mlflow"
