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

# 4. Web Frontend Secrets
if ! gcloud secrets describe web-frontend-auth-secret --project="$PROJECT_ID" 2>/dev/null; then
  echo "Tạo web-frontend-auth-secret..."
  AUTH_SECRET=$(openssl rand -base64 32)
  echo -n "$AUTH_SECRET" | gcloud secrets create web-frontend-auth-secret \
    --project="$PROJECT_ID" --replication-policy=automatic --data-file=-
  echo "  -> OK"
else
  echo "web-frontend-auth-secret đã tồn tại"
fi

# 5. Keycloak Client Secret for Frontend
AUTH_KEYCLOAK_SECRET="${AUTH_KEYCLOAK_SECRET:-keycloak-secret-change-in-prod}"
if ! gcloud secrets describe web-frontend-keycloak-secret --project="$PROJECT_ID" 2>/dev/null; then
  echo "Tạo web-frontend-keycloak-secret..."
  echo -n "$AUTH_KEYCLOAK_SECRET" | gcloud secrets create web-frontend-keycloak-secret \
    --project="$PROJECT_ID" --replication-policy=automatic --data-file=-
  echo "  -> OK"
else
  echo "web-frontend-keycloak-secret đã tồn tại"
fi

# 6. Keycloak Client ID and Issuer
AUTH_KEYCLOAK_ID="${AUTH_KEYCLOAK_ID:-flying-coin-web}"
AUTH_KEYCLOAK_ISSUER="${AUTH_KEYCLOAK_ISSUER:-https://keycloak.thinhopsops.win/realms/flying-coin}"

if ! gcloud secrets describe web-frontend-keycloak-id --project="$PROJECT_ID" 2>/dev/null; then
  echo -n "$AUTH_KEYCLOAK_ID" | gcloud secrets create web-frontend-keycloak-id --project="$PROJECT_ID" --replication-policy=automatic --data-file=-
fi

if ! gcloud secrets describe web-frontend-keycloak-issuer --project="$PROJECT_ID" 2>/dev/null; then
  echo -n "$AUTH_KEYCLOAK_ISSUER" | gcloud secrets create web-frontend-keycloak-issuer --project="$PROJECT_ID" --replication-policy=automatic --data-file=-
fi

# 7. Web Frontend Public URL (AUTH_URL)
AUTH_URL="${AUTH_URL:-https://flying-coin.thinhopsops.win}"
if ! gcloud secrets describe web-frontend-url --project="$PROJECT_ID" 2>/dev/null; then
  echo "Tạo web-frontend-url..."
  echo -n "$AUTH_URL" | gcloud secrets create web-frontend-url \
    --project="$PROJECT_ID" --replication-policy=automatic --data-file=-
  echo "  -> OK"
else
  echo "web-frontend-url đã tồn tại"
fi

# 8. Kong JWT Credential (keycloak-jwt-credential) - BẮT BUỘC để Kong verify token từ Keycloak
# Kong dùng claim "iss" trong JWT để tra cứu credential. Trường "key" phải KHỚP CHÍNH XÁC với iss trong token.
echo ""
echo "=== Kong JWT Credential (keycloak-jwt-credential) ==="
KEYCLOAK_ISSUER="${AUTH_KEYCLOAK_ISSUER:-https://keycloak.thinhopsops.win/realms/flying-coin}"
echo "Lấy public key từ Keycloak realm: $KEYCLOAK_ISSUER"
REALM_JSON=$(curl -sf "${KEYCLOAK_ISSUER}" 2>/dev/null || echo "")
if [ -n "$REALM_JSON" ]; then
  PUBLIC_KEY_B64=$(echo "$REALM_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('public_key',''))" 2>/dev/null || echo "$REALM_JSON" | jq -r '.public_key // empty' 2>/dev/null)
  if [ -n "$PUBLIC_KEY_B64" ]; then
    JWT_CREDENTIAL_JSON=$(printf '{"algorithm":"RS256","key":"%s","rsa_public_key":"%s"}' "$KEYCLOAK_ISSUER" "$PUBLIC_KEY_B64")
    if ! gcloud secrets describe keycloak-jwt-credential --project="$PROJECT_ID" 2>/dev/null; then
      echo "Tạo keycloak-jwt-credential..."
      echo -n "$JWT_CREDENTIAL_JSON" | gcloud secrets create keycloak-jwt-credential \
        --project="$PROJECT_ID" --replication-policy=automatic --data-file=-
      echo "  -> OK"
    else
      echo "Cập nhật keycloak-jwt-credential (issuer phải khớp với JWT)..."
      echo -n "$JWT_CREDENTIAL_JSON" | gcloud secrets versions add keycloak-jwt-credential \
        --project="$PROJECT_ID" --data-file=-
      echo "  -> Đã thêm version mới"
    fi
  else
    echo "  CẢNH BÁO: Không lấy được public_key từ Keycloak. Tạo secret thủ công với JSON:"
    echo "  {\"algorithm\":\"RS256\",\"key\":\"$KEYCLOAK_ISSUER\",\"rsa_public_key\":\"<base64 từ Keycloak realm>\"}"
  fi
else
  echo "  CẢNH BÁO: Không kết nối được Keycloak tại $KEYCLOAK_ISSUER"
  echo "  Tạo keycloak-jwt-credential thủ công. Lấy public_key từ: curl $KEYCLOAK_ISSUER"
fi

echo ""
echo "=== Hoàn tất ==="
echo "Chạy 'kubectl get externalsecret -n dev' để kiểm tra sync status"
echo "Sau khi sync thành công: kubectl rollout restart deployment -n dev"
