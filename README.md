# aiesec-match

`aiesec-match` — монорепозиторий платформы для сбора стажировочных возможностей AIESEC, подбора релевантных предложений и предоставления результатов через веб-интерфейс и REST API.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

## Архитектура

![C4 Context](<docs/c4/C4 Context.png>)

- [C4 Container](<docs/c4/С4 Container.png>)
- [ERD базы данных](docs/ERD.png)
- [DFD-схемы](docs/dfd/)
- [Описание документации](docs/README.md)

## Технический стек

- **Языки:** Python 3.12, TypeScript
- **Backend:** FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic
- **Фронтенд:** React 18, React Router, TanStack React Query, Vite
- **База данных:** PostgreSQL 16 с расширением `pgvector`
- **Службы:** отдельно развёрнутые сервисы backend, parser, matcher и веб-клиент
- **Инфраструктура:** Docker, Docker Compose, Make, Nginx
- **Тестирование:** pytest, Vitest, Testing Library, MSW
- **Внешний источник данных:** AIESEC GraphQL API

## Требования

- Git
- Docker Engine с плагином Docker Compose
- GNU Make
- Node.js 20 или новее — только для локальной разработки веб-клиента

Для запуска всего стека через Docker локально устанавливать Python или Node.js не требуется.

## Установка

1. Клонируйте репозиторий:

```bash
git clone <URL-репозитория>
cd aiesec_match
```

2. Создайте файл окружения:

```bash
cp .env.example .env
```

Либо создайте и заполните файл через Make:

```bash
make .env
```

3. В `.env` задайте обязательные параметры базы данных и секреты:

```dotenv
POSTGRES_PASSWORD=<пароль>
BACKEND_DB_PASSWORD=<пароль>
PARSER_DB_PASSWORD=<пароль>
MATCHER_DB_PASSWORD=<пароль>
JWT_SECRET=<секрет>
PROFILE_HMAC_SECRET=<секрет>
```

Для доступа к данным AIESEC при синхронизации задайте OAuth-параметры:

```dotenv
AIESEC_TOKEN=<токен>
AIESEC_REFRESH_TOKEN=<refresh-токен>
AIESEC_CLIENT_ID=<client-id>
AIESEC_CLIENT_SECRET=<client-secret>
```

Основные параметры портов и сервисов уже имеют значения по умолчанию в `docker-compose.yml` и `.env.example`.

## Запуск

### Полный стек через Docker

```bash
make up
```

Эта команда собирает и запускает PostgreSQL, backend, parser, matcher и веб-клиент в фоновом режиме.

Доступные адреса:

| Сервис | Адрес |
|---|---|
| Веб-клиент | `http://127.0.0.1:8080` |
| Backend API | `http://127.0.0.1:8000/api/v1` |
| Parser API | `http://127.0.0.1:8001` |
| Matcher API | `http://127.0.0.1:8002` |
| Health-check backend | `http://127.0.0.1:8000/api/v1/health` |

Полезные команды Compose через Make:

```bash
make ps
make logs
make down
make rebuild
```

Для логов одного сервиса или перезапуска конкретного компонента:

```bash
make logs SERVICE=backend
make dev-restart SERVICE=parser
make rebuild SERVICE=matcher
```

Допустимые сервисы для таких целей: `backend`, `parser`, `matcher`.

### Режим разработки

Запустите backend, parser, matcher и PostgreSQL с development-конфигурацией:

```bash
make dev-up
```

Затем установите зависимости и запустите веб-клиент локально:

```bash
make web-install
make web-dev
```

По умолчанию Vite предоставляет веб-приложение на `http://localhost:5173`.

Остановить development-стек:

```bash
make dev-down
```

## Структура проекта

```text
backend/       REST API, доменная логика, SQLAlchemy-модели и миграции Alembic
parser/        загрузка и синхронизация возможностей AIESEC
matcher/       каталог и сервис подбора рекомендаций
web/           React-приложение
infra/docker/  Docker-файлы backend, parser, matcher и веб-клиента
infra/postgres/ инициализация PostgreSQL и роли компонентов
infra/requirements/ закреплённые Python-зависимости
docs/          документация, OpenAPI, схемы и описание тестирования
scripts/       smoke-тесты и вспомогательные утилиты
loadtest/      сценарии и Make-цели нагрузочного тестирования
qa/            системные тестовые сценарии
data.csv       пример исходных данных
```

Основные точки входа:

- `backend/app/main.py` — приложение FastAPI backend
- `parser/app/main.py` — приложение FastAPI parser
- `matcher/app/main.py` — приложение FastAPI matcher
- `web/src/main.tsx` — точка входа веб-приложения
- `docker-compose.yml` — production-подобный Compose-стек
- `docker-compose.dev.yml` — Compose-накладка для разработки
- `docker-compose.test.yml` — Compose-конфигурация тестового окружения

## Тестирование

Запустить тесты всех компонентов:

```bash
make test
```

Запустить тесты конкретного компонента:

```bash
make test-backend
make test-parser
make test-matcher
make test-web
```

Запустить один тестовый файл:

```bash
make test-file SERVICE=backend F=tests/test_api_auth.py
make test-file SERVICE=web F=src/shared/lib/age.test.ts
make test-file SERVICE=parser F=tests/test_auth.py
```

Проверить покрытие:

