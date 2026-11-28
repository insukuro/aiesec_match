FROM python:3.16-rc-alpine3.24
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

COPY infra/requirements/ /srv/requirements/
ARG REQUIREMENTS=/srv/requirements/matcher.txt
RUN pip install --no-cache-dir -r ${REQUIREMENTS}

COPY matcher /srv

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]