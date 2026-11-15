#!/usr/bin/env bash
# Три прогона подряд: 10, 50 и 100 пользователей. Результаты складываются в out/.
# После адреса перечисляются сервисы, за ресурсами которых следим: имена контейнеров или порты.
#   ./run_load.sh matcher http://127.0.0.1:8002 aiesec-matcher-dev aiesec-postgres-dev
#   ./run_load.sh backend http://127.0.0.1:8000 aiesec-backend-dev aiesec-matcher-dev aiesec-postgres-dev
# Метка и список прогонов задаются переменными: TAG=_cache USERS_LIST="100" ./run_load.sh matcher ...
set -euo pipefail
NAME=$1; HOST=$2; shift 2; PORTS="$*"
TAG=${TAG:-}                       # метка прогона, например TAG=_cache
mkdir -p out
for U in ${USERS_LIST:-10 50 100}; do
  echo "=== $NAME: $U пользователей ==="
  python monitor.py "out/${NAME}${TAG}_u${U}_resources.csv" $PORTS &
  MON=$!
  USERS=$U locust -f "locustfile_${NAME}.py" --headless --host "$HOST" \
      --csv "out/${NAME}${TAG}_u${U}" --html "out/${NAME}${TAG}_u${U}.html" --only-summary || true
  kill $MON 2>/dev/null || true
  sleep 5                          # пауза, чтобы сервис «остыл» между прогонами
done
