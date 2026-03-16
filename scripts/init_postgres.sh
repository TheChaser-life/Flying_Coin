#!/bin/bash
# Script khởi tạo databases và users trong PostgreSQL (Bitnami chart)
# Chạy: bash scripts/init_postgres.sh
# Biến môi trường: .env hoặc POSTGRES_POD, POSTGRES_NAMESPACE, AIRFLOW_DB_USER, MLFLOW_DB_USER, MLFLOW_DB_PASSWORD, MARKET_DATA_DB

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Load .env
if [ -f .env ]; then
    set -a
    source <(sed 's/\r$//' .env)
    set +a
else
    echo "LỖI: Không tìm thấy .env"
    exit 1
fi

POSTGRES_PASSWORD=$(echo "$POSTGRES_PASSWORD" | tr -d '\r' | xargs)
AIRFLOW_DB_PASSWORD=$(echo "$AIRFLOW_DB_PASSWORD" | tr -d '\r' | xargs)
AIRFLOW_DB_USER="${AIRFLOW_DB_USER:-airflow}"
POSTGRES_NAMESPACE="${POSTGRES_NAMESPACE:-database}"
POSTGRES_POD="${POSTGRES_POD:-postgres-postgresql-primary-0}"
MARKET_DATA_DB="${MARKET_DATA_DB:-market_data}"

# Lấy password từ K8s secret (đồng bộ với Postgres) nếu có
SECRET_B64=$(kubectl get secret postgresql-credentials -n "$POSTGRES_NAMESPACE" -o jsonpath='{.data.postgres-password}' 2>/dev/null || true)
if [ -z "$SECRET_B64" ]; then
    SECRET_B64=$(kubectl get secret postgres-postgresql -n "$POSTGRES_NAMESPACE" -o jsonpath='{.data.postgres-password}' 2>/dev/null || true)
fi
if [ -n "$SECRET_B64" ]; then
    DECODED=$(echo "$SECRET_B64" | base64 -d 2>/dev/null || echo "$SECRET_B64" | base64 -D 2>/dev/null || true)
    [ -n "$DECODED" ] && POSTGRES_PASSWORD=$(echo "$DECODED" | tr -d '\r\n')
fi

# Parse MLflow credentials từ MLFLOW_BACKEND_URI hoặc .env
MLFLOW_DB_USER="${MLFLOW_DB_USER:-mlflow}"
MLFLOW_DB_PASSWORD="${MLFLOW_DB_PASSWORD:-mlflow_pass}"
if [[ "$MLFLOW_BACKEND_URI" =~ postgresql://([^:]+):([^@]+)@ ]]; then
    MLFLOW_DB_USER="${BASH_REMATCH[1]}"
    MLFLOW_DB_PASSWORD="${BASH_REMATCH[2]}"
fi

echo "=== Init PostgreSQL ==="
echo "Postgres pod: $POSTGRES_POD"
echo "Databases: airflow, mlflow, market_data, portfolio"

# Chờ Postgres Ready
echo "Đợi Postgres pod Ready..."
kubectl wait --for=condition=Ready "pod/$POSTGRES_POD" -n "$POSTGRES_NAMESPACE" --timeout=120s

run_sql() {
    PGPASSWORD="$POSTGRES_PASSWORD" kubectl exec -n "$POSTGRES_NAMESPACE" "$POSTGRES_POD" -c postgresql -- psql -U postgres -t -c "$1"
}

exec_sql() {
    PGPASSWORD="$POSTGRES_PASSWORD" kubectl exec -i -n "$POSTGRES_NAMESPACE" "$POSTGRES_POD" -c postgresql -- psql -U postgres -v ON_ERROR_STOP=1 <<EOSQL
$1
EOSQL
}

# Airflow — tạo user và database (idempotent)
echo "Tạo airflow user và database..."
exec_sql "
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='$AIRFLOW_DB_USER') THEN
    CREATE USER $AIRFLOW_DB_USER WITH PASSWORD '$AIRFLOW_DB_PASSWORD';
  END IF;
END \$\$;
"
run_sql "SELECT 1 FROM pg_database WHERE datname='airflow'" | grep -q 1 || exec_sql "CREATE DATABASE airflow OWNER $AIRFLOW_DB_USER;"
exec_sql "GRANT ALL PRIVILEGES ON DATABASE airflow TO $AIRFLOW_DB_USER;"
exec_sql "\c airflow
GRANT ALL ON SCHEMA public TO $AIRFLOW_DB_USER;
"

# MLflow — tạo user và database (idempotent), cập nhật password nếu user đã tồn tại
echo "Tạo mlflow user và database..."
exec_sql "
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='$MLFLOW_DB_USER') THEN
    CREATE USER $MLFLOW_DB_USER WITH PASSWORD '$MLFLOW_DB_PASSWORD';
  ELSE
    ALTER USER $MLFLOW_DB_USER WITH PASSWORD '$MLFLOW_DB_PASSWORD';
  END IF;
END \$\$;
"
run_sql "SELECT 1 FROM pg_database WHERE datname='mlflow'" | grep -q 1 || exec_sql "CREATE DATABASE mlflow OWNER $MLFLOW_DB_USER;"
exec_sql "GRANT ALL PRIVILEGES ON DATABASE mlflow TO $MLFLOW_DB_USER;"
exec_sql "\c mlflow
GRANT ALL ON SCHEMA public TO $MLFLOW_DB_USER;
"

# market_data — dùng postgres admin (postgres:POSTGRES_PASSWORD)
echo "Tạo market_data database..."
run_sql "SELECT 1 FROM pg_database WHERE datname='$MARKET_DATA_DB'" | grep -q 1 || exec_sql "CREATE DATABASE $MARKET_DATA_DB OWNER postgres;"
exec_sql "GRANT ALL PRIVILEGES ON DATABASE $MARKET_DATA_DB TO postgres;"

# portfolio — dùng postgres admin
echo "Tạo portfolio database..."
run_sql "SELECT 1 FROM pg_database WHERE datname='portfolio'" | grep -q 1 || exec_sql "CREATE DATABASE portfolio OWNER postgres;"
exec_sql "GRANT ALL PRIVILEGES ON DATABASE portfolio TO postgres;"

# Automated Table Creation (Schema)
echo "--- Khởi tạo Table Schema cho market_data ---"
POD=$(kubectl get pod -n dev -l app=market-data-service --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
if [ -n "$POD" ]; then
    echo "Chạy init_db qua pod $POD..."
    kubectl exec -n dev "$POD" -- python3 -c "
import asyncio
from app.core.database import engine
from shared.database.models import Base
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Database tables created/verified.')
asyncio.run(init_db())
"
else
    echo "CẢNH BÁO: Không tìm thấy pod market-data-service đang chạy để init tables. Bỏ qua bước này."
fi

echo "=== Init PostgreSQL xong ==="
echo "Databases: airflow, mlflow, market_data, portfolio"
