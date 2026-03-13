#!/bin/bash
# Script khởi tạo databases và users trong PostgreSQL (Bitnami chart)
# Chạy: bash scripts/init_postgres.sh

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

# Parse MLflow credentials từ MLFLOW_BACKEND_URI (format: postgresql://user:password@host/db)
MLFLOW_DB_USER="mlflow"
if [[ "$MLFLOW_BACKEND_URI" =~ postgresql://([^:]+):([^@]+)@ ]]; then
    MLFLOW_DB_USER="${BASH_REMATCH[1]}"
    MLFLOW_DB_PASSWORD="${BASH_REMATCH[2]}"
else
    MLFLOW_DB_PASSWORD="${MLFLOW_DB_PASSWORD:-mlflow_pass}"
fi

POSTGRES_POD="postgres-postgresql-primary-0"
NAMESPACE="database"

echo "=== Init PostgreSQL ==="
echo "Postgres pod: $POSTGRES_POD"
echo "Databases: airflow, mlflow"

# Chờ Postgres Ready
echo "Đợi Postgres pod Ready..."
kubectl wait --for=condition=Ready pod/$POSTGRES_POD -n $NAMESPACE --timeout=120s

run_sql() {
    PGPASSWORD="$POSTGRES_PASSWORD" kubectl exec -n $NAMESPACE $POSTGRES_POD -c postgresql -- psql -U postgres -t -c "$1"
}

exec_sql() {
    PGPASSWORD="$POSTGRES_PASSWORD" kubectl exec -i -n $NAMESPACE $POSTGRES_POD -c postgresql -- psql -U postgres -v ON_ERROR_STOP=1 <<EOSQL
$1
EOSQL
}

# Airflow — tạo user và database (idempotent)
echo "Tạo airflow user và database..."
exec_sql "
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='airflow') THEN
    CREATE USER airflow WITH PASSWORD '$AIRFLOW_DB_PASSWORD';
  END IF;
END \$\$;
"
run_sql "SELECT 1 FROM pg_database WHERE datname='airflow'" | grep -q 1 || exec_sql "CREATE DATABASE airflow OWNER airflow;"
exec_sql "GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;"
exec_sql "\c airflow
GRANT ALL ON SCHEMA public TO airflow;
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

echo "=== Init PostgreSQL xong ==="
echo "Databases: airflow, mlflow"
