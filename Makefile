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

# Сервисы, к которым применимы generic-цели (up/down/logs/shell/migrate/tests).
# web вынесен отдельно в web-* (нет shell/migrate, тесты через npm).
SERVICES := backend parser matcher

# -------------------- phony --------------------
.PHONY: help \
        up down logs ps psql rebuild \
        shell migrate \
        dev-up dev-down dev-restart dev-logs dev-shell \
        test test-file test-cov test-collect test-live \
        openapi-snapshot \
        web-install web-dev web-build web-lint web-test web-coverage \
        $(addprefix up-,$(SERVICES)) \
        $(addprefix rebuild-,$(SERVICES)) \
        $(addprefix shell-,$(SERVICES)) \
        $(addprefix migrate-,$(SERVICES)) \
        $(addprefix test-,$(SERVICES)) \
        $(addprefix test-cov-,$(SERVICES)) \
        $(addprefix test-collect-,$(SERVICES)) \
        $(addprefix test-file-,$(SERVICES))

# -------------------- help --------------------
help:            ## показать список команд
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "\033[36m%-28s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ==========================================================
#  GENERIC: работают для любого SERVICE из $(SERVICES)
#  Пример: make up SERVICE=backend   |   make up-backend
# ==========================================================

up: ensure-env            ## up [SERVICE=...]: поднять (все или один)
	$(COMPOSE) up -d --build $(SERVICE)

down:                     ## down [SERVICE=...]: остановить
	$(COMPOSE) down $(SERVICE)

logs:                     ## logs [SERVICE=...]: логи
	$(COMPOSE) logs -f $(SERVICE)

ps:                       ## ps: статус контейнеров
	$(COMPOSE) ps

psql:                     ## psql в контейнер postgres
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-platform} $${APP_DB:-aiesec_match}

rebuild:                  ## rebuild [SERVICE=...]: пересобрать без кэша и перезапустить
	$(COMPOSE) build --no-cache $(SERVICE)
	$(COMPOSE) up -d $(SERVICE)

shell:                    ## shell SERVICE=backend|parser|matcher
	@test -n "$(SERVICE)" || (echo "укажите SERVICE=backend|parser|matcher" && exit 1)
	$(COMPOSE) exec $(SERVICE) sh

migrate:                  ## migrate SERVICE=backend|parser
	@test -n "$(SERVICE)" || (echo "укажите SERVICE=backend|parser" && exit 1)
	$(COMPOSE) exec $(SERVICE) alembic upgrade head

# --- dev ---
dev-up: ensure-env        ## dev-стек (postgres, db-init, backend, parser, matcher)
	$(COMPOSE_DEV) up -d --build postgres db-init backend parser matcher

dev-down:
	$(COMPOSE_DEV) down

dev-restart:              ## dev-restart [SERVICE=...]
	$(COMPOSE_DEV) up -d --build $(or $(SERVICE),backend parser)

dev-logs:
	$(COMPOSE_DEV) logs -f $(or $(SERVICE),backend parser)

dev-shell:                ## dev-shell SERVICE=...
	@test -n "$(SERVICE)" || (echo "укажите SERVICE=backend|parser|matcher" && exit 1)
	$(COMPOSE_DEV) exec $(SERVICE) sh

# --- tests ---
test:                     ## test [SERVICE=...]: все тесты или тесты сервиса
ifeq ($(SERVICE),)
	$(MAKE) test-backend test-parser test-matcher test-web
else ifeq ($(SERVICE),web)
	$(MAKE) web-test
else
	$(COMPOSE_DEV) $(TOOLS) run --rm $(SERVICE)-tests
endif

test-file:                ## test-file SERVICE=backend F=tests/...: один файл
	@test -n "$(SERVICE)" -a -n "$(F)" || (echo "SERVICE=... F=tests/..." && exit 1)
ifeq ($(SERVICE),web)
	cd web && npx vitest run $(F)
else
	$(COMPOSE_DEV) $(TOOLS) run --rm $(SERVICE)-tests $(F)
endif

test-collect:             ## test-collect SERVICE=backend|parser
	@test -n "$(SERVICE)" || (echo "укажите SERVICE" && exit 1)
	$(COMPOSE_DEV) $(TOOLS) run --rm $(SERVICE)-tests --collect-only -o addopts=""

test-cov:                 ## test-cov [SERVICE=...]: coverage (порог — в pytest.ini)
ifeq ($(SERVICE),)
	$(MAKE) test-cov-backend test-cov-parser test-cov-matcher web-coverage
else ifeq ($(SERVICE),web)
	$(MAKE) web-coverage
else
	$(COMPOSE_DEV) $(TOOLS) run --rm $(SERVICE)-tests --tb=no
endif

test-live:                ## live-тесты парсера против AIESEC
	$(COMPOSE_DEV) $(TOOLS) run --rm -e AIESEC_TOKEN=$${AIESEC_TOKEN:?нужен AIESEC_TOKEN} parser-tests -m live -o addopts=""

# ==========================================================
#  PER-SERVICE АЛИАСЫ (тонкие, для tab-completion)
#  Генерируются из $(SERVICES) — добавь сервис в SERVICES,
#  получишь up-<svc>, rebuild-<svc>, shell-<svc>, test-<svc> и т.д.
# ==========================================================
define per_service_aliases
up-$(1):            ; $$(MAKE) up            SERVICE=$(1)
rebuild-$(1):       ; $$(MAKE) rebuild       SERVICE=$(1)
shell-$(1):         ; $$(MAKE) shell         SERVICE=$(1)
test-$(1):          ; $$(MAKE) test          SERVICE=$(1)
test-cov-$(1):      ; $$(MAKE) test-cov      SERVICE=$(1)
test-collect-$(1):  ; $$(MAKE) test-collect  SERVICE=$(1)
test-file-$(1):     ; $$(MAKE) test-file     SERVICE=$(1) F=$$(F)
endef

# migrate применим только к сервисам с alembic (backend, parser)
$(eval $(call per_service_aliases,backend))
$(eval $(call per_service_aliases,parser))
$(eval $(call per_service_aliases,matcher))
migrate-backend:    ; $(MAKE) migrate SERVICE=backend
migrate-parser:     ; $(MAKE) migrate SERVICE=parser

# ==========================================================
#  OPENAPI
# ==========================================================
openapi-snapshot:         ## пересоздать backend/openapi/backend.v1.json
	rm -f backend/openapi/backend.v1.json
	$(COMPOSE_DEV) $(TOOLS) run --rm backend-tests tests/test_openapi.py -o addopts=""

# ==========================================================
#  WEB (локально, без docker)
# ==========================================================
web-install:  ; cd web && npm install
web-dev:      ; cd web && npm run dev
web-build:    ; cd web && npm run build
web-lint:     ; cd web && npm run lint
web-test:     ; cd web && npm run test -- --run
web-coverage: ; cd web && npm run coverage