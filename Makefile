ifneq (,$(wildcard .env))
include .env
export
endif

COMPOSE      := docker compose -f docker-compose.yml
COMPOSE_DEV  := docker compose -f docker-compose.yml -f docker-compose.dev.yml

.PHONY: up down logs rebuild psql \
        dev-up dev-down dev-logs dev-shell \
        test test-file test-live test-collect \
        test-cov test-cov-html
## ---------- прод ----------
up:              ## поднять всё (прод)
	$(COMPOSE) up -d --build

down:            ## остановить
	$(COMPOSE) down

logs:            ## логи парсера
	$(COMPOSE) logs -f aiesec-parser

rebuild:         ## пересобрать парсер с нуля
	$(COMPOSE) build --no-cache aiesec-parser && $(COMPOSE) up -d aiesec-parser

psql:            ## psql в контейнер postgres
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-platform} $${PARSER_DB:-parser}

## ---------- dev ----------
dev-up:          ## поднять dev-стек (hot-reload)
	$(COMPOSE_DEV) up -d --build postgres aiesec-parser

dev-down:        ## остановить dev-стек
	$(COMPOSE_DEV) down

dev-logs:        ## логи dev-парсера
	$(COMPOSE_DEV) logs -f aiesec-parser

dev-shell:       ## shell в dev-контейнере
	$(COMPOSE_DEV) run --rm --entrypoint sh aiesec-parser




## ---------- тесты (в Docker, локальный Python не нужен) ----------
test:            ## быстрые тесты + покрытие (без порога)
	$(COMPOSE_DEV) run --rm tests

test-file:       ## один файл: make test-file F=tests/test_sync.py
	$(COMPOSE_DEV) run --rm tests $(F)

test-live:       ## live-тесты против настоящего AIESEC (нужен AIESEC_TOKEN)
	$(COMPOSE_DEV) run --rm -e AIESEC_TOKEN=$${AIESEC_TOKEN:?нужен AIESEC_TOKEN} tests -m live -o addopts=""

test-collect:    ## только собрать тесты (проверка импортов)
	$(COMPOSE_DEV) run --rm tests --collect-only -o addopts=""

test-cov:        ## тесты с покрытием, порог 70% (для CI)
	$(COMPOSE_DEV) run --rm tests --cov-fail-under=70 --tb=no -q

test-cov-html:   ## то же, но с HTML-отчётом в htmlcov/
	$(COMPOSE_DEV) run --rm tests --cov-report=html:htmlcov