#!/bin/sh
# Выполняется один раз при первом создании тома. Для нового сервиса добавьте строку create_db.
set -e

create_db() {
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres \
    -tc "SELECT 1 FROM pg_database WHERE datname = '$1'" | grep -q 1 \
    || psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"$1\""
}

create_db "${PARSER_DB:-parser}"