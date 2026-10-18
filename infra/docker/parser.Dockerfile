FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY parser/requirements.txt .
RUN pip install -r requirements.txt

COPY parser/app ./app
COPY parser/targets.json .
COPY parser/alembic.ini .
COPY parser/migrations ./migrations

# ОДИН воркер: планировщик живёт внутри процесса.
# Миграции — на старте, alembic идемпотентен.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]