#!/usr/bin/env bash
# Использование: ./summarize.sh loadtest/results/matcher-baseline.json
set -euo pipefail
FILE="${1:?usage: summarize.sh <summary.json>}"
command -v jq >/dev/null || { echo "нужен jq" >&2; exit 1; }
[ -f "$FILE" ] || { echo "нет файла: $FILE" >&2; exit 1; }

# k6 в --summary-export пишет миллисекунды (не секунды).
# Поэтому fmt() НЕ умножает на 1000 — иначе получаем 26572ms вместо 26.57ms.
FMT='def fmt(n): if n == null then "-" else (n|floor|tostring + "ms") end;'

echo "=== $(basename "$FILE") ==="

# --- per-endpoint (если k6 всё-таки положил тегированные метрики) ---
PER_EP=$(jq -r "$FMT"'
  def row(name; obj):
    [name, fmt(obj.avg), fmt(obj."p(90)"), fmt(obj."p(95)"), fmt(obj."p(99)"), fmt(obj.max)]
    | @tsv;
  [["endpoint","avg","p90","p95","p99","max"] | @tsv] +
  ([.metrics | to_entries[]
    | select(.key | startswith("http_req_duration{"))
    | .key as $k
    | (try ($k | capture("ep:(?<ep>[a-z_]+)").ep) catch null) as $ep
    | select($ep != null)
    | row($ep; .value)] | unique_by(.[0]))
  | .[]
' "$FILE" 2>/dev/null || true)

if [ -n "$PER_EP" ]; then
  echo "$PER_EP" | column -t -s $'\t'
else
  echo "(per-endpoint метрик нет — k6 --summary-export не включает тегированные"
  echo " под-метрики. Для разбивки по эндпоинтам используйте --out csv=/results/raw.csv"
  echo " и парсите его, либо смотрите консольный вывод k6.)"
fi

echo
echo "--- overall ---"
jq -r "$FMT"'
  "http_req_duration : avg=\(fmt(.metrics.http_req_duration.avg))  med=\(fmt(.metrics.http_req_duration.med // .metrics.http_req_duration."p(50)"))  p95=\(fmt(.metrics.http_req_duration."p(95)")) p99=\(fmt(.metrics.http_req_duration."p(99)" // "-"))  max=\(fmt(.metrics.http_req_duration.max))",
  "http_req_failed   : \((.metrics.http_req_failed.value // 0) * 100 | tostring)%",
  "http_reqs (total) : \(.metrics.http_reqs.count // 0)",
  "http_reqs (rps)   : \((.metrics.http_reqs.rate // 0) * 100 | floor / 100 | tostring)",
  "checks            : \((.metrics.checks.value // .metrics.checks.rate // 0) * 100 | tostring)%"
' "$FILE"