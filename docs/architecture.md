# Архитектура Utility Desk

## Компоненты и границы доверия

```
Telegram → aiogram / Redis FSM → internal API → PostgreSQL
                                              ↑       ↓ outbox
Browser → HTTPS / Nginx → Next.js → Admin API ──┘       Telegram Bot API
                             ↑ SSE / persisted events
```

Backend — единственный владелец БД. Bot не имеет DATABASE_URL, использует отдельный BOT_API_KEY. Browser не получает этот ключ или BOT_TOKEN. Файлы хранятся в приватном Docker volume и выдаются только после авторизации и проверки доступа к заявке. Redis хранит FSM и счётчики rate limit. PostgreSQL хранит заявки, сессии, историю, события и очередь уведомлений.

## Схема

- users: уникальный Telegram ID, профиль, timestamps.
- admins: уникальный email, Argon2id password hash, роль, active.
- admin_sessions: SHA-256 opaque session token, CSRF secret, expiry.
- applications: sequence ID, уникальный REQ-YYYYMMDD-NNNNN, FK user/admin, тип, статус, приоритет, координаты, дата МПИ, version для optimistic concurrency.
- application_files: предварительно загруженные изображения с владельцем Telegram ID; application_id nullable до подтверждения; уникальный storage key. После подтверждения прикрепление атомарно.
- application_history: переходы статусов, назначения и комментарии; public_comment отдельно от внутреннего комментария.
- audit_logs: действия сотрудников и входы без паролей, токенов и содержимого фотографий.
- outbox: доставка Telegram, retry/backoff и dead-letter после 12 попыток; событие и заявка записываются одной транзакцией.
- realtime_events: долговечные SSE события с монотонным ID, восстановление Last-Event-ID.
- system_settings: одна строка, название, телефоны, шаблоны статусов, лимит фото.

## Инварианты

Заявка появляется только после финального подтверждения. idempotency_key UUID переживает повтор отправки ботом: один пользователь + один ключ → одна заявка. Формат счёта не означает подтверждение существования абонента. Для MPI нужна дата сегодня или позже в Asia/Qyzylorda; для неисправности — фото и координаты; для утечки — два разных фото и координаты, priority всегда CRITICAL. Допустимы переходы NEW → IN_PROGRESS/REJECTED, IN_PROGRESS → COMPLETED/REJECTED. Терминальные заявки не открываются повторно.

## RBAC

| Действие | SUPER_ADMIN | DISPATCHER | OPERATOR |
|---|---|---|---|
| Все заявки, отчёты | да | да | только назначенные себе |
| Статус, комментарий | да | да | только назначенные себе |
| Назначение, приоритет | да | да | нет |
| Список сотрудников | да | да | только своё имя |
| Создание/деактивация сотрудников | да | нет | нет |
| Изменение настроек | да | нет | нет |

Защита: HttpOnly Secure SameSite=Lax cookie, серверные отзываемые сессии (8 часов), CSRF header + проверка Origin для mutations, Argon2id, Redis atomic rate limits, ограниченный CORS, запрет публичной раздачи файлов, Pillow decode/normalize, EXIF stripping, лимиты Nginx/API, отсутствие секретов в Git. Service API принимает Telegram user ID только от доверенного бота; handlers разрешены в private chats.

## Доставка и эксплуатация

Notification worker использует SELECT FOR UPDATE SKIP LOCKED. Доставка at-least-once: если Telegram принял сообщение, но commit не состоялся, возможен повтор. Это ограничение Telegram sendMessage. SSE повторно читает БД, поэтому рестарт backend не теряет события; после reconnect клиент обновляет данные. В production нужен один polling bot; масштабировать backend можно независимо. Файловый volume должен быть общим для backend/worker (для нескольких хостов нужен private object storage adapter).

Данные сохраняются в volumes. Резервировать БД и uploads совместно; retention должен утвердить владелец персональных данных. Аварийный номер по умолчанию пустой и задаётся SUPER_ADMIN после подтверждения организацией. Бот показывает предупреждение даже без номера и не является заменой аварийной службы.
