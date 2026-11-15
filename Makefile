# Makefile — корень проекта aiesec_match

ifneq (,$(wildcard .env))
include .env
export
endif

# -------------------- env --------------------
.env:
	@test -f .env.example || (echo "нет .env.example" && exit 1)
	cp .env.example .env
	@echo "Создан .env из .env.example. Отредактируйте пароли перед запуском."

ensure-env:
	@test -f .env || $(MAKE) .env

# -------------------- compose --------------------
COMPOSE      := docker compose -f docker-compose.yml
COMPOSE_DEV  := docker compose -f docker-compose.yml -f docker-compose.dev.yml
TOOLS        := --profile tools

# -------------------- phony --------------------
.PHONY: help \
        up down logs ps psql \
        rebuild rebuild-backend rebuild-parser rebuild-web \
        shell shell-backend shell-parser \
        migrate migrate-backend migrate-parser \
        dev-up dev-down dev-restart dev-logs \
        dev-shell dev-shell-backend dev-shell-parser \
        test test-backend test-parser \
        test-file-backend test-file-parser \
        test-live test-collect-backend test-collect-parser \
        test-cov test-cov-backend test-cov-parser \
        openapi-snapshot \
        web-install web-dev web-build web-lint web-test

# -------------------- help --------------------
help:            ## показать список команд
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# -------------------- prod --------------------
up: ensure-env            ## prod-стек (backend, parser, web, postgres)
	$(COMPOSE) up -d --build

down:                     ## остановить (volume сохраняется)
	$(COMPOSE) down

logs:                     ## логи всех сервисов
	$(COMPOSE) logs -f

ps:                       ## статус контейнеров
	$(COMPOSE) ps

psql:                     ## psql в контейнер postgres (БД приложения)
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-platform} $${APP_DB:-aiesec_match}

rebuild:                  ## пересобрать всё
	$(COMPOSE) build --no-cache

rebuild-backend:
	$(COMPOSE) build --no-cache backend && $(COMPOSE) up -d backend

rebuild-parser:
	$(COMPOSE) build --no-cache parser && $(COMPOSE) up -d parser

rebuild-web:
	$(COMPOSE) build --no-cache web && $(COMPOSE) up -d web

shell: shell-backend     ## короткий алиас: shell в backend

shell-backend:
	$(COMPOSE) exec backend sh

shell-parser:
	$(COMPOSE) exec parser sh

migrate: migrate-backend ## короткий алиас: миграции в backend

migrate-backend:
	$(COMPOSE) exec backend alembic upgrade head

migrate-parser:
	$(COMPOSE) exec parser alembic upgrade head

# -------------------- dev --------------------
dev-up: ensure-env        ## dev-стек: postgres, db-init, backend, parser (web — локально)
	$(COMPOSE_DEV) up -d --build postgres db-init backend parser

dev-down:                 ## остановить dev-стек (volume сохраняется)
	$(COMPOSE_DEV) down

dev-restart:              ## перезапустить backend+parser (после правок в Dockerfile)
	$(COMPOSE_DEV) up -d --build backend parser

dev-logs:                 ## логи backend+parser
	$(COMPOSE_DEV) logs -f backend parser

dev-shell: dev-shell-backend ## алиас

dev-shell-backend:
	$(COMPOSE_DEV) exec backend sh

dev-shell-parser:
	$(COMPOSE_DEV) exec parser sh

# -------------------- tests --------------------
test: test-backend test-parser ## все тесты

test-backend:             ## backend-тесты (pytest в одноразовом контейнере)
	$(COMPOSE_DEV) $(TOOLS) run --rm backend-tests

test-parser:              ## parser-тесты
	$(COMPOSE_DEV) $(TOOLS) run --rm parser-tests

test-file-backend:        ## один файл: make test-file-backend F=tests/test_concurrency.py
	$(COMPOSE_DEV) $(TOOLS) run --rm backend-tests $(F)

