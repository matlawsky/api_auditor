#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
    --set=app_password="$DB_PASSWORD" <<'SQL'
CREATE ROLE monitor LOGIN PASSWORD :'app_password';
CREATE DATABASE monitor OWNER monitor;
SQL