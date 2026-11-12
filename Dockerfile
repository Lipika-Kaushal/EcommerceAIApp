FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/data/ecommerce.db

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /app/data \
    && chown app:app /app/data

COPY --chown=app:app app.py database.py recommender.py ./
COPY --chown=app:app templates ./templates
COPY --chown=app:app static ./static

USER app

EXPOSE 8000

CMD ["gunicorn", "--bind=0.0.0.0:8000", "--workers=1", "--access-logfile=-", "app:app"]
