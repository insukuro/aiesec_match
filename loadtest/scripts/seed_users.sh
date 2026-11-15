#!/usr/bin/env bash
# Создаёт N пользователей: register → consent → PUT profile.
# Сохраняет токены в loadtest/data/tokens.json.
set -euo pipefail

BASE="${BASE_URL:-http://localhost:8000}"
OUT="${1:-loadtest/data/tokens.json}"
N="${N:-50}"
EMAIL_DOMAIN="${EMAIL_DOMAIN:-loadtest.example.com}"   # ← FIX: валидный TLD

command -v jq >/dev/null || { echo "нужен jq: apt install jq / brew install jq" >&2; exit 1; }

mkdir -p "$(dirname "$OUT")"
echo "[" > "$OUT"

ok=0; fail=0
for i in $(seq 1 "$N"); do
  EMAIL="loadtest+${i}@${EMAIL_DOMAIN}"
  PASS="TestPass123"

  REG_CODE=$(curl -s -o /tmp/reg.json -w '%{http_code}' -X POST "$BASE/api/v1/auth/register" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")

  TOK=""
  if [ "$REG_CODE" = "200" ] || [ "$REG_CODE" = "201" ]; then
    TOK=$(jq -r '.access_token // empty' /tmp/reg.json)
  else
    # fallback: login (Content-Type обязателен!)
    LOG=$(curl -s -X POST "$BASE/api/v1/auth/login" \
      -H 'Content-Type: application/json' \
      -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")
    TOK=$(echo "$LOG" | jq -r '.access_token // empty')
  fi

  if [ -z "$TOK" ] || [ "$TOK" = "null" ]; then
    echo "  ✗ $EMAIL — нет токена (register=$REG_CODE)" >&2
    [ -s /tmp/reg.json ] && echo "    register body: $(cat /tmp/reg.json)" >&2
    fail=$((fail+1)); continue
  fi

  # ← FIX: consent обязателен перед PUT /profiles/me
  CONSENT_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/v1/me/consents" \
    -H "Authorization: Bearer $TOK" \
    -H 'Content-Type: application/json' \
    -d '{"kind":"pd_processing","version":"v1"}')

  if [ "$CONSENT_CODE" != "204" ] && [ "$CONSENT_CODE" != "200" ]; then
    echo "  ✗ $EMAIL — consent вернул $CONSENT_CODE" >&2
    fail=$((fail+1)); continue
  fi

  # ← FIX: birth_date обязателен для ProfileIn
  PUT_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X PUT "$BASE/api/v1/profiles/me" \
    -H "Authorization: Bearer $TOK" \
    -H 'Content-Type: application/json' \
    -d '{
  "programmes": ["volunteer"],
  "english_level": "B2",
  "spheres": ["marketing"],
  "desired_countries": ["PL"],
  "duration": {"min_weeks": 6, "max_weeks": 12},
  "birth_date": "2000-01-01",
  "study": {"status": "bachelor"}
}')

  if [ "$PUT_CODE" -ge 400 ] 2>/dev/null; then
    echo "  ✗ $EMAIL — PUT профиля вернул $PUT_CODE" >&2
    fail=$((fail+1)); continue
  fi

  # ← FIX: проверяем, что профиль реально создан
  PROFILE_CODE=$(curl -s -o /dev/null -w '%{http_code}' \
    -H "Authorization: Bearer $TOK" "$BASE/api/v1/profiles/me")
  if [ "$PROFILE_CODE" != "200" ]; then
    echo "  ✗ $EMAIL — GET профиля вернул $PROFILE_CODE" >&2
    fail=$((fail+1)); continue
  fi

  [ "$ok" -gt 0 ] && echo "," >> "$OUT"
  printf '{"token":"%s","email":"%s"}' "$TOK" "$EMAIL" >> "$OUT"
  ok=$((ok+1))
done

echo "]" >> "$OUT"
echo "✓ seeded: $ok, failed: $fail → $OUT"