#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
umask 077
mkdir -p loadtest/results/runs
ARTIFACTS="$(mktemp -d "$PWD/loadtest/results/runs/catalog.XXXXXXXX")"
export MATCHER_CATALOG_SOURCE=db PARSER_SCHEDULER_ENABLED=false
export AIESEC_TOKEN= AIESEC_REFRESH_TOKEN=
export CATALOG_SIZE=1000

git branch --show-current > "$ARTIFACTS/branch.txt"
git rev-parse HEAD > "$ARTIFACTS/commit.txt"
git status --short > "$ARTIFACTS/git-status.txt"
sha256sum docker-compose.yml loadtest/k6/recommendations.js \
  loadtest/scripts/recommendation_report.py qa/catalog_data.py > "$ARTIFACTS/input.sha256"
docker version > "$ARTIFACTS/docker-version.txt"
docker compose version > "$ARTIFACTS/compose-version.txt"
docker run --rm grafana/k6:0.54.0 version > "$ARTIFACTS/k6-version.txt"
docker compose up -d --build --wait postgres parser backend matcher
# В проекте могут остаться контейнеры из docker-compose.test.yml с удалёнными
# образами. Собираем паспорт только сервисов текущего стенда.
docker compose images postgres db-init parser backend matcher > "$ARTIFACTS/images.txt"
docker compose ps postgres db-init parser backend matcher > "$ARTIFACTS/compose-ps.txt"

# Каталог в чистой БД. Код генерации берётся из репозитория.
{
  cat qa/catalog_data.py
  cat <<'PY'
import os
import psycopg

dsn = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
size = int(os.environ["CATALOG_SIZE"])
with psycopg.connect(dsn) as connection:
    if connection.execute("SELECT count(*) FROM parser.opportunities").fetchone()[0]:
        raise SystemExit("Use a clean test catalog")
    rng = random.Random(42)
    insert_rows(connection, [random_row(8000000 + i, rng) for i in range(size)])
    summary = connection.execute("""
        SELECT programme_kind, count(*) AS total,
               count(*) FILTER (WHERE is_open) AS open,
               count(*) FILTER (WHERE is_open AND available_openings > 0
                    AND (applications_close_date IS NULL OR applications_close_date >= CURRENT_DATE)) AS eligible
        FROM catalog.opportunity_v1 GROUP BY programme_kind ORDER BY programme_kind
    """).fetchall()
    print("DB date/zone:", connection.execute("SELECT CURRENT_DATE, current_setting('TimeZone')").fetchone())
    print("kind/total/open/eligible:", summary)
    print("requirement rows:", connection.execute(
        "SELECT count(*) FROM catalog.opportunity_requirement_v1"
    ).fetchone()[0])
PY
} | docker compose exec -T -e CATALOG_SIZE="$CATALOG_SIZE" parser python - \
  | tee "$ARTIFACTS/catalog-counts.txt"

docker compose exec -T postgres sh -ec \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$APP_DB" --data-only -t parser.opportunities' \
  > "$ARTIFACTS/catalog.sql"
sha256sum "$ARTIFACTS/catalog.sql" > "$ARTIFACTS/catalog.sha256"
printf 'Каталог и паспорт: %s\n' "$ARTIFACTS"