test-file-parser:         ## один файл: make test-file-parser F=tests/test_sync.py
	$(COMPOSE_DEV) $(TOOLS) run --rm parser-tests $(F)

test-live:                ## live-тесты парсера против AIESEC (нужен AIESEC_TOKEN)
	$(COMPOSE_DEV) $(TOOLS) run --rm -e AIESEC_TOKEN=$${AIESEC_TOKEN:?нужен AIESEC_TOKEN} parser-tests -m live -o addopts=""

test-collect-backend:
	$(COMPOSE_DEV) $(TOOLS) run --rm backend-tests --collect-only -o addopts=""

test-collect-parser:
	$(COMPOSE_DEV) $(TOOLS) run --rm parser-tests --collect-only -o addopts=""

test-cov: test-cov-backend test-cov-parser

test-cov-backend:         ## backend: порог 80% (ТЗ-B)
	$(COMPOSE_DEV) $(TOOLS) run --rm backend-tests --cov-fail-under=80 --tb=no

test-cov-parser:          ## parser: порог 70%
	$(COMPOSE_DEV) $(TOOLS) run --rm parser-tests --cov-fail-under=70 --tb=no

# -------------------- openapi --------------------
openapi-snapshot:         ## пересоздать backend/openapi/backend.v1.json
	rm -f backend/openapi/backend.v1.json
	$(COMPOSE_DEV) $(TOOLS) run --rm backend-tests tests/test_openapi.py -o addopts=""

# -------------------- web (локально) --------------------
web-install:
	cd web && npm install

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

web-lint:
	cd web && npm run lint

web-test:
	cd web && npm run test# Добавить в конец Makefile (отступ перед командами обязательно TAB, не пробелы).

COMPOSE_QA := $(COMPOSE_DEV) -f docker-compose.qa.yml

test-matcher:             ## matcher: весь набор
	$(COMPOSE_QA) $(TOOLS) run --rm matcher-tests

test-matcher-main:        ## matcher: набор на коде main до исправлений (без тестов кэша, которого там ещё нет)
	$(COMPOSE_QA) $(TOOLS) run --rm matcher-tests -q --ignore tests/test_catalog_cache.py

test-matcher-smoke:       ## matcher: только smoke
	$(COMPOSE_QA) $(TOOLS) run --rm matcher-tests -q -m smoke

test-matcher-cov:         ## matcher: покрытие, порог 90%
	$(COMPOSE_QA) $(TOOLS) run --rm matcher-tests -q --cov=app --cov-report=term-missing --cov-fail-under=90

test-matcher-defects:     ## matcher: контрольные дефекты (ловят ли тесты внесённые ошибки)
	$(COMPOSE_QA) $(TOOLS) run --rm --entrypoint python matcher-tests tools/control_defects.py

test-system:              ## системные тесты всего сервиса (сначала make qa-up)
	$(COMPOSE_QA) $(TOOLS) run --rm qa-tests

test-system-smoke:        ## системные: только smoke
	$(COMPOSE_QA) $(TOOLS) run --rm qa-tests -q -m smoke

qa-up:                    ## стек для системных тестов: matcher читает базу, кэш выключен
	MATCHER_CATALOG_SOURCE=db MATCHER_CATALOG_CACHE_TTL_S=0 $(COMPOSE_QA) up -d --build postgres db-init backend parser matcher

qa-up-cache:              ## тот же стек, но кэш каталога включён на 60 секунд (для нагрузочных прогонов)
	MATCHER_CATALOG_SOURCE=db MATCHER_CATALOG_CACHE_TTL_S=60 $(COMPOSE_QA) up -d --build postgres db-init backend parser matcher

load-seed:                ## добавить в каталог синтетические вакансии: make load-seed N=1000
	$(COMPOSE_QA) $(TOOLS) run --rm --entrypoint python qa-tests seed_catalog.py --n $(or $(N),1000)

load-clean:               ## убрать синтетические вакансии из каталога
	$(COMPOSE_QA) $(TOOLS) run --rm --entrypoint python qa-tests seed_catalog.py --clean
