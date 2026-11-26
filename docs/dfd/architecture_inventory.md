# Architecture Inventory

## Backend

| Компонент | Назначение | Расположение | Входящие данные | Исходящие данные | Хранилища | Связи | Подтверждение |
|---|---|---|---|---|---|---|---|
| FastAPI application | Маршрутизация API и middleware request ID/CORS | `backend/app/main.py` | HTTP request data | JSON / HTTP status | none | frontend, matcher, PostgreSQL | include_router, lifespan, CORS |
| Auth service | Регистрация, login, Telegram auth, смена credentials | `backend/app/application/auth_service.py` | email/password/Telegram initData | JWT, account changes | core.users, identities, password_credentials, verifications | API auth router, UserRepo | HTTP routes and tests |
| Profile service | Загрузка, обновление и версионирование анкеты | `backend/app/application/profile_service.py` | ProfileIn, ETag version | ProfileOut, version history | core.profiles, profile_versions | consent service, ProfileRepo | profiles router and tests |
| Consent service | Проверка и изменение accept/revoke consent | `backend/app/application/consent_service.py` | consent kind/version | consent result | core.consents | forms/consents.v1.yaml | consent API |
| Form schema | Схема анкеты и справочники | `backend/app/forms/form_schema.v2.yaml`, `backend/app/formschema.py` | none | form schema/options | none | profile frontend | meta API |
| Consent schema | Версии документов обработки данных | `backend/app/forms/consents.v1.yaml` | none | consent schema | none | consent service | meta/me API |
| Matching service | Создание matching-run и сохранение ответов | `backend/app/application/matching_service.py` | profile, filters, idempotency key | recommendation groups/run | core runs/items/profile/feedback; catalog.* | Matcher HTTP client, CatalogRepo | POST /recommendations |
| Matcher client | Синхронный HTTP-вызов matcher | `backend/app/infrastructure/matcher_client.py` | match payload | match response/errors | none | matcher POST /v1/match | AsyncClient |
| Catalog repositories | Чтение catalog opportunities/views | `backend/app/infrastructure/repositories/catalog_repo.py` | opportunity ids | cards/requirements/watermark | catalog.* | matching and feedback | SQLAlchemy queries |
| Feedback service | Сигналы и liked/hidden списки | `backend/app/application/feedback_service.py` | feedback signal/run/opportunity | feedback lists/cards | core.feedback, catalog.* | FeedbackRepo, CatalogRepo | feedback API |
| History service | Комбинированная история runs и feedback | `backend/app/application/history_service.py` | type/date range/pagination | history events | core.runs, feedback | history API | SQL UNION |
| Analytics service | Агрегация profile/runs/feedback | `backend/app/application/analytics_service.py` | period/date range | analytics metrics | core profiles/runs/feedback | analytics API | SQL aggregates |
| Notification service | In-app notifications и consumer lease/ack | `backend/app/application/notification_service.py` | lease parameters/ack error | notification payload/read state | core.notification_outbox | external Telegram consumer | internal/v1 API |
| Outbox repository | Дедупликация, leasing, ack и in-app state | `backend/app/infrastructure/repositories/outbox_repo.py` | run/user/payload/error | outbox state | core.notification_outbox, subscriptions | notification service | SQLAlchemy |
| Link code service | Привязка Telegram identity | `backend/app/application/link_code_service.py` | code/chat/id | identity update | core.link_codes, identities, outbox | external bot/internal API | consume endpoint |
| Outbox worker module | Формирует outbox-события после runs | `backend/workers/outbox.py` | run id/items/user id | pending outbox payload | core.notification_outbox, subscriptions | MatchingService | enqueue_for_user |

## Matcher

