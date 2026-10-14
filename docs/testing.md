# Тестирование aiesec-parser

Четыре уровня, от дешёвого к дорогому. Каждый следующий нужен, только если предыдущий зелёный.

| Уровень | Что проверяет | Команда | Сеть к AIESEC |
|---|---|---|---|
| 1. Авто (unit + API) | Вся логика синка и ручки на фейковом AIESEC | `make test` | нет |
| 2. Контракт (live) | Что AIESEC не сломал схему, на которую мы опираемся | `AIESEC_TOKEN=... make test-live` | ~4 запроса |
| 3. Smoke стека | Поднятый compose живой, данные есть, авторизация работает | `./scripts/smoke.sh` | да (штатный sync) |
| 4. Ручные сценарии | Поведение на реальных данных, сбои, восстановление | ниже | да |

## 0. Подготовка к ручным сценариям

```bash
cp .env.example .env          # заполнить AIESEC_TOKEN, PARSER_API_KEY, POSTGRES_PASSWORD
make up
export URL=http://127.0.0.1:8001 KEY=<PARSER_API_KEY>
alias api='curl -s -H "X-API-Key: $KEY"'
alias sql='docker compose exec -T postgres psql -U platform parser -c'
```

## 1. Автотесты: что покрыто

- **normalize**: `id` → `opportunity_id`, вложенные поля, `host_lc: null`, мусорные значения, «лёгкие» строки не затирают поля.
- **full**: берёт только целевые страны/города, отсеивает чужие, без мест, просроченные; идемпотентен; закрывает пропавшие.
- **Предохранители**: пустая выдача не закрывает 29 из 30; обрыв на середине выдачи не закрывает ничего.
- **incremental**: без первого full откатывается на full; шлёт `created.from = последний sync − 1 день`; тянет только новые; никогда ничего не закрывает; откат на full, если фильтра нет.
- **reconcile**: только лёгкие запросы; обновляет места; закрывает пропавшие и «без мест»; переоткрывает вернувшиеся; новые догружает по id или полным проходом; не затирает поля карточки.
- **Служебное**: expire без обращений к API; refresh одной стажировки; один синк за раз; упавший запуск пишется в историю и снимает блокировку.
- **API**: авторизация, фильтры (`country`, `city`, `q`, `closing_before`, `new_since`), пагинация, сортировка, stats, карточка, refresh (в т.ч. 501), триггеры синка, 409, админ-ручки.

## 2. Ручные сценарии

Формат: **действие → ожидаемый результат**.

### M1. Холодный старт
1. `docker compose down -v && make up && make logs`.
2. В логах: `full → countries …`, `full → turkey_lcs …`, номера страниц с паузами ≈0.7 с.
3. `api $URL/sync/runs | python3 -m json.tool` → первый запуск `kind=full`, `status=ok`, `stats.inserted > 0`.
4. `api $URL/opportunities/stats` → `open_total > 0`, ненулевые счётчики по странам; города Турции могут быть 0 (если открытых нет).

**Сверка с реальностью:** возьмите 3 любые стажировки из `api "$URL/opportunities?limit=3"` и откройте их на сайте AIESEC. Статус, количество мест и дедлайн совпадают.

### M2. Рестарт не запускает bootstrap повторно
`docker compose restart aiesec-parser` → в `/sync/runs` нового `full` нет, данные на месте. (Состояние `last_full_at` лежит в БД.)

### M3. Идемпотентность
`api -X POST $URL/sync/full` дважды подряд (второй раз после завершения первого) → во втором запуске `inserted` нет, `updated` ≈ `open_total`, число строк в БД не растёт:
`sql "select count(*) from opportunities"`.

### M4. Incremental: схема и фильтр
1. `api $URL/admin/schema/filters` → `incremental_filter_ok: true`.
   Если `false`, это не ошибка: incremental будет откатываться на full. Но это дороже, поэтому подберите имя фильтра (`INCREMENTAL_DATE_FILTER`) по списку `filters` из ответа.
2. `api -X POST $URL/sync/incremental` → `stats.since` = вчерашняя дата, `fetched` мало (единицы или десятки), а не сотни.

### M5. Incremental пропустил новую стажировку → reconcile догружает
1. Удалить одну: `sql "delete from opportunities where opportunity_id = (select min(opportunity_id) from opportunities where is_open)"`.
2. `api -X POST $URL/sync/reconcile`.
3. Ожидаем в stats: `new_found: 1`, `gap_fill: by_id`; строка вернулась, `raw` заполнен.
   Если `gap_fill: full_scan`, значит, в схеме нет `opportunity(id)` (смотрите и M9).