```bash
make test-cov
make test-cov-backend
make test-cov-parser
make test-cov-matcher
make web-coverage
```

Системные тесты:

```bash
make test-system
```

## Нагрузочное тестирование

Сценарии НТ-01–НТ-03 и запуск дашборда Grafana описаны в [инструкции нагрузочного тестирования](loadtest/README.md).

## Примеры

Показать справку по доступным Make-командам:

```bash
make help
```

Подключиться к shell контейнера:

```bash
make shell SERVICE=backend
make shell SERVICE=parser
make shell SERVICE=matcher
```

Накатить миграции backend или parser:

```bash
make migrate-backend
make migrate-parser
```

Проверить живость поднятого сервиса:

```bash
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
```

Запустить smoke-тест parser после подъёма стека:

```bash
./scripts/smoke.sh
```

Для работы с parser URL можно переопределить переменной окружения:

```bash
PARSER_URL=http://127.0.0.1:8001 ./scripts/smoke.sh
```

```
aiesec_match
├─ .dockerignore
├─ .ruff_cache
│  ├─ 0.17.5
│  │  ├─ 6609985663905342634
│  │  └─ 8213006384568045760
│  └─ CACHEDIR.TAG
├─ Makefile
├─ README.md
├─ backend
│  ├─ .pytest_cache
│  │  ├─ CACHEDIR.TAG
│  │  ├─ README.md
│  │  └─ v
│  │     └─ cache
│  │        ├─ lastfailed
│  │        ├─ nodeids
│  │        └─ stepwise
│  ├─ alembic.ini
│  ├─ app
│  │  ├─ __init__.py
│  │  ├─ __pycache__
│  │  │  ├─ __init__.cpython-312.pyc
│  │  │  ├─ config.cpython-312.pyc
│  │  │  ├─ db.cpython-312.pyc
│  │  │  ├─ errors.cpython-312.pyc
│  │  │  ├─ formschema.cpython-312.pyc
│  │  │  ├─ main.cpython-312.pyc
│  │  │  └─ schemas.cpython-312.pyc
│  │  ├─ api
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ analytics.cpython-312.pyc
│  │  │  │  ├─ auth.cpython-312.pyc
│  │  │  │  ├─ feedback.cpython-312.pyc
│  │  │  │  ├─ health.cpython-312.pyc
│  │  │  │  ├─ history.cpython-312.pyc
│  │  │  │  ├─ internal_notifications.cpython-312.pyc
│  │  │  │  ├─ me.cpython-312.pyc
│  │  │  │  ├─ meta.cpython-312.pyc
│  │  │  │  ├─ notifications.cpython-312.pyc
│  │  │  │  ├─ opportunities.cpython-312.pyc
│  │  │  │  ├─ profiles.cpython-312.pyc
│  │  │  │  ├─ recommendations.cpython-312.pyc
│  │  │  │  └─ subscriptions.cpython-312.pyc
│  │  │  ├─ analytics.py
│  │  │  ├─ auth.py
│  │  │  ├─ feedback.py
│  │  │  ├─ health.py
│  │  │  ├─ history.py
│  │  │  ├─ internal_notifications.py
│  │  │  ├─ me.py
│  │  │  ├─ meta.py
│  │  │  ├─ notifications.py
│  │  │  ├─ opportunities.py
│  │  │  ├─ profiles.py
│  │  │  ├─ recommendations.py
│  │  │  └─ subscriptions.py
│  │  ├─ application
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ analytics_service.cpython-312.pyc
│  │  │  │  ├─ auth_service.cpython-312.pyc
│  │  │  │  ├─ catalog_service.cpython-312.pyc
│  │  │  │  ├─ consent_service.cpython-312.pyc
│  │  │  │  ├─ deps.cpython-312.pyc
│  │  │  │  ├─ dto_mappers.cpython-312.pyc
│  │  │  │  ├─ feedback_service.cpython-312.pyc
│  │  │  │  ├─ history_service.cpython-312.pyc
│  │  │  │  ├─ link_code_service.cpython-312.pyc
│  │  │  │  ├─ matching_service.cpython-312.pyc
│  │  │  │  ├─ me_service.cpython-312.pyc
│  │  │  │  ├─ meta_service.cpython-312.pyc
│  │  │  │  ├─ notification_service.cpython-312.pyc
│  │  │  │  ├─ profile_service.cpython-312.pyc
│  │  │  │  └─ subscription_service.cpython-312.pyc
│  │  │  ├─ analytics_service.py
│  │  │  ├─ auth_service.py
│  │  │  ├─ catalog_service.py
│  │  │  ├─ consent_service.py
│  │  │  ├─ deps.py
│  │  │  ├─ dto_mappers.py
│  │  │  ├─ feedback_service.py
│  │  │  ├─ history_service.py
│  │  │  ├─ link_code_service.py
│  │  │  ├─ matching_service.py
│  │  │  ├─ me_service.py
│  │  │  ├─ meta_service.py
│  │  │  ├─ notification_service.py
│  │  │  ├─ profile_service.py
│  │  │  └─ subscription_service.py
│  │  ├─ config.py
│  │  ├─ db.py
│  │  ├─ domain
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ age.cpython-312.pyc
│  │  │  │  ├─ completeness.cpython-312.pyc
│  │  │  │  └─ scoring.cpython-312.pyc
│  │  │  ├─ age.py
│  │  │  ├─ completeness.py
│  │  │  └─ scoring.py
│  │  ├─ errors.py
│  │  ├─ forms
│  │  │  ├─ consents.v1.yaml
│  │  │  └─ form_schema.v2.yaml
│  │  ├─ formschema.py
│  │  ├─ infrastructure
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ matcher_client.cpython-312.pyc
│  │  │  │  ├─ telegram_adapter.cpython-312.pyc
│  │  │  │  └─ time_utils.cpython-312.pyc
│  │  │  ├─ matcher_client.py
│  │  │  ├─ models
│  │  │  │  ├─ __init__.py
│  │  │  │  ├─ __pycache__
│  │  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  │  ├─ catalog.cpython-312.pyc
│  │  │  │  │  └─ core.cpython-312.pyc
│  │  │  │  ├─ catalog.py
│  │  │  │  └─ core.py
│  │  │  ├─ repositories
│  │  │  │  ├─ __init__.py
│  │  │  │  ├─ __pycache__
│  │  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  │  ├─ catalog_repo.cpython-312.pyc
│  │  │  │  │  ├─ consent_repo.cpython-312.pyc
│  │  │  │  │  ├─ feedback_repo.cpython-312.pyc
│  │  │  │  │  ├─ link_code_repo.cpython-312.pyc
│  │  │  │  │  ├─ outbox_repo.cpython-312.pyc
│  │  │  │  │  ├─ profile_repo.cpython-312.pyc
│  │  │  │  │  ├─ run_repo.cpython-312.pyc
│  │  │  │  │  ├─ subscription_repo.cpython-312.pyc
│  │  │  │  │  └─ user_repo.cpython-312.pyc
│  │  │  │  ├─ catalog_repo.py
│  │  │  │  ├─ consent_repo.py
│  │  │  │  ├─ feedback_repo.py
│  │  │  │  ├─ link_code_repo.py
│  │  │  │  ├─ outbox_repo.py
│  │  │  │  ├─ profile_repo.py
│  │  │  │  ├─ run_repo.py
│  │  │  │  ├─ subscription_repo.py
│  │  │  │  └─ user_repo.py
│  │  │  ├─ telegram_adapter.py
│  │  │  └─ time_utils.py
│  │  ├─ main.py
│  │  └─ schemas.py
│  ├─ migrations
│  │  ├─ README
│  │  ├─ env.py
│  │  ├─ script.py.mako
│  │  └─ versions
│  │     ├─ 0001_core.py
│  │     ├─ 0002_auth.py
│  │     ├─ 0003_auth.py
│  │     ├─ 0004_feedback_unique.py
│  │     ├─ 0005_drop_anonymous.py
│  │     ├─ 0006_missing_scenarios.py
│  │     ├─ 0007_recommendation_item_label.py
│  │     └─ __pycache__
│  │        ├─ 0001_core.cpython-312.pyc
│  │        └─ 71ae476ee49e_.cpython-312.pyc
│  ├─ openapi
│  │  └─ backend.v1.json
│  ├─ pytest.ini
│  ├─ tests
│  │  ├─ __pycache__
│  │  │  ├─ conftest.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_age.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_api_auth.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_api_feedback.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_api_profiles.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_api_recommendations.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_auth_unit.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_completeness.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_concurrency.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_errors.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_matcher_client.cpython-312-pytest-8.3.3.pyc
│  │  │  └─ test_schemas_unit.cpython-312-pytest-8.3.3.pyc
│  │  ├─ conftest.py
│  │  ├─ test_age.py
│  │  ├─ test_api_auth.py
│  │  ├─ test_api_feedback.py
│  │  ├─ test_api_profiles.py
│  │  ├─ test_api_recommendations.py
│  │  ├─ test_auth_unit.py
│  │  ├─ test_completeness.py
│  │  ├─ test_concurrency.py
│  │  ├─ test_errors.py
│  │  ├─ test_matcher_client.py
│  │  └─ test_schemas_unit.py
│  └─ workers
│     └─ outbox.py
├─ data.csv
├─ docker-compose.dev.yml
├─ docker-compose.test.yml
├─ docker-compose.yml
├─ docs
│  ├─ ERD.png
│  ├─ README.md
│  ├─ c4
│  │  ├─ C4 Context.png
│  │  └─ С4 Container.png
│  ├─ dfd
│  │  ├─ 00_system_context.drawio
│  │  ├─ 01_system_level_0.drawio
│  │  ├─ 02_authentication_account.drawio
│  │  ├─ 03_profile_questionnaire.drawio
│  │  ├─ 04_opportunity_catalog_parser.drawio
│  │  ├─ 05_matching_recommendations.drawio
│  │  ├─ 06_feedback_history_analytics.drawio
│  │  ├─ 07_notifications_outbox.drawio
│  │  ├─ 08_database_data_stores.drawio
│  │  ├─ README.md
│  │  ├─ architecture_inventory.md
│  │  └─ png
│  │     ├─ 00_system_context.png
│  │     ├─ 01_system_level_0.png
│  │     ├─ 02_authentication_account.png
│  │     ├─ 03_profile_questionnaire.png
│  │     ├─ 04_opportunity_catalog_parser.png
│  │     ├─ 05_matching_recommendations.png
│  │     ├─ 06_feedback_history_analytics.png
│  │     ├─ 07_notifications_outbox.png
│  │     └─ 08_database_data_stores.png
│  ├─ openapi.json
│  ├─ system-test-report.md
│  ├─ technical-specification.md
│  └─ testing.md
├─ htmlcov
│  ├─ class_index.html
│  ├─ coverage_html_cb_54cfdca1.js
│  ├─ favicon_32_cb_c827f16f.png
│  ├─ function_index.html
│  ├─ index.html
│  ├─ keybd_closed_cb_900cfef5.png
│  ├─ status.json
│  ├─ style_cb_4667309f.css
│  ├─ z_5f5a17c013354698___init___py.html
│  ├─ z_5f5a17c013354698_age_py.html
│  ├─ z_5f5a17c013354698_auth_py.html
│  ├─ z_5f5a17c013354698_catalog_py.html
│  ├─ z_5f5a17c013354698_client_py.html
│  ├─ z_5f5a17c013354698_completeness_py.html
│  ├─ z_5f5a17c013354698_config_py.html
│  ├─ z_5f5a17c013354698_db_py.html
│  ├─ z_5f5a17c013354698_errors_py.html
│  ├─ z_5f5a17c013354698_formschema_py.html
│  ├─ z_5f5a17c013354698_main_py.html
│  ├─ z_5f5a17c013354698_matcher_client_py.html
│  ├─ z_5f5a17c013354698_models_py.html
│  ├─ z_5f5a17c013354698_normalize_py.html
│  ├─ z_5f5a17c013354698_schemas_py.html
│  ├─ z_5f5a17c013354698_tokens_py.html
│  ├─ z_bcd186691859bdf8___init___py.html
│  ├─ z_bcd186691859bdf8_gapfill_py.html
│  ├─ z_bcd186691859bdf8_ingest_py.html
│  ├─ z_bcd186691859bdf8_queries_py.html
│  ├─ z_bcd186691859bdf8_service_py.html
│  ├─ z_bcd186691859bdf8_state_py.html
│  ├─ z_bcd186691859bdf8_strategies_py.html
│  ├─ z_cfb6adc3f81c8e3c___init___py.html
│  ├─ z_cfb6adc3f81c8e3c_admin_py.html
│  ├─ z_cfb6adc3f81c8e3c_analytics_py.html
│  ├─ z_cfb6adc3f81c8e3c_auth_py.html
│  ├─ z_cfb6adc3f81c8e3c_deps_py.html
│  ├─ z_cfb6adc3f81c8e3c_feedback_py.html
│  ├─ z_cfb6adc3f81c8e3c_health_py.html
│  ├─ z_cfb6adc3f81c8e3c_history_py.html
│  ├─ z_cfb6adc3f81c8e3c_me_py.html
│  ├─ z_cfb6adc3f81c8e3c_meta_py.html
│  ├─ z_cfb6adc3f81c8e3c_notifications_py.html
│  ├─ z_cfb6adc3f81c8e3c_opportunities_py.html
│  ├─ z_cfb6adc3f81c8e3c_profiles_py.html
│  ├─ z_cfb6adc3f81c8e3c_recommendations_py.html
│  ├─ z_cfb6adc3f81c8e3c_schemas_py.html
│  ├─ z_cfb6adc3f81c8e3c_subscriptions_py.html
│  └─ z_cfb6adc3f81c8e3c_sync_py.html
├─ infra
│  ├─ docker
│  │  ├─ backend.Dockerfile
│  │  ├─ matcher.Dockerfile
│  │  ├─ parser.Dockerfile
│  │  ├─ web.Dockerfile
│  │  └─ web.nginx.conf
│  ├─ postgres
│  │  ├─ bootstrap.sql
│  │  └─ init
│  │     └─ 01-databases.sh
│  └─ requirements
│     ├─ README.md
│     ├─ backend-dev.txt
│     ├─ backend.txt
│     ├─ matcher-dev.txt
│     ├─ matcher.txt
│     ├─ parser-dev.txt
│     └─ parser.txt
├─ loadtest
│  ├─ Makefile.loadtest
│  ├─ README.md
│  ├─ data
│  │  └─ tokens.json
│  ├─ docker-compose.loadtest.yml
│  ├─ grafana
│  │  ├─ dashboards
│  │  │  └─ recommendations.json
│  │  └─ provisioning
│  │     ├─ dashboards
│  │     │  └─ loadtest.yml
│  │     └─ datasources
│  │        └─ prometheus.yml
│  ├─ k6
│  │  └─ recommendations.js
│  ├─ prometheus.yml
│  ├─ results
│  │  └─ runs
│  │     ├─ 20261127-152626-570-nt01-1
│  │     │  ├─ commit.txt
│  │     │  ├─ grafana-url.txt
│  │     │  ├─ k6.log
│  │     │  ├─ parameters.txt
│  │     │  ├─ plateau-report.json
│  │     │  ├─ raw.ndjson
│  │     │  ├─ scenario.sha256
│  │     │  └─ summary.json
│  │     ├─ 20261127-152702-139-nt03-15
│  │     │  ├─ commit.txt
│  │     │  ├─ grafana-plateau-url.txt
│  │     │  ├─ grafana-url.txt
│  │     │  ├─ k6.log
│  │     │  ├─ parameters.txt
│  │     │  ├─ plateau-report.json
│  │     │  ├─ raw.ndjson
│  │     │  ├─ scenario.sha256
│  │     │  └─ summary.json
│  │     ├─ 20261127-154349-604-nt03-15
│  │     │  ├─ commit.txt
│  │     │  ├─ grafana-plateau-url.txt
│  │     │  ├─ grafana-url.txt
│  │     │  ├─ k6.log
│  │     │  ├─ parameters.txt
│  │     │  ├─ plateau-report.json
│  │     │  ├─ raw.ndjson
│  │     │  ├─ scenario.sha256
│  │     │  └─ summary.json
│  │     ├─ 20261127-160017-675-nt01-1
│  │     │  ├─ commit.txt
│  │     │  ├─ grafana-url.txt
│  │     │  ├─ k6.log
│  │     │  ├─ parameters.txt
│  │     │  ├─ plateau-report.json
│  │     │  ├─ raw.ndjson
│  │     │  ├─ scenario.sha256
│  │     │  └─ summary.json
│  │     ├─ 20261127-160418-374-nt02-10
│  │     │  ├─ commit.txt
│  │     │  ├─ grafana-plateau-url.txt
│  │     │  ├─ grafana-url.txt
│  │     │  ├─ k6.log
│  │     │  ├─ parameters.txt
│  │     │  ├─ plateau-report.json
│  │     │  ├─ raw.ndjson
│  │     │  ├─ scenario.sha256
│  │     │  └─ summary.json
│  │     ├─ 20261127-161915-112-nt01-1
│  │     │  ├─ commit.txt
│  │     │  ├─ grafana-url.txt
│  │     │  ├─ k6.log
│  │     │  ├─ parameters.txt
│  │     │  ├─ plateau-report.json
│  │     │  ├─ raw.ndjson
│  │     │  ├─ scenario.sha256
│  │     │  └─ summary.json
│  │     ├─ 20261127-223912-948-nt01-1
│  │     │  ├─ commit.txt
│  │     │  ├─ grafana-url.txt
│  │     │  ├─ k6.log
│  │     │  ├─ parameters.txt
│  │     │  ├─ plateau-report.json
│  │     │  ├─ raw.ndjson
│  │     │  ├─ scenario.sha256
│  │     │  └─ summary.json
│  │     └─ catalog.DgYaZ7tf
│  │        ├─ branch.txt
│  │        ├─ catalog-counts.txt
│  │        ├─ commit.txt
│  │        ├─ compose-ps.txt
│  │        ├─ compose-version.txt
│  │        ├─ docker-version.txt
│  │        ├─ git-status.txt
│  │        ├─ images.txt
│  │        ├─ input.sha256
│  │        └─ k6-version.txt
│  └─ scripts
│     ├─ __pycache__
│     │  ├─ docker_metrics.cpython-312.pyc
│     │  └─ test_docker_metrics.cpython-312.pyc
│     ├─ docker_metrics.py
│     ├─ prepare.sh
│     ├─ recommendation_report.py
│     ├─ run.sh
│     └─ test_docker_metrics.py
├─ matcher
│  ├─ .pytest_cache
│  │  ├─ CACHEDIR.TAG
│  │  ├─ README.md
│  │  └─ v
│  │     └─ cache
│  │        ├─ lastfailed
│  │        ├─ nodeids
│  │        └─ stepwise
│  ├─ app
│  │  ├─ __init__.py
│  │  ├─ __pycache__
│  │  │  ├─ __init__.cpython-312.pyc
│  │  │  ├─ config.cpython-312.pyc
│  │  │  ├─ deps.cpython-312.pyc
│  │  │  ├─ main.cpython-312.pyc
│  │  │  └─ schemas.cpython-312.pyc
│  │  ├─ config.py
│  │  ├─ data
│  │  │  ├─ _lists_backgrounds.json
│  │  │  ├─ _lists_industries.json
│  │  │  ├─ _lists_issues.json
│  │  │  ├─ _lists_languages.json
│  │  │  ├─ _lists_skills.json
│  │  │  └─ fake_catalog.json
│  │  ├─ deps.py
│  │  ├─ domain
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ features.cpython-312.pyc
│  │  │  │  ├─ filters.cpython-312.pyc
│  │  │  │  ├─ models.cpython-312.pyc
│  │  │  │  ├─ profile.cpython-312.pyc
│  │  │  │  └─ scoring.cpython-312.pyc
│  │  │  ├─ features.py
│  │  │  ├─ filters.py
│  │  │  ├─ models.py
│  │  │  ├─ profile.py
│  │  │  ├─ scoring.py
│  │  │  └─ taxonomy.yaml
│  │  ├─ main.py
│  │  ├─ repo
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  └─ catalog_reader.cpython-312.pyc
│  │  │  └─ catalog_reader.py
│  │  ├─ routers
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ dictionaries.cpython-312.pyc
│  │  │  │  ├─ health.cpython-312.pyc
│  │  │  │  └─ match.cpython-312.pyc
│  │  │  ├─ dictionaries.py
│  │  │  ├─ health.py
│  │  │  └─ match.py
│  │  ├─ schemas.py
│  │  └─ weights.yaml
│  ├─ migrations
│  ├─ pytest.ini
│  ├─ tests
│  │  ├─ __init__.py
│  │  ├─ __pycache__
│  │  │  ├─ __init__.cpython-312.pyc
│  │  │  ├─ conftest.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ factories.cpython-312.pyc
│  │  │  ├─ test_ai_cycle.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_api.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_boundaries.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_catalog_cache.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_catalog_reader.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_contract.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_features.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_filters.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_negative.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_privacy.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_profile.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_regression_bugs.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_router.cpython-312-pytest-8.3.3.pyc
│  │  │  ├─ test_scoring.cpython-312-pytest-8.3.3.pyc
│  │  │  └─ test_spec_values.cpython-312-pytest-8.3.3.pyc
│  │  ├─ conftest.py
│  │  ├─ factories.py
│  │  ├─ test_ai_cycle.py
│  │  ├─ test_api.py
│  │  ├─ test_boundaries.py
│  │  ├─ test_catalog_cache.py
│  │  ├─ test_catalog_reader.py
│  │  ├─ test_contract.py
│  │  ├─ test_features.py
│  │  ├─ test_filters.py
│  │  ├─ test_negative.py
│  │  ├─ test_privacy.py
│  │  ├─ test_profile.py
│  │  ├─ test_regression_bugs.py
│  │  ├─ test_router.py
│  │  ├─ test_scoring.py
│  │  └─ test_spec_values.py
│  └─ tools
│     └─ control_defects.py
├─ parser
│  ├─ .coveragerc
│  ├─ .pytest_cache
│  │  ├─ CACHEDIR.TAG
│  │  ├─ README.md
│  │  └─ v
│  │     └─ cache
│  │        ├─ nodeids
│  │        └─ stepwise
│  ├─ alembic.ini
│  ├─ app
│  │  ├─ __init__.py
│  │  ├─ __pycache__
│  │  │  ├─ __init__.cpython-312.pyc
│  │  │  ├─ auth.cpython-312.pyc
│  │  │  ├─ client.cpython-312.pyc
│  │  │  ├─ config.cpython-312.pyc
│  │  │  ├─ errors.cpython-312.pyc
│  │  │  ├─ main.cpython-312.pyc
│  │  │  ├─ models.cpython-312.pyc
│  │  │  ├─ normalize.cpython-312.pyc
│  │  │  ├─ runtime.cpython-312.pyc
│  │  │  └─ tokens.cpython-312.pyc
│  │  ├─ api
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ admin.cpython-312.pyc
│  │  │  │  ├─ deps.cpython-312.pyc
│  │  │  │  ├─ health.cpython-312.pyc
│  │  │  │  ├─ opportunities.cpython-312.pyc
│  │  │  │  ├─ schemas.cpython-312.pyc
│  │  │  │  └─ sync.cpython-312.pyc
│  │  │  ├─ admin.py
│  │  │  ├─ deps.py
│  │  │  ├─ health.py
│  │  │  ├─ opportunities.py
│  │  │  ├─ schemas.py
│  │  │  └─ sync.py
│  │  ├─ auth.py
│  │  ├─ client.py
│  │  ├─ config.py
│  │  ├─ errors.py
│  │  ├─ main.py
│  │  ├─ models.py
│  │  ├─ normalize.py
│  │  ├─ runtime.py
│  │  ├─ sync
│  │  │  ├─ __init__.py
│  │  │  ├─ __pycache__
│  │  │  │  ├─ __init__.cpython-312.pyc
│  │  │  │  ├─ gapfill.cpython-312.pyc
│  │  │  │  ├─ ingest.cpython-312.pyc
│  │  │  │  ├─ queries.cpython-312.pyc
│  │  │  │  ├─ service.cpython-312.pyc
│  │  │  │  ├─ state.cpython-312.pyc
│  │  │  │  └─ strategies.cpython-312.pyc
│  │  │  ├─ gapfill.py
│  │  │  ├─ ingest.py
│  │  │  ├─ queries.py
│  │  │  ├─ service.py
│  │  │  ├─ state.py
│  │  │  └─ strategies.py
│  │  └─ tokens.py
│  ├─ migrations
│  │  ├─ env.py
│  │  ├─ script.py.mako
│  │  └─ versions
│  │     ├─ 0001_initial.py
│  │     ├─ 0002_catalog_v1.py
│  │     └─ 0003_catalog_v1_fix.py
│  ├─ pytest.ini
│  ├─ targets.json
│  └─ tests
│     ├─ __init__.py
│     ├─ __pycache__
│     │  ├─ __init__.cpython-312.pyc
│     │  ├─ conftest.cpython-312-pytest-8.3.3.pyc
│     │  ├─ test_api.cpython-312-pytest-8.3.3.pyc
│     │  ├─ test_auth.cpython-312-pytest-8.3.3.pyc
│     │  ├─ test_live.cpython-312-pytest-8.3.3.pyc
│     │  ├─ test_normalize.cpython-312-pytest-8.3.3.pyc
│     │  ├─ test_openapi.cpython-312-pytest-8.3.3.pyc
│     │  └─ test_sync.cpython-312-pytest-8.3.3.pyc
│     ├─ conftest.py
│     ├─ test_api.py
│     ├─ test_auth.py
│     ├─ test_live.py
│     ├─ test_normalize.py
│     ├─ test_openapi.py
│     └─ test_sync.py
├─ qa
│  ├─ catalog_data.py
│  ├─ conftest.py
│  ├─ load
│  ├─ pytest.ini
│  ├─ seed_catalog.py
│  ├─ test_backend_negative.py
│  ├─ test_db_contract.py
│  ├─ test_e2e_user_flow.py
│  ├─ test_matcher_db.py
│  ├─ test_parser_api.py
│  └─ test_smoke.py
├─ scripts
│  ├─ __pycache__
│  │  ├─ generate_dfd.cpython-312.pyc
│  │  ├─ prettify_dfd.cpython-312.pyc
│  │  ├─ refactor_dfd_layout.cpython-312.pyc
│  │  ├─ refactor_layout.cpython-312.pyc
│  │  ├─ validate_dfd.cpython-312.pyc
│  │  └─ validate_layout.cpython-312.pyc
│  ├─ find_env_vars.py
│  ├─ generate_dfd.py
│  ├─ prettify_dfd.py
│  ├─ refactor_dfd_layout.py
│  ├─ smoke.sh
│  └─ validate_dfd.py
└─ web
   ├─ README.md
   ├─ coverage
   │  ├─ base.css
   │  ├─ block-navigation.js
   │  ├─ favicon.png
   │  ├─ index.html
   │  ├─ lcov-report
   │  │  ├─ base.css
   │  │  ├─ block-navigation.js
   │  │  ├─ favicon.png
   │  │  ├─ index.html
   │  │  ├─ prettify.css
   │  │  ├─ prettify.js
   │  │  ├─ readex-pro-license.txt
   │  │  ├─ readex-pro.woff2
   │  │  ├─ sort-arrow-sprite.png
   │  │  ├─ sorter.js
   │  │  └─ theme.js
   │  ├─ lcov.info
   │  ├─ prettify.css
   │  ├─ prettify.js
   │  ├─ readex-pro-license.txt
   │  ├─ readex-pro.woff2
   │  ├─ sort-arrow-sprite.png
   │  ├─ sorter.js
   │  └─ theme.js
   ├─ dist
   │  ├─ assets
   │  │  ├─ index-BpcgN5Bj.js
   │  │  └─ index-C_Y0ROFh.css
   │  └─ index.html
   ├─ e2e
   │  └─ recommendations-favorites.spec.ts
   ├─ eslint.config.js
   ├─ index.html
   ├─ package.json
   ├─ playwright-report
   │  ├─ data
   │  │  └─ 2963af16c2de027e223ed109a8494fb5f88713a3.zip
   │  ├─ index.html
   │  └─ trace
   │     ├─ assets
   │     │  ├─ codeMirrorModule-DNqxPF-E.js
   │     │  ├─ defaultSettingsView-BQT9Z6FV.js
   │     │  ├─ rolldown-runtime-QTnfLwEv.js
   │     │  └─ urlMatch-Cgl6axSs.js
   │     ├─ codeMirrorModule.-QdMvsKi.css
   │     ├─ codicon.DCmgc-ay.ttf
   │     ├─ defaultSettingsView.C8BeHuxd.css
   │     ├─ index.BY2vkw8A.js
   │     ├─ index.B_TqY17P.css
   │     ├─ index.html
   │     ├─ manifest.webmanifest
   │     ├─ playwright-logo.svg
   │     ├─ snapshot.-ChLTbql.js
   │     ├─ snapshot.html
   │     ├─ sw.bundle.js
   │     ├─ uiMode.CyMfwkXJ.css
   │     ├─ uiMode.DuLwZHRf.js
   │     ├─ uiMode.html
   │     └─ xtermModule.kHJ-D0s7.css
   ├─ playwright.config.ts
   ├─ seed.spec.ts
   ├─ specs
   │  ├─ README.md
   │  ├─ recommendations-favorites-fault-validation.md
   │  └─ test-plan-recommendations-favorites.md
   ├─ src
   │  ├─ app
   │  │  ├─ App.tsx
   │  │  ├─ providers.tsx
   │  │  ├─ router.tsx
   │  │  └─ routes.ts
   │  ├─ entities
   │  │  ├─ history
   │  │  │  └─ HistoryEventItem.tsx
   │  │  ├─ opportunity
   │  │  │  ├─ CapacityBadge.tsx
   │  │  │  ├─ CostLabel.tsx
   │  │  │  ├─ OpportunityCard.tsx
   │  │  │  ├─ ProgrammeBadge.tsx
   │  │  │  └─ RequirementChips.tsx
   │  │  ├─ profile
   │  │  │  └─ ProfileSummary.tsx
   │  │  └─ recommendation
   │  │     ├─ MatchLabel.tsx
   │  │     ├─ ReasonList.tsx
   │  │     └─ RecItemCard.tsx
   │  ├─ features
   │  │  ├─ account
   │  │  │  ├─ AccountSecurityForm.tsx
   │  │  │  ├─ DeleteAccountDialog.tsx
   │  │  │  └─ LinkTelegramPanel.tsx
   │  │  ├─ auth
   │  │  │  └─ AuthContext.tsx
   │  │  ├─ consent
   │  │  │  └─ ConsentSettings.tsx
   │  │  ├─ dashboard
   │  │  ├─ feedback
   │  │  │  └─ useSendFeedback.ts
   │  │  ├─ questionnaire
   │  │  │  ├─ FieldRenderer.tsx
   │  │  │  ├─ FormRenderer.tsx
   │  │  │  ├─ ProgrammeCards.tsx
   │  │  │  ├─ useFormState.test.ts
   │  │  │  ├─ useFormState.ts
   │  │  │  └─ validation.ts
   │  │  ├─ recommendations
   │  │  │  └─ useCreateRecommendations.ts
   │  │  └─ subscription
   │  │     └─ SubscriptionForm.tsx
   │  ├─ main.tsx
   │  ├─ pages
   │  │  ├─ errors
   │  │  │  ├─ NotFoundPage.tsx
   │  │  │  └─ OfflinePage.tsx
   │  │  ├─ history
   │  │  │  └─ HistoryPage.tsx
   │  │  ├─ login
   │  │  │  └─ LoginPage.tsx
   │  │  ├─ notifications
   │  │  │  └─ NotificationsPage.tsx
   │  │  ├─ onboarding
   │  │  │  └─ OnboardingPage.tsx
   │  │  ├─ opportunities
   │  │  ├─ opportunity
   │  │  │  └─ OpportunityPage.tsx
   │  │  ├─ profile
   │  │  │  ├─ FavoritesPage.tsx
   │  │  │  ├─ ProfileEditPage.tsx
   │  │  │  ├─ ProfilePage.tsx
   │  │  │  └─ ProfileStatisticsPage.tsx
   │  │  ├─ register
   │  │  │  └─ RegisterPage.tsx
   │  │  ├─ results
   │  │  │  └─ ResultsPage.tsx
   │  │  ├─ settings
   │  │  │  └─ SettingsPage.tsx
   │  │  └─ welcome
   │  │     └─ WelcomePage.tsx
   │  ├─ shared
   │  │  ├─ api
   │  │  │  ├─ client.test.ts
   │  │  │  ├─ client.ts
   │  │  │  ├─ endpoints.ts
   │  │  │  ├─ queries.ts
   │  │  │  └─ types.ts
   │  │  ├─ config
   │  │  │  └─ brand.ts
   │  │  ├─ hooks
   │  │  │  ├─ useMediaQuery.ts
   │  │  │  └─ useOnline.ts
   │  │  ├─ lib
   │  │  │  ├─ age.test.ts
   │  │  │  ├─ age.ts
   │  │  │  ├─ condition.test.ts
   │  │  │  ├─ condition.ts
   │  │  │  ├─ date.ts
   │  │  │  ├─ errors.test.ts
   │  │  │  ├─ errors.ts
   │  │  │  ├─ format.test.ts
   │  │  │  ├─ format.ts
   │  │  │  ├─ get.test.ts
   │  │  │  ├─ get.ts
   │  │  │  ├─ password.test.ts
   │  │  │  └─ password.ts
   │  │  ├─ styles
   │  │  │  ├─ global.css
   │  │  │  ├─ layout.css
   │  │  │  └─ tokens.css
   │  │  └─ ui
   │  │     ├─ AuthCard.tsx
   │  │     ├─ Avatar.tsx
   │  │     ├─ Badge.tsx
   │  │     ├─ BarChart.tsx
   │  │     ├─ Button.tsx
   │  │     ├─ Card.tsx
   │  │     ├─ ChartLegend.tsx
   │  │     ├─ ChartTooltip.tsx
   │  │     ├─ Chip.tsx
   │  │     ├─ ChipGroup.tsx
   │  │     ├─ DateField.tsx
   │  │     ├─ DateRangeFilter.tsx
   │  │     ├─ Dialog.tsx
   │  │     ├─ DonutChart.tsx
   │  │     ├─ EmptyState.tsx
   │  │     ├─ ErrorBanner.tsx
   │  │     ├─ IconButton.tsx
   │  │     ├─ LineChart.tsx
   │  │     ├─ NavigationBar.tsx
   │  │     ├─ NumberStepper.tsx
   │  │     ├─ PasswordField.tsx
   │  │     ├─ Progress.tsx
   │  │     ├─ Segmented.tsx
   │  │     ├─ Select.tsx
   │  │     ├─ Skeleton.tsx
   │  │     ├─ Tabs.tsx
   │  │     ├─ TextArea.tsx
   │  │     ├─ TextField.tsx
   │  │     ├─ Timeline.tsx
   │  │     ├─ Toast.tsx
   │  │     ├─ Toggle.tsx
   │  │     └─ index.ts
   │  ├─ test
   │  │  ├─ msw
   │  │  │  ├─ handlers.ts
   │  │  │  └─ server.ts
   │  │  ├─ setup.ts
   │  │  └─ utils.tsx
   │  └─ widgets
   │     ├─ MainNavigation.tsx
   │     ├─ OnboardingWizard.tsx
   │     ├─ ProfileCompleteness.tsx
   │     ├─ ProfileSummaryBar.tsx
   │     ├─ ProfileVersionHistory.tsx
   │     ├─ ResultsTabs.tsx
   │     └─ UserStatisticsDashboard.tsx
   ├─ test-results
   │  ├─ .last-run.json
   │  └─ recommendations-favorites--d4c6b-анением-после-перезагрузки-
   │     └─ trace.zip
   ├─ tsconfig.app.json
   ├─ tsconfig.json
   ├─ tsconfig.node.json
   ├─ vite.config.ts
   └─ vitest.config.ts

```