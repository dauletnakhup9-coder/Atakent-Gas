# Газ қызметі — Өтінімдерді басқару жүйесі

Production-ready system for accepting resident requests via a Telegram bot (Kazakh-language
UI) and processing them by staff through a web admin dashboard. Monorepo with a FastAPI
backend, an aiogram 3 Telegram bot, and a Next.js admin panel, all backed by one PostgreSQL
database.

## Architecture

```
Resident → Telegram Bot → Backend API → PostgreSQL → Admin Dashboard → Operator
                              │                              ▲
                              └────────── WebSocket / Redis ─┘  (real-time updates)
```

- **apps/backend** — FastAPI + SQLAlchemy 2 (async) + Alembic + JWT auth + RBAC + rate
  limiting + WebSocket broadcast + Telegram notifications.
- **apps/telegram-bot** — aiogram 3 bot, Kazakh-language FSM flows, talks to the backend
  over a small internal API (`/api/bot/*`) authenticated with a shared secret.
- **apps/admin-web** — Next.js (App Router) + TypeScript + Tailwind CSS, shadcn/ui-style
  components, live updates over WebSocket, Leaflet map, photo lightbox, CSV/Excel reports.
- **docker/nginx** — reverse proxy in front of the dashboard and API (single origin, so the
  browser only ever talks to one host).

Both the bot and the dashboard share one backend/database — there is no duplicated state and
no mock data.

## 1. Prerequisites

- Docker and Docker Compose v2
- A Telegram account (to create the bot)
- (For local, non-Docker development only) Python 3.12+, Node.js 20+, PostgreSQL 16, Redis 7

## 2. Creating the Telegram Bot via BotFather

1. Open Telegram and start a chat with **@BotFather**.
2. Send `/newbot` and follow the prompts (choose a name and a unique username ending in `bot`).
3. BotFather replies with an API token that looks like `123456789:AAExampleTokenValue`.
   This is your `BOT_TOKEN`.
4. Optional but recommended: send `/setcommands` to BotFather and register:
   ```
   start - Жаңа өтінім / басты мәзір
   ```

## 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in, at minimum:

| Variable | Description |
|---|---|
| `POSTGRES_PASSWORD` | Strong password for the PostgreSQL user |
| `SECRET_KEY` | Random secret used to sign admin JWTs — generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `BOT_INTERNAL_API_KEY` | Random shared secret between the bot and backend (same command as above) |
| `BOT_TOKEN` | The token from BotFather (step 2) |
| `CORS_ORIGINS` | Origins allowed to call the API from a browser (e.g. your dashboard domain) |

`DATABASE_URL` is assembled automatically by `docker-compose.yml` from the `POSTGRES_*`
variables — you don't need to set it yourself when running via Docker.

## 4. Running database migrations

Migrations run automatically on backend container startup (see `apps/backend/Dockerfile`'s
`CMD`). To run them manually against a running stack:

```bash
docker compose run --rm backend alembic upgrade head
```

For local (non-Docker) development:

```bash
cd apps/backend
python -m venv .venv && .venv/Scripts/activate   # or `source .venv/bin/activate` on Linux/Mac
pip install -r requirements.txt
cp .env.example .env   # then edit DATABASE_URL to point at your local Postgres
alembic upgrade head
```

## 5. Creating the first SUPER_ADMIN

Once the database is migrated:

```bash
docker compose run --rm backend python create_super_admin.py \
  --email admin@example.com --password "a-strong-password" --name "Admin"
```

(For local dev without Docker: `python create_super_admin.py --email ... --password ... --name ...`
from inside `apps/backend` with the venv activated.)

Log into the dashboard at `http://localhost` (or your domain) with this email/password.
Use the dashboard's **Қызметкерлер** page to create DISPATCHER/OPERATOR accounts afterwards.

## 6. Running with Docker

```bash
docker compose up --build -d
docker compose logs -f
```

Services:
- `http://localhost` — admin dashboard (proxied through nginx)
- `http://localhost/api` — backend REST API
- The bot starts polling Telegram automatically once `BOT_TOKEN` is valid.