| Компонент | Назначение | Расположение | Входящие данные | Исходящие данные | Хранилища | Связи | Подтверждение |
|---|---|---|---|---|---|---|---|
| Match router | Приём запроса на подбор | `matcher/app/routers/match.py` | profile snapshot, filters, limit | groups/scores/reasons | catalog.* read-only | backend HTTP | POST /v1/match |
| Catalog reader | Чтение opportunities и requirements | `matcher/app/repo/catalog_reader.py` | programme kind | opportunity model list | catalog.opportunity_v1, opportunity_requirement_v1 | PostgreSQL/read-only | DbCatalogReader |
| Fake catalog reader | Фиктивный каталог для dev/test | `matcher/app/repo/catalog_reader.py` | fake JSON path | opportunity list | `matcher/app/data/*.json` | tests/dev | MATCHER_CATALOG_SOURCE=fake |
| Filters | Жёсткие фильтры кандидатов | `matcher/app/domain/filters.py` | profile/opportunity/filter | retained opportunities | none | match router | direct function calls |
| Features | Features scoring | `matcher/app/domain/features.py` | opportunity/profile/chance/date | feature map | none | scoring | direct function calls |
| Scoring | Weighted scoring, labels, reasons | `matcher/app/domain/scoring.py` | feature map/opportunities/weights | ranked MatchItems | weights.yaml | match router | load_weights |
| Dictionaries | Справочники для API | `matcher/app/routers/dictionaries.py`, `matcher/app/data/*.json` | HTTP request | dictionary values | local JSON | frontend direct/backend? | matcher's router |

## Parser

| Компонент | Назначение | Расположение | Входящие данные | Исходящие данные | Хранилища | Связи | Подтверждение |
|---|---|---|---|---|---|---|---|
| AIESEC client | GraphQL/auth, paging, retry and throttling | `parser/app/client.py` | OAuth/access tokens, query filters | raw opportunity records | parser.sync_state indirectly | AIESEC API | HTTP requests |
| OAuth refresher | Exchange and refresh access tokens | `parser/app/auth.py`, `parser/app/tokens.py` | refresh/client credentials | access/refresh tokens | parser.sync_state | AIESEC OAuth | refresh flow |
| Sync strategies | Full, incremental, reconcile | `parser/app/sync/strategies.py` | remote rows/watermarks/known ids | normalized ingest operations | parser.* | SyncService | scheduler/API/tests |
| Ingestor | Normalize, target check, actuality, upsert/close | `parser/app/sync/ingest.py`, `parser/app/normalize.py` | raw opportunity rows | parser opportunity rows | parser.opportunities | PostgreSQL | direct SQLAlchemy |
| Gap filler | Получение full-данных для новых ids | `parser/app/sync/gapfill.py` | new opportunity ids | full opportunity rows | parser.opportunities | AIESEC client | reconcile strategy |
| Sync API | Ручной запуск sync и списки runs | `parser/app/api/sync.py` | kind/pagination | run status/stats | parser.sync_runs | scheduler | POST/GET endpoints |
| Admin API | Targets, schema, token diagnostics | `parser/app/api/admin.py` | token/refresh data | health/status/sync trigger | parser.sync_state | AIESEC client | endpoint implementation |

## Frontend

| Компонент | Назначение | Расположение | Входящие данные | Исходящие данные | Хранилища | Связи | Подтверждение |
|---|---|---|---|---|---|---|---|
| API client | Authorization header, request ID, idempotency key | `web/src/shared/api/client.ts` | response/HTTP errors | bearer JWT/JSON request | browser localStorage access_token | backend /api/v1 | fetch implementation |
| Endpoints | Typed backend API calls | `web/src/shared/api/endpoints.ts` | domain params | backend requests | none | backend routers | API methods |
| Telegram WebApp integration | Получение initData | `web/src/pages/welcome/WelcomePage.tsx` | Telegram WebApp initData | auth/telegram request | browser only | backend auth/telegram | window.Telegram check |

## PostgreSQL / Logical Stores

