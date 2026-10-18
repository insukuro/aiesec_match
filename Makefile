ifneq (,$(wildcard .env))
include .env
export
endif
.env:
	@test -f .env.example || (echo "нет .env.example" && exit 1)
	cp .env.example .env
	@echo "Создан .env из .env.example. Отредактируйте пароли перед запуском."

ensure-env:
	@test -f .env || $(MAKE) .env
COMPOSE      := docker compose -f docker-compose.yml
COMPOSE_DEV  := docker compose -f docker-compose.yml -f docker-compose.dev.yml

.PHONY: up down logs rebuild psql migrate shell \
        dev-up dev-down dev-logs dev-shell \
        test test-file test-live test-collect \
        test-cov test-cov-html openapi-snapshot

## ---------- прод ----------
up: ensure-env
	$(COMPOSE) up -d --build

down:            ## остановить (данные сохраняются — volume не удаляется)
	$(COMPOSE) down

logs:            ## логи парсера
	$(COMPOSE) logs -f parser

rebuild:         ## пересобрать парсер с нуля
	$(COMPOSE) build --no-cache parser && $(COMPOSE) up -d parser

psql:            ## psql в контейнер postgres
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-platform} $${PARSER_DB:-parser}

migrate:         ## применить миграции вручную (обычно делает entrypoint)
	$(COMPOSE) exec parser alembic upgrade head

shell:           ## shell в прод-контейнере парсера
	$(COMPOSE) exec parser sh

## ---------- dev ----------
dev-up: ensure-env        ## поднять dev-стек (hot-reload)
	$(COMPOSE_DEV) up -d --build postgres parser

dev-down:        ## остановить dev-стек (данные сохраняются)
	$(COMPOSE_DEV) down

dev-logs:        ## логи dev-парсера
	$(COMPOSE_DEV) logs -f parser

dev-shell:       ## shell в dev-контейнере
	$(COMPOSE_DEV) run --rm --entrypoint sh parser

## ---------- тесты (в Docker, локальный Python не нужен) ----------
test:            ## быстрые тесты + покрытие
	$(COMPOSE_DEV) run --rm tests --cov=app --cov-report=term-missing

test-file:       ## один файл: make test-file F=tests/test_sync.py
	$(COMPOSE_DEV) run --rm tests $(F)

test-live:       ## live-тесты против настоящего AIESEC (нужен AIESEC_TOKEN)
	$(COMPOSE_DEV) run --rm -e AIESEC_TOKEN=$${AIESEC_TOKEN:?нужен AIESEC_TOKEN} tests -m live -o addopts=""

test-collect:    ## только собрать тесты (проверка импортов)
	$(COMPOSE_DEV) run --rm tests --collect-only -o addopts=""

test-cov:        ## тесты с покрытием, порог 70% (для CI)
	$(COMPOSE_DEV) run --rm tests --cov-fail-under=70 --tb=no

test-cov-html:   ## то же, но с HTML-отчётом в htmlcov/
	$(COMPOSE_DEV) run --rm tests --cov-report=html:htmlcov

## ---------- openapi ----------
openapi-snapshot: ## пересоздать docs/openapi.json (осознанное изменение API)
	rm -f docs/openapi.json
	$(COMPOSE_DEV) run --rm tests tests/test_openapi.py -o addopts=""