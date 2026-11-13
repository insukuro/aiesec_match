FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /srv

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY infra/requirements/ /srv/requirements/

ARG REQUIREMENTS=/srv/requirements/backend.txt
RUN pip install --no-cache-dir -r ${REQUIREMENTS}

COPY backend /srv
RUN mkdir -p /srv/openapi

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --retries=5 --start-period=20s \
  CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

# Ждём БД, накатываем миграции, проверяем, что схема core существует.
CMD ["sh", "-c", "\
  python -c 'import time, psycopg; \
for _ in range(30): \
    try: \
        psycopg.connect(\"host=postgres dbname=aiesec_match user=backend_writer password=backend\").close(); break \
    except Exception as e: \
        print(\"waiting for postgres:\", e); time.sleep(1)' && \
  alembic upgrade head && \
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]