### M6. Стажировка закрылась у AIESEC → мы её закрываем
Эмуляция «она есть у нас, но уже нет в выдаче open»:
```bash
sql "insert into opportunities (opportunity_id,is_open,home_mc_id,title,first_seen_at,last_seen_at,updated_at)
     values (900000001,true,1559,'FAKE closed upstream',now(),now(),now())"
api -X POST $URL/sync/reconcile
sql "select opportunity_id,is_open,close_reason from opportunities where opportunity_id=900000001"
```
Ожидаем `is_open=f`, `close_reason=not_in_open_list`, в stats `closed ≥ 1`. В `GET /opportunities` её нет, в `?only_open=false` есть.

### M7. Дедлайн прошёл (без запросов к AIESEC)
```bash
sql "update opportunities set applications_close_date = current_date - 1 where opportunity_id = <любой открытый>"
api -X POST $URL/maintenance/expire     # -> {"closed": 1}
```
`close_reason = deadline_passed`; в логах парсера в этот момент нет запросов к AIESEC.

### M8. Предохранитель от массового закрытия
```bash
sql "insert into opportunities (opportunity_id,is_open,home_mc_id,first_seen_at,last_seen_at,updated_at)
     select 910000000+g,true,1559,now(),now(),now() from generate_series(1,5000) g"
api -X POST $URL/sync/reconcile
api "$URL/sync/runs?limit=1"
```
Ожидаем `status=failed`, в `error` слово «Предохранитель», **ни одна** реальная стажировка не закрыта (`open_total` прежний).
Уборка: `sql "delete from opportunities where opportunity_id >= 900000000"`.

### M9. Контракт AIESEC
`AIESEC_TOKEN=<токен> make test-live`. Тесты упадут с понятным текстом, если AIESEC убрал фильтр, `created` или `opportunity(id)`.

### M10. Плохой токен
1. В `.env` поставить `AIESEC_TOKEN=bad`, `docker compose up -d aiesec-parser`.
2. `api -X POST $URL/sync/full` → run `failed`, `error` с `AuthError … 401/403`.
3. Данные в БД не тронуты (`open_total` прежний), блокировка снята (повторный POST даёт 202, а не 409).
4. Вернуть токен.

### M11. Недоступность AIESEC посреди синка
1. Запустить `api -X POST $URL/sync/full`.
2. Пока он идёт, «сломать» DNS для AIESEC внутри контейнера:
   `docker compose exec -u root aiesec-parser sh -c 'echo "0.0.0.0 gis-api.aiesec.org" >> /etc/hosts'`
3. Ожидаем ретраи с растущими паузами в логах, затем run `failed`, закрытых стажировок нет.
4. Восстановление: `docker compose restart aiesec-parser` (сбрасывает `/etc/hosts`), затем `POST /sync/reconcile` отрабатывает штатно.

### M12. Конкурентные запуски
Два POST подряд: `api -X POST $URL/sync/full; api -X POST $URL/sync/full -w ' %{http_code}\n'` → `202`, затем `409`. `/health` показывает `sync_running: true`.

### M13. Планировщик
В `.env`: `PARSER_INCREMENTAL_INTERVAL_MINUTES=1`, `docker compose up -d`. Через 3 минуты в `/sync/runs` три `incremental` без пропусков и без параллельных (`max_instances=1`). Вернуть 360.

### M14. Правка таргетов
Добавить страну в `services/aiesec-parser/targets.json` (ID найти через `api "$URL/admin/offices?q=Egypt"`), `docker compose restart aiesec-parser`, `POST /sync/full` → в `stats.countries` появилась новая страна.

### M15. Авторизация
Без `X-API-Key` → 401 на всё, кроме `/health`; с неверным → 401.

## 3. Чек-лист перед релизом

- [ ] `make test` зелёный
- [ ] `make test-live` зелёный на актуальном токене
- [ ] `docker compose down -v && make up` → bootstrap отработал, `./scripts/smoke.sh` → `SMOKE OK`
- [ ] M5, M6, M8 пройдены вручную на реальных данных
- [ ] В логах нет 429; интервал между запросами к AIESEC не меньше `REQUEST_DELAY_SEC`
- [ ] Токен и `PARSER_API_KEY` не попали в git (`git grep -i token` без реальных значений)

## 4. Что тесты не покрывают

- Реальные имена полей GraphQL: их проверяет только live-уровень (M9), а `auto_select` собирает запрос по интроспекции.
- Миграции схемы БД: пока используется `create_all`. При изменении колонок нужен Alembic.
- Нагрузка на реальный лимит AIESEC. Он неизвестен, поэтому держим паузу 0.7 с и смотрим логи на 429.