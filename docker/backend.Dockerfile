FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY apps/backend/requirements.lock /srv/requirements.lock
RUN pip install --no-cache-dir -r requirements.lock && useradd --uid 10001 --create-home app && mkdir -p /data/uploads && chown -R app:app /data
COPY --chown=app:app apps/backend /srv
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*", "--no-access-log"]
