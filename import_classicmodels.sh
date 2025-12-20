#!/usr/bin/env bash
set -euo pipefail

# Usage: ./import_classicmodels.sh [mysql_user] [mysql_host] [mysql_port]
# Defaults: mysql_user=root, mysql_host=127.0.0.1, mysql_port=3306

DB=classicmodels
USER="${1:-root}"
HOST="${2:-127.0.0.1}"
PORT="${3:-3306}"

echo "This will create DB '$DB' on ${HOST}:${PORT} and import schema files. You will be prompted for MySQL password."
read -s -p "MySQL password: " PASS
echo
export MYSQL_PWD="$PASS"

# Drop any existing database first to ensure a clean import
mysql -h "$HOST" -P "$PORT" -u "$USER" --default-character-set=utf8mb4 \
  -e "DROP DATABASE IF EXISTS ${DB};" \
  || { echo "Failed to drop existing database ${DB}"; unset MYSQL_PWD; exit 1; }

# Create database with utf8mb4
mysql -h "$HOST" -P "$PORT" -u "$USER" --default-character-set=utf8mb4 \
  -e "CREATE DATABASE IF NOT EXISTS ${DB} CHARACTER SET utf8mb4 COLLATE=utf8mb4_general_ci;" \
  || { echo "Failed to create database ${DB}"; unset MYSQL_PWD; exit 1; }

# Import files in dependency order
ORDER_FILES=(
  tables/productlines.sql
  tables/products.sql
  tables/offices.sql
  tables/employees.sql
  tables/customers.sql
  tables/orders.sql
  tables/orderdetails.sql
  tables/payments.sql
  tables/employee_auth.sql
  tables/employee_reports.sql
  tables/customer_auth.sql
)

for f in "${ORDER_FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "Importing $f ..."
    mysql -h "$HOST" -P "$PORT" -u "$USER" --default-character-set=utf8mb4 "$DB" < "$f" \
      || { echo "Import failed at $f"; unset MYSQL_PWD; exit 2; }
  else
    echo "Warning: $f not found, skipping."
  fi
done

# Import any remaining .sql files in tables/ not listed above
for f in tables/*.sql; do
  # skip files already in ORDER_FILES
  skip=false
  for donef in "${ORDER_FILES[@]}"; do
    if [ "$f" = "$donef" ]; then
      skip=true
      break
    fi
  done
  if [ "$skip" = false ]; then
    echo "Importing extra $f ..."
    mysql -h "$HOST" -P "$PORT" -u "$USER" --default-character-set=utf8mb4 "$DB" < "$f" \
      || { echo "Import failed at extra $f"; unset MYSQL_PWD; exit 3; }
  fi
done

unset MYSQL_PWD
echo "Import finished."