# Utility Desk · Qala Gas

Монорепозиторий для приёма заявок жителей в Telegram и обработки в веб-панели. Интерфейс преимущественно на казахском. **Production не содержит демонстрационных заявок и стандартных учётных записей.** Первый администратор создаётся отдельно.

## Что реализовано

- FastAPI, SQLAlchemy 2, PostgreSQL, Alembic: центральная БД и API.
- aiogram 3: подтверждение лицевого счёта, три полных FSM-сценария, календарь МПИ, фото, геолокация, предпросмотр, назад/отмена, список своих заявок.
- Next.js 16, React 19, TypeScript, Tailwind 4, компоненты shadcn/ui на Radix: Dashboard, фильтры/поиск/сортировка/pagination, карточка с lightbox и Leaflet-картой, статусы, назначения, комментарии, сотрудники, отчёты, настройки.
- Авторизация через серверную сессию, Argon2id, HttpOnly/Secure cookie, CSRF, RBAC, Redis rate limiting, audit log.
- CRITICAL для утечки, SSE обновления, транзакционный outbox и повторная доставка Telegram.
- Excel/CSV с теми же фильтрами и ограничениями доступа, защита от формул в экспорте.
- Docker Compose: PostgreSQL, Redis, backend, bot, frontend, Nginx; дополнительные одноразовый `migrate` и фоновый `worker`.

Подробности: [архитектура](docs/architecture.md), [эксплуатация](docs/operations.md), [проверки](docs/verification.md), [контракт API](packages/shared/openapi.json).

## 1. Установка

Для сервера: Linux, Docker Engine и Docker Compose v2. Практический стартовый размер — 2 CPU / 4 ГБ RAM, SSD; ёмкость диска зависит от числа фотографий. Открыты наружу только TCP 80 и 443. PostgreSQL, Redis и API не публикуют host ports.

Распакуйте проект и перейдите в его корень:

```sh
cd utility-desk
cp .env.example .env
```

В Windows для локальной разработки используйте Docker Desktop с Linux containers / WSL2. Production Compose рассчитан на Linux containers.

## 2. Создание Telegram-бота

1. Откройте официальный **@BotFather** в Telegram.
2. Выполните `/newbot`, задайте название и уникальный username.
3. Сохраните выданный токен в `.env` как `BOT_TOKEN`.
4. Не публикуйте токен. При раскрытии перевыпустите его в BotFather.

Бот использует long polling, сам регистрирует команды и снимает старый webhook без удаления pending updates. Для одного BOT_TOKEN запускайте **ровно один экземпляр bot**. Жители работают в личном чате с ботом. Автоматическая отправка фотографий должна оставаться недоступной в группах.

## 3. Конфигурация `.env`

Сгенерируйте **три независимых** секрета — для PostgreSQL, Redis и service API:

```sh
python -c "import secrets; print(secrets.token_hex(32))"
```

Повторите команду для каждого секрета. Заполните:

| Переменная | Назначение |
|---|---|
| `POSTGRES_PASSWORD` | пароль роли БД |
| `DATABASE_URL` | `postgresql+asyncpg://utility:ПАРОЛЬ@postgres:5432/utility` |
| `REDIS_PASSWORD` | пароль Redis |
| `REDIS_URL` | `redis://:ПАРОЛЬ@redis:6379/0` |
| `BOT_REDIS_URL` | `redis://:ПАРОЛЬ@redis:6379/1` |
| `BOT_API_KEY` | случайный секрет не короче 32 символов |
| `BOT_TOKEN` | токен BotFather |
| `ALLOWED_ORIGINS` | точный origin панели: `https://ваш-домен.kz`, без пути |
| `ENVIRONMENT` | `production` |
| `COOKIE_SECURE` | `true` |

Пароли в URL должны быть URL-encoded; генерируемые hex-значения не требуют кодирования. `POSTGRES_PASSWORD` и пароль в `DATABASE_URL` должны совпадать. Аналогично для Redis. `.env` находится в `.gitignore` и `.dockerignore`.

Не храните пользовательские контакты или аварийный номер в исходном коде. Они задаются в панели после подтверждения организацией.

## 4. Сборка и миграции

```sh
docker compose config --quiet
docker compose build
docker compose up -d postgres redis
docker compose run --rm migrate
```

Миграция создаёт таблицы, индексы и одну строку настроек с пустыми контактными номерами. Она **не создаёт** администратора или заявки. Схема не создаётся автоматически через `create_all` при старте production API.

Проверка соответствия схемы:

```sh
docker compose run --rm --no-deps backend alembic check
```

## 5. Первый SUPER_ADMIN

```sh
docker compose run --rm --no-deps backend python -m app.cli --email admin@your-domain.kz --name "Бас әкімші"
```

CLI дважды запросит пароль без отображения на экране. Минимум 12 символов. Пароль не передаётся аргументом командной строки. Других сотрудников можно добавить после входа в раздел «Қызметкерлер».

## 6. HTTPS и домен

1. Направьте DNS A/AAAA вашего домена на сервер.
2. Получите TLS-сертификат через ACME-клиент вашей инфраструктуры (например, Certbot с DNS challenge). Настройте автоматическое продление.
3. Создайте `certs/` и поместите туда **реальные** `fullchain.pem` и `privkey.pem`. Закрытый ключ должен быть доступен только уполномоченным администраторам сервера.
4. Укажите этот же origin в `ALLOWED_ORIGINS`.
5. Nginx читает сертификаты из `certs/`, перенаправляет HTTP на HTTPS, включает HSTS и закрывает `/api/internal` снаружи.

