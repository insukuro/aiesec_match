# aiesec-platform (монорепо)


## Быстрый старт

```bash
cp .env.example .env     # заполнить AIESEC_TOKEN, PARSER_API_KEY, POSTGRES_PASSWORD
make up                  # postgres + парсер; первый full-sync стартует сам
curl -H "X-API-Key: $PARSER_API_KEY" localhost:8001/opportunities/stats
```

Новый сервис: папка в `services/`, блок в `docker-compose.yml`, строка `create_db` в `infra/postgres/init/01-databases.sh`.
Остальные сервисы ходят к парсеру по `http://aiesec-parser:8000` внутри сети `backend`.
