# Health-алерты в Telegram

Изолированный сервис мониторинга. Не импортирует код CityBoost и не меняет
backend/frontend. Проверяет:

- `backend` — `http://backend:8000/health`;
- `nginx` — `http://nginx/health`;
- `db` — TCP `db:5432`;
- `redis` — TCP `redis:6379`;
- опционально внешний URL (`HEALTH_ALERT_EXTERNAL_URL`).

При проблеме отправляет сообщение в Telegram, при восстановлении — сообщение
о восстановлении. Пока проблема не устранена, повторяет алерт раз в
`HEALTH_ALERT_REPEAT_MINUTES` минут.

## Что нужно заполнить в `.env`

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=123456789
```

Опционально:

```env
# Если алерты в топик Telegram-группы
TELEGRAM_MESSAGE_THREAD_ID=123

# Публичный URL (например, Cloudflare Tunnel) — проверять доступность снаружи
HEALTH_ALERT_EXTERNAL_URL=https://example.com/health

# Тонкая настройка (значения по умолчанию)
HEALTH_ALERT_INTERVAL_SECONDS=60
HEALTH_ALERT_FAILURE_THRESHOLD=2
HEALTH_ALERT_REPEAT_MINUTES=30
HEALTH_ALERT_STARTUP_DELAY_SECONDS=20
HEALTH_ALERT_TIMEZONE=Europe/Minsk
```

## Как получить токен и chat_id

1. В Telegram напишите `@BotFather` → `/newbot` → получите токен вида
   `123456789:AA...`.
2. Напишите своему боту любое сообщение (иначе он не сможет вам писать).
3. Откройте в браузере:
   `https://api.telegram.org/bot<ТОКЕН>/getUpdates`
   и найдите `"chat":{"id": ...}` — это и есть `TELEGRAM_CHAT_ID`.
   Либо используйте бота `@userinfobot`.

Проще — встроенная команда (после того как написали боту):

```bash
docker compose run --rm health-alert python monitor.py --chat-id
```

Она выведет все chat_id, которые видит бот.

Важно: без сообщения от вас бот не может написать первым — Telegram вернёт
`403 Forbidden`. Это не ошибка токена.

## Запуск

```bash
docker compose up -d --build health-alert
```

Проверка без отправки сообщений:

```bash
docker compose run --rm -e HEALTH_ALERT_DRY_RUN=true \
  -e HEALTH_ALERT_STARTUP_DELAY_SECONDS=0 \
  health-alert python monitor.py --once
```

Проверка реальной отправки в Telegram:

```bash
docker compose run --rm health-alert python monitor.py --test
```

Имитация сбоя (реальный алерт без остановки сервисов):

```bash
docker compose run --rm \
  -e HEALTH_ALERT_BACKEND_URL=http://backend:8000/does-not-exist \
  -e HEALTH_ALERT_NGINX_URL= \
  -e HEALTH_ALERT_CHECK_DB=false \
  -e HEALTH_ALERT_CHECK_REDIS=false \
  health-alert python monitor.py --once
```

Полноценная проверка с восстановлением: остановить backend, дождаться
алерта, запустить backend и дождаться сообщения о восстановлении.

```bash
docker compose stop backend
# подождать 2–3 минуты (интервал 60 сек + порог 2)
docker compose start backend
docker compose logs -f health-alert
```

## Как удалить

1. Удалить сервис `health-alert` из `docker-compose.yml`.
2. Удалить папку `ops/health-alert`.
3. Удалить переменные `TELEGRAM_*` и `HEALTH_ALERT_*` из `.env`.
4. Выполнить `docker compose up -d --remove-orphans`.
