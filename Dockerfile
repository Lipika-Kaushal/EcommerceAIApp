FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/data/service.db \
    APP_MODULE=app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --ingroup app app \
    && mkdir -p /data \
    && chown app:app /data

COPY --chown=app:app app.py catalog_data.py recommender.py ./
COPY --chown=app:app microservices ./microservices
COPY --chown=app:app templates ./templates
COPY --chown=app:app static ./static

USER app

EXPOSE 8000

CMD ["sh", "-c", "exec gunicorn --bind=0.0.0.0:8000 --workers=1 --access-logfile=- \"${APP_MODULE}:app\""]
