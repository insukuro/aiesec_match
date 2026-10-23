# aiesec-platform (монорепо)


## Быстрый старт

```bash
cp .env.example .env     # заполнить AIESEC_TOKEN, PARSER_API_KEY, POSTGRES_PASSWORD
make up                  # postgres + парсер; первый full-sync стартует сам
```


```
aiesec_match
├─ .dockerignore
├─ Makefile
├─ README.md
├─ docker-compose.dev.yml
├─ docker-compose.yml
├─ docs
│  ├─ README.md
│  └─ testing.md
├─ htmlcov
├─ infra
│  ├─ docker
│  │  ├─ parser.Dockerfile
│  │  └─ parser.dev.Dockerfile
│  └─ postgres
│     ├─ bootstrap.sql
│     └─ init
│        └─ 01-databases.sh
├─ parser
│  ├─ .coveragerc
│  ├─ alembic.ini
│  ├─ app
│  │  ├─ __init__.py
│  │  ├─ api
│  │  │  ├─ __init__.py
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
│  │  │  ├─ gapfill.py
│  │  │  ├─ ingest.py
│  │  │  ├─ queries.py
│  │  │  ├─ service.py
│  │  │  ├─ state.py
│  │  │  └─ strategies.py
│  │  └─ tokens.py
│  ├─ migrations
│  │  ├─ script.py.mako
│  │  └─ versions
│  │     └─ 0001_initial.py
│  ├─ pytest.ini
│  ├─ requirements-dev.txt
│  ├─ requirements.txt
│  ├─ targets.json
│  └─ tests
│     ├─ __init__.py
│     ├─ conftest.py
│     ├─ test_api.py
│     ├─ test_auth.py
│     ├─ test_live.py
│     ├─ test_normalize.py
│     ├─ test_openapi.py
│     └─ test_sync.py
└─ scripts
   └─ smoke.sh

```