| Хранилище | Назначение | Основные поля | Читают | Пишут |
|---|---|---|---|---|
| core.users | Пользовательские accounts и soft-delete | user_id, created_at, deleted_at | auth/me | auth/me |
| core.identities | Password/Telegram identity mapping | provider, external_id | auth/me/link | auth/link |
| core.password_credentials | Email и password hash | email, password_hash, verified_at | auth | auth |
| core.password_reset_tokens | Reset-token hashes | token_hash, expiry, used_at | auth | auth |
| core.email_verifications | Email-change code hashes | code_hash, expiry | auth | auth |
| core.consents | Acceptance records | kind, version, accepted_at | consent/matching | consent |
| core.profiles | Текущая profile version | current_version, updated_at | profile/matching/analytics | profile |
| core.profile_versions | Questionnaire JSON snapshots | body, birth_date, completeness | profile/matching/analytics | profile |
| core.recommendation_runs | Matching run metadata/state | state, filters, watermark, idempotency | matching/history/analytics/outbox | matching |
| core.recommendation_items | Ranked results | rank, score, label, reasons | matching/history/analytics | matching |
| core.feedback | User signals | signal, opportunity_id, run_id | feedback/matching/analytics/history | feedback |
| core.subscriptions | Notification preferences | notify, min_score, channels | outbox enqueue | subscription/outbox ack |
| core.notification_outbox | Async notification events | state, attempts, lease, payload | notification consumer/in-app | matching/outbox worker service |
| core.link_codes | Telegram linking codes | code, expiry, used_at | link service | me/link |
| catalog.opportunity_v1 | Canonical opportunity view/model | opportunity fields | matcher/backend | `UNVERIFIED` loader/export relation |
| catalog.opportunity_requirement_v1 | Opportunity requirements view/model | kind, constant, option | matcher/backend | `UNVERIFIED` loader/export relation |
| catalog.sync_state_v1 | Catalog sync watermark | committed_watermark | backend matching | `UNVERIFIED` loader/export relation |
| parser.opportunities | Raw normalized parser catalog | raw JSON and parsed columns | reconcile/targets | parser ingest |
| parser.sync_runs | Sync execution history | kind/status/stats/error | sync API | SyncService |
| parser.sync_state | Watermarks/tokens | key/value | sync strategies/tokens | sync/tokens |

## Confirmed Cross-Service Flows

- Frontend → Backend: REST `/api/v1/*` and bearer JWT.
- Backend → Matcher: synchronous HTTP `POST http://matcher:8000/v1/match`.
- Backend → PostgreSQL: asyncpg on `AIESEC_DATABASE_URL`, core/catalog stores.
- Matcher → PostgreSQL: psycopg read-only `catalog.*` when `MATCHER_CATALOG_SOURCE=db`.
- Parser → AIESEC OAuth: OAuth token exchange/refresh.
- Parser → AIESEC GraphQL: opportunity queries and paging.
- External Telegram consumer → Backend: internal `/internal/v1/notifications/lease`, `/ack`, `/link-codes/consume`.
- Backend → in-app UI: notification records from outbox.

## Async and Sync Boundaries

- Synchronous: HTTP API, profile put, catalog reads, matcher call, run persistence, feedback/history/analytics reads.
- Scheduled/async within parser: APScheduler jobs `full`, `incremental`, `reconcile`, `expire_by_deadline`, token keepalive.
- Deferred notification: matching creates outbox synchronously; external consumer leases and acknowledges asynchronously.
- Parser manual sync: FastAPI `202` plus `BackgroundTasks` executes sync.

## Security and Privacy

- JWT is HS256 with `sub`, `exp`, `aud`, `iat`; frontend stores access token in localStorage.
- Passwords use bcrypt; stored values are password hashes, not plaintext.
- Telegram initData is HMAC-verified using bot token and has auth-date 24-hour check.
- Profile payload sent to matcher is HMAC-derived profile id plus selected non-birth profile fields; diagram shows types only.
- Consent `pd_processing` is required before profile or matching operations; it cannot be revoked.
- Telegram identity is stored with external id and chat id metadata.
- DFD files contain no secret values or real personal data.

## Unverified or Ambiguous Items

- `parser.*` to `catalog.*` transfer: parser code writes raw normalized opportunities, while catalog views/tables are backend/matcher sources. A migration or DB bootstrap can create/populate catalog views, but no direct in-code parser→catalog write was found. Marked UNVERIFIED in DFD-04.
- Telegram delivery implementation is external; repository contains internal APIs but no bot sender/consumer process.
- Retry behavior: outbox rows support `retry` state in leasing, but ack sets `failed` and no local retry loop/scheduler is implemented in the repository. Retry count exists; automatic retry semantics are not confirmed.
- Parser `password_reset_tokens` has no API implementation despite model/migration presence.
- Email change code is returned to API caller and encoded together with code hash/new email verification; no real email sender integration was found.
