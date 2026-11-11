FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /srv

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем каталог целиком — тогда `-r parser.txt` внутри parser-dev.txt
# резолвится относительно /srv/requirements/parser.txt
COPY infra/requirements/ /srv/requirements/

ARG REQUIREMENTS=/srv/requirements/parser.txt
RUN pip install --no-cache-dir -r ${REQUIREMENTS}

COPY parser/app ./app
COPY parser/targets.json .
COPY parser/alembic.ini .
COPY parser/migrations ./migrations

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --retries=5 --start-period=20s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]