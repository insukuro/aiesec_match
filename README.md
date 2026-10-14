# aiesec-platform (монорепо)


## Быстрый старт

```bash
cp .env.example .env     # заполнить AIESEC_TOKEN, PARSER_API_KEY, POSTGRES_PASSWORD
make up                  # postgres + парсер; первый full-sync стартует сам
curl -H "X-API-Key: $PARSER_API_KEY" localhost:8001/opportunities/stats
```

Новый сервис: папка в `services/`, блок в `docker-compose.yml`, строка `create_db` в `infra/postgres/init/01-databases.sh`.
Остальные сервисы ходят к парсеру по `http://aiesec-parser:8000` внутри сети `backend`.

```
aiesec_match
├─ .dockerignore
├─ .env
├─ .env.example
├─ Makefile
├─ docker-compose.dev.yml
├─ docker-compose.yml
├─ docs
│  ├─ README.md
│  └─ testing.md
├─ infra
│  ├─ docker
│  │  ├─ aiesec-parser.Dockerfile
│  │  └─ aiesec-parser.dev.Dockerfile
│  └─ postgres
│     └─ init
│        └─ 01-databases.sh
├─ scripts
│  └─ smoke.sh
└─ services
   └─ aiesec-parser
      ├─ app
      │  ├─ __init__.py
      │  ├─ client.py
      │  ├─ config.py
      │  ├─ main.py
      │  ├─ models.py
      │  ├─ normalize.py
      │  └─ sync.py
      ├─ pytest.ini
      ├─ requirements-dev.txt
      ├─ requirements.txt
      ├─ targets.json
      └─ tests
         ├─ __init__.py
         ├─ conftest.py
         ├─ test_api.py
         ├─ test_live.py
         ├─ test_normalize.py
         └─ test_sync.py

```