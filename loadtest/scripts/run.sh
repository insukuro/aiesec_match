#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
umask 077

test_case=${1:-NT01}
case "$test_case" in
  NT01) users=${2:-1}; hold=${3:-600}; [[ "$users" == 1 ]] ;;
  NT02) users=${2:-10}; hold=${3:-600}; [[ "$users" == 10 ]] ;;
  NT03) users=${2:-15}; hold=${3:-180}; [[ "$users" == 15 || "$users" == 20 ]] ;;
  *) printf 'CASE должен быть NT01, NT02 или NT03\n' >&2; exit 2 ;;
esac || { printf 'Недопустимое число VU для %s\n' "$test_case" >&2; exit 2; }
if [[ ! "$hold" =~ ^[0-9]+$ ]] || (( 10#$hold < 60 )); then
  printf 'HOLD_SECONDS должен быть целым числом от 60\n' >&2
  exit 2
fi

compose=(docker compose -f loadtest/docker-compose.loadtest.yml)
"${compose[@]}" up -d --wait prometheus grafana
run_id="$(date -u +%Y%m%d-%H%M%S-%3N)-${test_case,,}-$users"
export RUN_DIR="$PWD/loadtest/results/runs/$run_id"
mkdir -p "$(dirname "$RUN_DIR")"
mkdir "$RUN_DIR"
dashboard="http://localhost:3000/d/aiesec-loadtest?var-run_id=$run_id"
if [[ "$test_case" == NT01 ]]; then
  printf 'НТ-01: один контрольный подбор. Для нагрузки: make loadtest CASE=NT02\n'
else
  printf '%s: разгон 60 с, плато %s с (%s VU), спад 30 с.\n' "$test_case" "$hold" "$users"
fi
printf 'Мониторинг во время теста: %s&var-phase=.*&from=now-15m&to=now&refresh=5s\n' "$dashboard"
printf 'RUN_ID=%s\nCASE=%s\nUSERS=%s\nHOLD_SECONDS=%s\n' \
  "$run_id" "$test_case" "$users" "$hold" > "$RUN_DIR/parameters.txt"
git rev-parse HEAD > "$RUN_DIR/commit.txt"
sha256sum loadtest/k6/recommendations.js loadtest/scripts/recommendation_report.py > "$RUN_DIR/scenario.sha256"

before_ms=$(date +%s%3N)
status=0
"${compose[@]}" run --rm --user "$(id -u):$(id -g)" \
  -e RUN_ID="$run_id" -e TEST_CASE="$test_case" -e USERS="$users" -e HOLD_SECONDS="$hold" \
  k6 run --out experimental-prometheus-rw --out json=/results/raw.ndjson \
  --summary-export=/results/summary.json /scripts/recommendations.js \
  2>&1 | tee "$RUN_DIR/k6.log" || status=$?
after_ms=$(date +%s%3N)

report_args=(--run-id "$run_id")
start_ms="$(sed -nE 's/.*scenario_start_ms=([0-9]+).*/\1/p' "$RUN_DIR/k6.log" | sort -u)"
# Оставляем контекст для шага графиков и финальной отправки remote write.
printf '%s&var-phase=.*&from=%s&to=%s\n' "$dashboard" "$(( ${start_ms:-$before_ms} - 30000 ))" "$((after_ms + 30000))" \
  | tee "$RUN_DIR/grafana-url.txt"
printf 'Результаты: %s\n' "$RUN_DIR"
if (( status != 0 )); then
  exit "$status"
fi
if [[ "$test_case" != NT01 ]]; then
  [[ "$start_ms" =~ ^[0-9]+$ ]] || { printf 'В журнале отсутствует единый T0\n' >&2; exit 1; }
  plateau_from=$((start_ms + 60000))
  plateau_to=$((plateau_from + 10#$hold * 1000))
  printf 'PLATEAU_FROM_MS=%s\nPLATEAU_TO_MS=%s\n' "$plateau_from" "$plateau_to" >> "$RUN_DIR/parameters.txt"
  printf '%s&var-phase=plateau&from=%s&to=%s\n' "$dashboard" "$plateau_from" "$plateau_to" \
    | tee "$RUN_DIR/grafana-plateau-url.txt"
  report_args+=(--start-ms "$start_ms" --hold "$hold")
fi
python3 loadtest/scripts/recommendation_report.py "$RUN_DIR/raw.ndjson" "${report_args[@]}" \
  | tee "$RUN_DIR/plateau-report.json"
