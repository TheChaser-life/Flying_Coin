#!/bin/bash
# Tạo các secret cần thiết trong GCP Secret Manager cho External Secrets Operator
# Chạy: ./scripts/create-gcp-secrets.sh
# Yêu cầu: gcloud CLI đã login và có quyền secretmanager.admin
# Biến môi trường: .env (RABBITMQ_URL, REDIS_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, MARKET_DATA_DB)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Load .env
if [ -f .env ]; then
    set -a
    source <(sed 's/\r$//' .env)
    set +a
fi

PROJECT_ID="${GCP_PROJECT_ID:-${PROJECT_ID:-flying-coin-489803}}"
RABBITMQ_URL="${RABBITMQ_URL:-amqp://admin:${RABBITMQ_PASSWORD}@rabbitmq.database.svc.cluster.local:5672/}"
REDIS_URL="${REDIS_URL:-redis://redis-service.database.svc.cluster.local:6379/0}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD=$(echo "${POSTGRES_PASSWORD:-postgres}" | tr -d '\r' | xargs)
POSTGRES_HOST="${POSTGRES_HOST:-postgres-postgresql-primary.database.svc.cluster.local}"
MARKET_DATA_DB="${MARKET_DATA_DB:-market_data}"
MARKET_DATA_DB_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5432/${MARKET_DATA_DB}"

echo "=== Tạo secrets trong GCP Secret Manager (project: $PROJECT_ID) ==="

# 0. rabbitmq-password (cho RabbitMQ Helm chart - rabbitmq-credentials)
RABBITMQ_PASSWORD=$(echo "${RABBITMQ_PASSWORD:-rabbitmq}" | tr -d '\r' | xargs)
if ! gcloud secrets describe rabbitmq-password --project="$PROJECT_ID" 2>/dev/null; then
  echo "Tạo rabbitmq-password..."
  echo -n "$RABBITMQ_PASSWORD" | gcloud secrets create rabbitmq-password \
    --project="$PROJECT_ID" --replication-policy=automatic --data-file=-
  echo "  -> OK"
else
  echo "rabbitmq-password đã tồn tại (thêm version mới để cập nhật...)"
  echo -n "$RABBITMQ_PASSWORD" | gcloud secrets versions add rabbitmq-password \
    --project="$PROJECT_ID" --data-file=-
  echo "  -> Đã thêm version mới"
fi

# 1. rabbitmq-url
if ! gcloud secrets describe rabbitmq-url --project="$PROJECT_ID" 2>/dev/null; then
  echo "Tạo rabbitmq-url..."
  echo -n "$RABBITMQ_URL" | gcloud secrets create rabbitmq-url \
    --project="$PROJECT_ID" \
    --replication-policy=automatic \
    --data-file=-
  echo "  -> OK"
else
  echo "rabbitmq-url đã tồn tại"
fi

# 2. redis-url
if ! gcloud secrets describe redis-url --project="$PROJECT_ID" 2>/dev/null; then
  echo "Tạo redis-url..."
  echo -n "$REDIS_URL" | gcloud secrets create redis-url \
    --project="$PROJECT_ID" \
    --replication-policy=automatic \
    --data-file=-
  echo "  -> OK"
else
  echo "redis-url đã tồn tại"
fi

# 3. market-data-db-url
if ! gcloud secrets describe market-data-db-url --project="$PROJECT_ID" 2>/dev/null; then
  echo "Tạo market-data-db-url..."
  echo -n "$MARKET_DATA_DB_URL" | gcloud secrets create market-data-db-url \
    --project="$PROJECT_ID" \
    --replication-policy=automatic \
    --data-file=-
  echo "  -> OK"
else
  echo "market-data-db-url đã tồn tại"
fi

echo ""
echo "=== Hoàn tất ==="
echo "Chạy 'kubectl get externalsecret -n dev' để kiểm tra sync status"
echo "Sau khi sync thành công: kubectl rollout restart deployment -n dev"
