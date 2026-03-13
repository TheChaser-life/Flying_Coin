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

# 2. Kiểm tra các gcloud components cần thiết
echo "--- 2. Checking required gcloud components ---"
REQUIRED_COMPONENTS=("kubectl" "gke-gcloud-auth-plugin")
for comp in "${REQUIRED_COMPONENTS[@]}"; do
    if ! gcloud components list --filter="id:$comp AND state.name:Installed" --format="value(id)" | grep -q "$comp"; then
        echo "LỖI: Component '$comp' chưa được cài đặt."
        echo "Vui lòng chạy: gcloud components install $comp"
        echo "Nếu bạn dùng WSL và gcloud cài từ Windows, hãy chạy lệnh install trên Windows CMD với quyền Administrator."
        exit 1
    fi
done

echo "=== GKE Setup started. Logging to: $LOG_FILE ==="

# 3. Authenticating with GCP
echo "--- 3. Authenticating with GCP ---"

# Thêm --no-launch-browser nếu chạy trên WSL để lấy link manual
# LOGIN_FLAGS=""
# if grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null; then
#     LOGIN_FLAGS="--no-launch-browser"
# fi

# gcloud auth login $LOGIN_FLAGS --project=$PROJECT_ID
# gcloud auth application-default login $LOGIN_FLAGS --project=$PROJECT_ID

#cd terraform && terraform init && terraform apply && cd ..

gcloud secrets create postgres-password --replication-policy=automatic --project=$PROJECT_ID
echo -n "$POSTGRES_PASSWORD" | gcloud secrets versions add postgres-password --data-file=- --project=$PROJECT_ID

gcloud secrets create redis-password --replication-policy=automatic --project=$PROJECT_ID
echo -n "$REDIS_PASSWORD" | gcloud secrets versions add redis-password --data-file=- --project=$PROJECT_ID

gcloud secrets create rabbitmq-password --replication-policy=automatic --project=$PROJECT_ID
echo -n "$RABBITMQ_PASSWORD" | gcloud secrets versions add rabbitmq-password --data-file=- --project=$PROJECT_ID

gcloud secrets create rabbitmq-erlang-cookie --replication-policy=automatic --project=$PROJECT_ID 2>/dev/null || true
echo -n "$RABBITMQ_ERLANG_COOKIE" | gcloud secrets versions add rabbitmq-erlang-cookie --data-file=- --project=$PROJECT_ID

gcloud secrets create airflow-db-password --replication-policy=automatic --project=$PROJECT_ID
echo -n "$AIRFLOW_DB_PASSWORD" | gcloud secrets versions add airflow-db-password --data-file=- --project=$PROJECT_ID

gcloud secrets create airflow-admin-password --replication-policy=automatic --project=$PROJECT_ID
echo -n "$AIRFLOW_ADMIN_PASSWORD" | gcloud secrets versions add airflow-admin-password --data-file=- --project=$PROJECT_ID

# airflow-session-secret-key: apiSecretKey + webserverSecretKey (Flask session)
AIRFLOW_SESSION_KEY="${AIRFLOW_SESSION_SECRET_KEY:-$(openssl rand -hex 32)}"
gcloud secrets create airflow-session-secret-key --replication-policy=automatic --project=$PROJECT_ID 2>/dev/null || true
echo -n "$AIRFLOW_SESSION_KEY" | gcloud secrets versions add airflow-session-secret-key --data-file=- --project=$PROJECT_ID

# airflow-jwt-secret-key: jwtSecretName (API auth JWT)
AIRFLOW_JWT_KEY="${AIRFLOW_JWT_SECRET_KEY:-$(openssl rand -hex 32)}"
gcloud secrets create airflow-jwt-secret-key --replication-policy=automatic --project=$PROJECT_ID 2>/dev/null || true
echo -n "$AIRFLOW_JWT_KEY" | gcloud secrets versions add airflow-jwt-secret-key --data-file=- --project=$PROJECT_ID

gcloud secrets create mlflow-backend-uri --replication-policy=automatic --project=$PROJECT_ID
echo -n "$MLFLOW_BACKEND_URI" | gcloud secrets versions add mlflow-backend-uri --data-file=- --project=$PROJECT_ID

gcloud secrets create keycloak-jwt-credential --replication-policy=automatic --project=$PROJECT_ID
echo -n "$KEYCLOAK_JWT_CREDENTIAL" | gcloud secrets versions add keycloak-jwt-credential --data-file=- --project=$PROJECT_ID

gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add apache-airflow https://airflow.apache.org
helm repo add kong https://charts.konghq.com
helm repo update

# Apply ClusterSecretStore + ExternalSecrets TRƯỚC để tạo các secret
# (Postgres, Redis, RabbitMQ, Airflow Helm charts cần existingSecret)
kubectl apply -k k8s/overlays/dev-gcp/external-secrets/
echo "Đợi ESO sync secrets (postgresql-credentials, redis-credentials, rabbitmq-credentials, rabbitmq-erlang-secret, airflow-secrets)..."
for es in sync-postgres-credentials sync-redis-credentials sync-rabbitmq-credentials sync-rabbitmq-erlang-secret; do
  kubectl wait --for=condition=SecretSynced externalsecret/$es -n database --timeout=120s 2>/dev/null || true
done
kubectl wait --for=condition=SecretSynced externalsecret/airflow-secrets -n mlops --timeout=120s 2>/dev/null || true
sleep 5

helm upgrade --install postgres bitnami/postgresql -f helm_values/postgres/postgres-gcp.yaml -n database --create-namespace

# Init databases (airflow, mlflow) — chạy sau khi Postgres Ready
if [ -f scripts/init_postgres.sh ]; then
  echo "--- Init PostgreSQL (airflow, mlflow) ---"
  bash scripts/init_postgres.sh
fi

helm upgrade --install redis bitnami/redis -f helm_values/redis/redis-gcp.yaml -n database --create-namespace
helm upgrade --install rabbitmq bitnami/rabbitmq -f helm_values/rabbitmq/rabbitmq-gcp.yaml -n database --create-namespace
helm upgrade --install airflow apache-airflow/airflow -f helm_values/airflow/airflow-gcp.yaml -n mlops --create-namespace
helm upgrade --install kong kong/kong -f helm_values/kong/kong-gcp.yaml -n kong --create-namespace

# Apply toàn bộ overlay (api-gateway, collectors, services...) — Kong CRDs đã có
kubectl apply -k k8s/overlays/dev-gcp/

kubectl get pods -A
