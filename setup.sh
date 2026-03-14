#!/bin/bash

set -eo pipefail

LOG_FILE="setup_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -i "$LOG_FILE") 2>&1

# 1. Load biến môi trường từ .env
if [ -f .env ]; then
    echo "--- Loading variables from .env ---"
    # Sourcing và xóa ký tự \r (tránh lỗi CRLF trên WSL)
    set -a
    source <(sed 's/\r$//' .env)
    set +a
else
    echo "LỖI: Không tìm thấy file .env!"
    exit 1
fi

# Sanitize variables (xóa ký tự trắng dư thừa và \r)
PROJECT_ID=$(echo "$PROJECT_ID" | tr -d '\r' | xargs)
REGION=$(echo "$REGION" | tr -d '\r' | xargs)
CLUSTER_NAME=$(echo "$CLUSTER_NAME" | tr -d '\r' | xargs)

echo "=== GKE Setup started. Logging to: $LOG_FILE ==="

# 2. Infrastructure Setup (Terraform)
echo "--- 2. Checking/Creating Infrastructure with Terraform ---"
if [ -d terraform ]; then
    cd terraform
    echo "Running terraform init..."
    terraform init -input=false
    echo "Running terraform apply..."
    terraform apply -auto-approve -input=false
    cd ..
else
    echo "CẢNH BÁO: Thư mục terraform không tồn tại. Bỏ qua bước tạo hạ tầng."
fi

# 3. Kiểm tra các gcloud components cần thiết
echo "--- 3. Checking required gcloud components ---"

# 3. Authenticating with GCP
echo "--- 3. Authenticating with GCP ---"

# GKE credentials
gcloud container clusters get-credentials "$CLUSTER_NAME" --region "$REGION" --project "$PROJECT_ID"

# Synced list of secrets from setup.ps1
# Cần format lại một chút cho Bash
declare -A SECRETS_MAP=(
    ["postgres-password"]="$POSTGRES_PASSWORD"
    ["redis-password"]="$REDIS_PASSWORD"
    ["rabbitmq-password"]="$RABBITMQ_PASSWORD"
    ["rabbitmq-erlang-cookie"]="$RABBITMQ_ERLANG_COOKIE"
    ["airflow-db-password"]="$AIRFLOW_DB_PASSWORD"
    ["airflow-admin-password"]="$AIRFLOW_ADMIN_PASSWORD"
    ["mlflow-backend-uri"]="$MLFLOW_BACKEND_URI"
    ["keycloak-jwt-credential"]="$KEYCLOAK_JWT_CREDENTIAL"
    ["rabbitmq-url"]="$RABBITMQ_URL"
    ["redis-url"]="$REDIS_URL"
    ["newsapi-key"]="$NEWSAPI_KEY"
    ["market-data-db-url"]="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5432/${MARKET_DATA_DB}"
    ["kong-cloudflare-cert"]="$KONG_CLOUDFLARE_CERT"
    ["kong-cloudflare-key"]="$KONG_CLOUDFLARE_KEY"
)

# Airflow keys (nếu chưa có trong .env thì gen)
AIRFLOW_SESSION_KEY="${AIRFLOW_SESSION_SECRET_KEY:-$(openssl rand -hex 32)}"
AIRFLOW_JWT_KEY="${AIRFLOW_JWT_SECRET_KEY:-$(openssl rand -hex 32)}"
SECRETS_MAP["airflow-session-secret-key"]="$AIRFLOW_SESSION_KEY"
SECRETS_MAP["airflow-jwt-secret-key"]="$AIRFLOW_JWT_KEY"

for key in "${!SECRETS_MAP[@]}"; do
    val="${SECRETS_MAP[$key]}"
    if [ -z "$val" ]; then continue; fi
    
    echo "Syncing secret: $key ..."
    gcloud secrets create "$key" --replication-policy=automatic --project="$PROJECT_ID" 2>/dev/null || true
    echo -n "$val" | gcloud secrets versions add "$key" --data-file=- --project="$PROJECT_ID"
done

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add apache-airflow https://airflow.apache.org
helm repo add kong https://charts.konghq.com
helm repo update

# Apply ClusterSecretStore + ExternalSecrets TRƯỚC
kubectl apply -k k8s/overlays/dev-gcp/external-secrets/
# Đợi ESO sync secrets
for es in sync-postgres-credentials sync-redis-credentials sync-rabbitmq-credentials sync-rabbitmq-erlang-secret; do
  kubectl wait --for=condition=SecretSynced "externalsecret/$es" -n database --timeout=120s 2>/dev/null || true
done
kubectl wait --for=condition=SecretSynced externalsecret/cloudflare-origin-tls -n kong --timeout=120s 2>/dev/null || true
kubectl wait --for=condition=SecretSynced externalsecret/infra-credentials-sync -n default --timeout=120s 2>/dev/null || true
kubectl wait --for=condition=SecretSynced externalsecret/airflow-secrets -n mlops --timeout=120s 2>/dev/null || true
kubectl wait --for=condition=SecretSynced externalsecret/sync-keycloak-credentials -n auth --timeout=120s 2>/dev/null || true
kubectl wait --for=condition=SecretSynced externalsecret/sync-keycloak-postgres-credentials -n auth --timeout=120s 2>/dev/null || true
kubectl wait --for=condition=SecretSynced externalsecret/keycloak-tls-sync -n auth --timeout=120s 2>/dev/null || true

sleep 5

helm upgrade --install postgres bitnami/postgresql -f helm_values/postgres/postgres-gcp.yaml -n database --create-namespace

# Init databases (airflow, mlflow)
if [ -f scripts/init_postgres.sh ]; then
  echo "--- Init PostgreSQL (airflow, mlflow) ---"
  bash scripts/init_postgres.sh
fi

helm upgrade --install redis bitnami/redis -f helm_values/redis/redis-gcp.yaml -n database --create-namespace
helm upgrade --install rabbitmq bitnami/rabbitmq -f helm_values/rabbitmq/rabbitmq-gcp.yaml -n database --create-namespace
helm upgrade --install airflow apache-airflow/airflow -f helm_values/airflow/airflow-gcp.yaml -n mlops --create-namespace
helm upgrade --install kong kong/kong -f helm_values/kong/kong-gcp.yaml -n kong --create-namespace

# Apply toàn bộ overlay
kubectl apply -k k8s/overlays/dev-gcp/

echo "--- Post-setup cleanup and restarts ---"
echo "Restarting deployments in 'dev' namespace to pick up new secrets..."
kubectl rollout restart statefulset rabbitmq -n database
kubectl rollout restart deployment collectors-deployment -n dev
kubectl rollout restart deployment market-data-service-deployment -n dev
kubectl rollout restart deployment sentiment-service-deployment -n dev
kubectl rollout restart deployment forecast-service-deployment -n dev

echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available deployment/market-data-service-deployment -n dev --timeout=300s
kubectl wait --for=condition=available deployment/sentiment-service-deployment -n dev --timeout=300s

kubectl get pods -A
