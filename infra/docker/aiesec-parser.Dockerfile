FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY services/aiesec-parser/requirements.txt .
RUN pip install -r requirements.txt

COPY services/aiesec-parser/app ./app
COPY services/aiesec-parser/targets.json .

# ОДИН воркер: планировщик живёт внутри процесса
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]