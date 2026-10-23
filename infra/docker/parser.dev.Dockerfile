# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/srv

WORKDIR /srv

# dev-инструменты, чтобы потом удобно дебажить в контейнере
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Сначала зависимости — отдельным слоем, чтобы кэш работал при правках кода
COPY parser/requirements.txt parser/requirements-dev.txt ./
RUN pip install -r requirements.txt -r requirements-dev.txt

# Код и тесты монтируются через volume в compose (docker-compose.dev.yml),
# но копируем — на случай запуска без bind-mount.
COPY parser/ /srv/

EXPOSE 8000

# В dev НЕ применяем миграции и НЕ фиксируем команду запуска —
# всё это делает compose (entrypoint/command), чтобы hot-reload и
# тесты можно было гонять одной и той же сборкой.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--reload"]