$ErrorActionPreference = "Stop"

$ProjectRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
Set-Location $ProjectRoot

$LOG_FILE = "setup_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Start-Transcript -Path $LOG_FILE -Append

# 1. Load biến môi trường từ .env
$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Error "LỖI: Không tìm thấy file .env!"
    exit 1
}

Write-Host "--- Loading variables from .env ---"
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = ($matches[2].Trim().Trim('"') -replace "`r", "" -replace "`n", "").Trim()
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

$PROJECT_ID = ($env:PROJECT_ID -replace "`r", "" -replace "`n", "").Trim()
$REGION = ($env:REGION -replace "`r", "" -replace "`n", "").Trim()
$CLUSTER_NAME = ($env:CLUSTER_NAME -replace "`r", "" -replace "`n", "").Trim()

# 2. Kiểm tra các gcloud components cần thiết
Write-Host "--- 2. Checking required gcloud components ---"
$REQUIRED_COMPONENTS = @("kubectl", "gke-gcloud-auth-plugin")
foreach ($comp in $REQUIRED_COMPONENTS) {
    $installed = gcloud components list --filter="id:$comp AND state.name:Installed" --format="value(id)" 2>$null
    if (-not $installed -or $installed -notmatch $comp) {
        Write-Error "LỖI: Component '$comp' chưa được cài đặt."
        Write-Host "Vui lòng chạy: gcloud components install $comp"
        exit 1
    }
}

Write-Host "=== GKE Setup started. Logging to: $LOG_FILE ==="

# 3. Authenticating with GCP
Write-Host "--- 3. Authenticating with GCP ---"

# Tạo secrets trong GCP Secret Manager
# AIRFLOW_SESSION_SECRET_KEY: nếu trống thì generate random
$airflowSessionKey = ($env:AIRFLOW_SESSION_SECRET_KEY -replace "`r", "" -replace "`n", "").Trim()
if ([string]::IsNullOrWhiteSpace($airflowSessionKey)) {
    $airflowSessionKey = -join ((1..64) | ForEach-Object { "{0:x2}" -f (Get-Random -Maximum 256) })
}
$airflowJwtKey = ($env:AIRFLOW_JWT_SECRET_KEY -replace "`r", "" -replace "`n", "").Trim()
if ([string]::IsNullOrWhiteSpace($airflowJwtKey)) {
    $airflowJwtKey = -join ((1..64) | ForEach-Object { "{0:x2}" -f (Get-Random -Maximum 256) })
}
$secrets = @(
    @{ Key = "postgres-password"; Value = $env:POSTGRES_PASSWORD },
    @{ Key = "redis-password"; Value = $env:REDIS_PASSWORD },
    @{ Key = "rabbitmq-password"; Value = $env:RABBITMQ_PASSWORD },
    @{ Key = "rabbitmq-erlang-cookie"; Value = $env:RABBITMQ_ERLANG_COOKIE },
    @{ Key = "airflow-db-password"; Value = $env:AIRFLOW_DB_PASSWORD },
    @{ Key = "airflow-admin-password"; Value = $env:AIRFLOW_ADMIN_PASSWORD },
    @{ Key = "airflow-session-secret-key"; Value = $airflowSessionKey },
    @{ Key = "airflow-jwt-secret-key"; Value = $airflowJwtKey },
    @{ Key = "mlflow-backend-uri"; Value = $env:MLFLOW_BACKEND_URI },
    @{ Key = "keycloak-jwt-credential"; Value = $env:KEYCLOAK_JWT_CREDENTIAL }
)

$tempSecret = Join-Path $env:TEMP "gcloud_secret_$(Get-Random).txt"
foreach ($s in $secrets) {
    $val = ($s.Value -replace "`r", "" -replace "`n", "").Trim()
    gcloud secrets create $s.Key --replication-policy=automatic --project=$PROJECT_ID 2>$null
    [System.IO.File]::WriteAllText($tempSecret, $val)
    Get-Content $tempSecret -Raw | gcloud secrets versions add $s.Key --data-file=- --project=$PROJECT_ID
}
Remove-Item $tempSecret -ErrorAction SilentlyContinue

gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add apache-airflow https://airflow.apache.org
helm repo add kong https://charts.konghq.com
helm repo update

# Apply ClusterSecretStore + ExternalSecrets TRƯỚC để tạo các secret
Write-Host "Apply ClusterSecretStore + ExternalSecrets..."
kubectl apply -k k8s/overlays/dev-gcp/external-secrets/
Write-Host "Đợi ESO sync secrets (postgresql-credentials, redis-credentials, rabbitmq-credentials, rabbitmq-erlang-secret, airflow-secrets)..."
$esList = @("sync-postgres-credentials", "sync-redis-credentials", "sync-rabbitmq-credentials", "sync-rabbitmq-erlang-secret")
foreach ($es in $esList) {
    kubectl wait --for=condition=SecretSynced "externalsecret/$es" -n database --timeout=120s 2>$null
}
# Chờ airflow-secrets trong mlops — tránh CreateContainerConfigError khi Helm install Airflow
kubectl wait --for=condition=SecretSynced externalsecret/airflow-secrets -n mlops --timeout=120s 2>$null
Start-Sleep -Seconds 5

helm upgrade --install postgres bitnami/postgresql -f helm_values/postgres/postgres-gcp.yaml -n database --create-namespace

# Init databases (airflow, mlflow) — chạy sau khi Postgres Ready
if (Test-Path "scripts/init_postgres.ps1") {
    Write-Host "--- Init PostgreSQL (airflow, mlflow) ---"
    & ".\scripts\init_postgres.ps1"
}

helm upgrade --install redis bitnami/redis -f helm_values/redis/redis-gcp.yaml -n database --create-namespace
helm upgrade --install rabbitmq bitnami/rabbitmq -f helm_values/rabbitmq/rabbitmq-gcp.yaml -n database --create-namespace
helm upgrade --install airflow apache-airflow/airflow -f helm_values/airflow/airflow-gcp.yaml -n mlops --create-namespace
helm upgrade --install kong kong/kong -f helm_values/kong/kong-gcp.yaml -n kong --create-namespace

# Apply toàn bộ overlay (api-gateway, collectors, services...)
kubectl apply -k k8s/overlays/dev-gcp/

kubectl get pods -A

Stop-Transcript