Stop everything with `docker compose down` (add `-v` to also drop the database volume).

## 7. Local development without Docker

**Backend:**
```bash
cd apps/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Telegram bot:**
```bash
cd apps/telegram-bot
pip install -r requirements.txt
python -m bot.main
```

**Admin dashboard:**
```bash
cd apps/admin-web
npm install
npm run dev
```

## 8. Running tests

```bash
# Backend (35 tests: auth, RBAC, application creation, FSM-adjacent validation,
# file upload validation, status history, gas-leak critical priority)
cd apps/backend
pip install -r requirements.txt
pytest

# Telegram bot (validators, API client payload/error handling)
cd apps/telegram-bot
pip install -r requirements.txt
pytest

# Admin dashboard (type-check + production build)
cd apps/admin-web
npm install
npm run build
```

## 9. HTTPS / domain setup for production

The bundled `docker/nginx/nginx.conf` ships with an HTTP server block and a commented-out
HTTPS server block.

1. Point your domain's DNS `A` record at the server running this stack.
2. Obtain a certificate, e.g. with [certbot](https://certbot.eff.org/) in standalone mode:
   ```bash
   docker compose stop nginx
   certbot certonly --standalone -d your-domain.example
   cp /etc/letsencrypt/live/your-domain.example/fullchain.pem docker/nginx/certs/
   cp /etc/letsencrypt/live/your-domain.example/privkey.pem docker/nginx/certs/
   ```
3. Uncomment the HTTPS `server` block in `docker/nginx/nginx.conf`, set `server_name` to your
   domain, and update `CORS_ORIGINS` / `NEXT_PUBLIC_API_BASE_URL` in `.env` if the dashboard is
   served from a different origin than the API.
4. `docker compose up -d --force-recreate nginx`.
5. Set up certificate renewal (`certbot renew`) via cron or a systemd timer.

## 10. Production deployment checklist

- [ ] Strong, unique `SECRET_KEY`, `BOT_INTERNAL_API_KEY`, and `POSTGRES_PASSWORD` (never reuse
      the example values).
- [ ] `.env` is **not** committed to Git (already covered by `.gitignore`).
- [ ] `CORS_ORIGINS` restricted to your real dashboard domain(s).
- [ ] HTTPS enabled (section 9) — the JWT bearer token and admin credentials must not travel
      over plain HTTP in production.
- [ ] Database volume (`postgres_data`) included in your backup strategy.
- [ ] `uploads_data` volume (resident photos) included in your backup strategy.
- [ ] Telegram bot's emergency phone number and organization contact set correctly under
      **Баптаулар** (Settings) before go-live — these are shown to residents reporting gas leaks.
- [ ] Consider a process supervisor / restart policy for the `bot` service beyond Docker's
      `restart: unless-stopped` if you need alerting on crashes.

## Project structure

```
/apps
  /backend        FastAPI service (models, schemas, repositories, services, api, auth)
  /telegram-bot   aiogram 3 bot (handlers, keyboards, states, middlewares, services)
  /admin-web      Next.js admin dashboard (app router, components, lib)
/docker
  /nginx          Reverse proxy config + TLS certs (not committed)
/docs             Additional documentation
docker-compose.yml
.env.example
```

## Notes on design decisions

- **Application numbers** use the format `REQ-YYYYMMDD-#####` where the numeric suffix is the
  application's database id (zero-padded), guaranteeing uniqueness without a race-prone
  per-day counter.
- **Personal account verification** (`verify_personal_account` in
  `apps/backend/app/services/validators.py`) currently checks format only. It is isolated in
  its own function specifically so a real subscriber-database/API check can be plugged in
  later without touching call sites.
- **Photo storage**: the bot never downloads files itself — it passes Telegram `file_id`s to
  the backend, which downloads, validates (magic bytes + Pillow decode + size/MIME
  allow-list), and stores them. This keeps all file handling and validation in one place.
- **Real-time updates** go through Redis pub/sub → WebSocket, so the dashboard stays in sync
  even when running multiple backend replicas.
