# Architecture

## Data flow

```
Resident (Telegram)
  → Telegram Bot (aiogram FSM)
  → Backend API  POST /api/bot/applications   (X-Internal-Api-Key auth)
  → PostgreSQL   (applications, application_files, application_history)
  → Redis pub/sub → WebSocket  /api/ws/applications
  → Admin Dashboard (Next.js)                 (JWT bearer auth)
  → Operator changes status/assignee
  → Backend API  PATCH /api/applications/{id}/status
  → Telegram Bot API sendMessage               (resident notified)
```

The bot and the dashboard never talk to the database directly or to each other — everything
goes through the FastAPI backend, which is the single source of truth.

## Database schema (see `apps/backend/app/models/`)

- **users** — one row per Telegram user (`telegram_user_id` unique).
- **admins** — dashboard accounts (`role`: SUPER_ADMIN / DISPATCHER / OPERATOR).
- **applications** — one row per request; `application_type`, `status`, `priority`,
  `requested_date` (MPI only), `latitude`/`longitude` (meter + gas leak only).
- **application_files** — photos, linked to an application, storing both the original
  Telegram `file_id` and the backend-managed `storage_url`.
- **application_history** — append-only log of every status transition, who made it (nullable
  for the initial system-created "NEW" entry), and any comment.
- **system_settings** — key/value store for organization name, contact/emergency phone
  numbers, notification text templates, and the max upload size.
- **audit_logs** — security-relevant admin actions (login, status change, assignment) with
  actor, IP, and timestamp.

## Authentication & authorization

- **Admin dashboard**: email + password → bcrypt hash check → short-lived JWT (HS256) bearer
  token. No cookies, so no CSRF surface. `GET /auth/me` re-validates the token on page load.
- **Telegram bot → backend**: a static shared secret (`X-Internal-Api-Key` header) — the bot
  is a trusted internal service, not an end-user client, so it doesn't need per-user tokens.
- **RBAC**: enforced server-side via FastAPI dependencies
  (`app/auth/rbac.py`): `require_any_admin`, `require_dispatcher_or_above`,
  `require_super_admin`. The frontend also hides UI it knows the current role can't use, but
  that is a UX convenience only — the backend is the actual enforcement point.

## Real-time updates

`app/services/realtime.py` publishes application lifecycle events to a Redis channel. Every
backend replica subscribes to that channel and fans events out to its own locally-connected
WebSocket clients. This means dashboard updates work correctly even when the backend is
horizontally scaled behind a load balancer — a single Postgres write is not tied to a single
WebSocket connection.

## Why application numbers look like `REQ-20260915-00007`

The numeric suffix is the application's database primary key (zero-padded), not a per-day
counter. A per-day counter reset at midnight would need its own row-locking logic to stay
race-free under concurrent inserts; keying off the existing auto-increment id gets uniqueness
for free while still reading naturally in the `REQ-YYYYMMDD-#####` format the bot and
dashboard display to users.
