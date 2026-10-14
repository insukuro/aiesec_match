#!/usr/bin/env bash
# Сквозная проверка поднятого стека (docker compose up). Ничего не меняет, кроме запуска sync.
#   PARSER_URL=http://127.0.0.1:8001 PARSER_API_KEY=... ./scripts/smoke.sh
set -u
URL="${PARSER_URL:-http://127.0.0.1:8001}"
KEY="${PARSER_API_KEY:-}"
FAIL=0

get()  { curl -s -m 30 -H "X-API-Key: $KEY" "$URL$1"; }
code() { curl -s -m 30 -o /dev/null -w '%{http_code}' "${@:2}" "$URL$1"; }
py()   { python3 -c "import sys,json; d=json.load(sys.stdin); print($1)"; }
check() { # check "описание" "ожидаемое" "фактическое"
  if [ "$2" = "$3" ]; then echo "  ok   $1"; else echo "  FAIL $1 (ожидали '$2', получили '$3')"; FAIL=1; fi
}

echo "1. Живость и авторизация"
check "/health без ключа = 200" 200 "$(code /health)"
check "/opportunities без ключа = 401" 401 "$(code /opportunities)"
check "/opportunities с ключом = 200" 200 "$(code /opportunities -H "X-API-Key: $KEY")"

echo "2. Схема AIESEC (фильтры, на которые мы опираемся)"
SCHEMA="$(get /admin/schema/filters)"
for f in home_mcs committee_scope programmes status; do
  check "фильтр $f есть" True "$(echo "$SCHEMA" | py "'$f' in d['filters']")"
done
echo "  info incremental_filter_ok = $(echo "$SCHEMA" | py "d['incremental_filter_ok']")"

echo "3. Первичная загрузка"
TOTAL="$(get /opportunities/stats | py "d['open_total']")"
check "в базе есть открытые стажировки (>0)" True "$([ "${TOTAL:-0}" -gt 0 ] && echo True || echo False)"
echo "  info open_total = $TOTAL"
get /opportunities/stats | py "'\n'.join(f'  info {k}: {v}' for k, v in d['countries'].items())"

echo "4. Последний запуск синка"
LAST="$(get '/sync/runs?limit=1')"
echo "  info $(echo "$LAST" | py "d[0]['kind'], d[0]['status'], d[0]['stats']")"
check "последний sync не упал" ok "$(echo "$LAST" | py "d[0]['status']")"

echo "5. Карточка и точечный refresh"
ID="$(get '/opportunities?limit=1' | py "d['items'][0]['opportunity_id']")"
check "карточка $ID отдаёт raw" True "$(get "/opportunities/$ID" | py "bool(d['raw'])")"
echo "  info refresh $ID -> $(curl -s -m 30 -X POST -H "X-API-Key: $KEY" "$URL/opportunities/$ID/refresh" | py "d.get('result', d)")"

echo "6. Конкурентный запуск не плодит синки"
code /sync/reconcile -X POST -H "X-API-Key: $KEY" >/dev/null
check "второй запуск во время первого = 409" 409 "$(code /sync/reconcile -X POST -H "X-API-Key: $KEY")"

echo
[ $FAIL -eq 0 ] && echo "SMOKE OK" || { echo "SMOKE FAILED"; exit 1; }