Для тестового домена можно использовать локально доверенный сертификат. Не отключайте проверку TLS в production. После продления сертификата обновите файлы в `certs/` и выполните `docker compose exec nginx nginx -s reload`.

## 7. Запуск

```sh
docker compose up -d
docker compose ps
docker compose logs --tail=100 backend bot worker nginx
```

Откройте `https://ваш-домен.kz`, войдите под созданным администратором. Проверьте «Баптаулар»: название, контактный и **подтверждённый** аварийный номер, тексты уведомлений, максимальный размер фото.

Отправьте `/start` вашему боту и выполните по одной тестовой заявке каждого типа. Убедитесь, что аварийная заявка выделена и смена статуса доставляет уведомление в Telegram. Систему можно вводить в эксплуатацию после этой проверки на вашем токене и домене.

## 8. Структура

```text
apps/
  backend/
    app/                 # models, schemas, services, repositories, api, auth,
                         # database, storage, notifications, config, cli
    migrations/          # зафиксированная начальная Alembic migration
  telegram-bot/
    bot/                 # handlers, keyboards, states, middlewares, services
  admin-web/
    src/app/             # Next.js App Router
    src/components/      # страницы и UI
    src/hooks/           # запросы с отменой
    src/services/        # API/CSRF/download
    src/types/           # TypeScript contract
packages/shared/         # OpenAPI
docker/                  # Dockerfiles, Nginx
docs/                    # архитектура, проверки, эксплуатация
tests/                   # unit/integration/FSM/concurrency
.github/workflows/ci.yml # PostgreSQL + Redis + browser tests
```

Логические слои backend и bot представлены отдельными Python-модулями; их можно развивать в пакеты без изменения границ API.

## 9. API и права

Внешний префикс — `/api`: `POST /api/auth/login`, `GET /api/applications` и т. д. Все endpoints из ТЗ реализованы; добавлены `/auth/me`, `/auth/logout`, `/events`, `/files/{id}`, `/reports`, `/reports/export`, `/settings`, `/audit`, `/operations`.

Вход возвращает `csrf_token`; cookie выставляется сервером. Для POST/PATCH нужен `X-CSRF-Token` и разрешённый `Origin`. Сессионный токен никогда не хранится в localStorage. Сессия действует 8 часов; logout и деактивация сотрудника отзывают её. Для изменения заявки передавайте её текущую `version`; при конфликте API отвечает `409`.

OPERATOR видит только назначенные себе заявки, файлы, историю и отчёты. DISPATCHER работает со всеми заявками и назначает исполнителей. SUPER_ADMIN дополнительно управляет сотрудниками, настройками и повторной доставкой из dead-letter очереди.

Полный контракт — `packages/shared/openapi.json`. В режиме разработки `/docs` backend показывает Swagger; в production интерактивная документация отключена.

## 10. Тесты и локальная разработка

Python 3.12+, Node.js 24. Версии Python-зависимостей зафиксированы в `requirements.lock` и `requirements-dev.lock`, npm — в `package-lock.json`.

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.lock
pytest -q
ruff check apps tests scripts
cd apps/admin-web
npm ci
npm run build
```

Без `TEST_DATABASE_URL` unit/integration тесты работают на изолированной SQLite, тесты блокировок пропускаются. Для проверки PostgreSQL задайте `TEST_DATABASE_URL` на **отдельную одноразовую БД**, имя которой содержит `test` или `e2e`: тесты пересоздают таблицы. Никогда не направляйте эту переменную на production.

Полный CI запускает тесты с PostgreSQL и Redis, применяет Alembic, создаёт только E2E-администратора в тестовой БД, собирает Next.js и выполняет `npm run test:e2e`. Браузерный тест создаёт заявки через API; подмена ответов API не используется.

Для разработки без контейнеров:

- Укажите локальные PostgreSQL/Redis URL, `ENVIRONMENT=development`, `COOKIE_SECURE=false`, `ALLOWED_ORIGINS=http://127.0.0.1:3000`, абсолютный `UPLOAD_DIR`.
- Из `apps/backend`: `alembic upgrade head`, затем `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
- Из `apps/admin-web`: `npm run dev`. Next.js проксирует `/api` на `127.0.0.1:8000`. `INTERNAL_API_URL` меняет адрес прокси; для production build задаётся до сборки.
- Из `apps/telegram-bot`: `python -m bot.main` с `BACKEND_URL=http://127.0.0.1:8000/api/internal` и Redis DB 1.
- Из `apps/backend` отдельным процессом: `python -m app.notifications` с `BOT_TOKEN`.

В Windows с ограничением дочерних процессов для `next build` можно задать `NEXT_WORKER_THREADS=true`. Проверка типов при этом остаётся включённой.

## 11. Production deployment

Подготовьте секреты, домен и TLS; выполните миграции и создайте администратора; поднимите Compose; выполните приёмочные сценарии Telegram → панель → уведомление. Настройте резервные копии БД и фото, мониторинг health endpoints и очереди, ротацию логов, срок хранения персональных данных. См. [runbook](docs/operations.md).

**Границы текущей реализации:** `verify_personal_account` проверяет только формат 6–20 цифр, не существование абонента. Хранилище фотографий — приватный volume для одного Docker-хоста. При нескольких хостах нужен общий private object storage. Telegram доставка — at-least-once, поэтому после редкого сбоя между отправкой и commit возможен повтор уведомления. Правила повторного открытия закрытых заявок не введены: COMPLETED/REJECTED являются конечными статусами.

Живой Telegram-токен и TLS-домен не входят в поставку. Фактически выполненные проверки и ограничения среды перечислены в [verification.md](docs/verification.md).
