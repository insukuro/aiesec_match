#!/bin/sh
# Выполняется ОДИН РАЗ при первом создании volume.
# Только создание единой БД приложения. Роли/схемы — в db-init (bootstrap.sql), он идемпотентен.
set -e

create_db() {
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres \
    -tc "SELECT 1 FROM pg_database WHERE datname = '$1'" | grep -q 1 \
    || psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"$1\""
}

create_db "${APP_DB:-aiesec_match}"