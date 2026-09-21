FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY apps/telegram-bot/requirements.lock /srv/requirements.lock
RUN pip install --no-cache-dir -r requirements.lock && useradd --uid 10001 --create-home app
COPY --chown=app:app apps/telegram-bot /srv
USER app
CMD ["python", "-m", "bot.main"]
