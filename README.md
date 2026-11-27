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
