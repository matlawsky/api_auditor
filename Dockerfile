FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
RUN useradd --create-home --uid 10001 app
COPY --chown=app:app . .
RUN mkdir -p /app/staticfiles \
    && chown -R app:app /app/staticfiles
USER app
RUN DJANGO_SECRET_KEY=build-only \
    DB_PASSWORD=build-only \
    CELERY_BROKER_URL=amqp://unused \
    python manage.py collectstatic --noinput
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
FROM runtime AS test
USER root
RUN pip install --no-cache-dir --require-hashes -r requirements-dev.lock
USER app
CMD ["pytest", "-q"]