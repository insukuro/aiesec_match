FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY services/aiesec-parser/requirements.txt services/aiesec-parser/requirements-dev.txt ./
RUN pip install -r requirements.txt -r requirements-dev.txt

# код НЕ копируем — он монтируется через compose для hot-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--workers", "1"]