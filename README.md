# CityBoost

Городская служба заявок: жители создают заявки с фото и адресом на карте,
администраторы обрабатывают их, ведут аудит и смотрят аналитику.

## Стек

- **Backend** — FastAPI, SQLAlchemy 2 (async), Alembic, PostgreSQL, Redis.
- **Frontend** — Vue 3, TypeScript, Vite, Tailwind CSS, MapLibre.
- **Инфраструктура** — Docker Compose, nginx (раздача SPA + reverse proxy).

## Быстрый старт (Docker)

```bash
cp .env.example .env
# отредактируйте .env: секреты, пароль БД, SMTP и т.д.
docker compose up -d --build
```

После запуска:

- приложение — http://localhost
- backend напрямую — http://127.0.0.1:8000 (только localhost)
- healthcheck — http://localhost/health

Миграции применяются автоматически при старте backend
(`backend/docker-entrypoint.sh`). Отключить: `SKIP_MIGRATIONS=true`.

Полезные команды:

```bash
docker compose ps
docker compose logs -f backend
docker compose up -d --build backend   # пересобрать один сервис
docker compose down                    # остановить (данные сохраняются)
docker compose down -v                 # остановить и удалить БД/Redis
```

## Локальная разработка

Поднимите только инфраструктуру:

```bash
docker compose up -d db redis
```

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

При запуске вне Docker база и Redis доступны на опубликованных портах
(`127.0.0.1:5433` и `127.0.0.1:6379`), поэтому в `backend/.env` или в
переменных окружения укажите:

```env
DATABASE_URL=postgresql+asyncpg://cityboost:cityboost_secret@localhost:5433/cityboost
REDIS_URL=redis://localhost:6379/0
DEBUG=true
```

Затем:

```bash
alembic upgrade head
uvicorn src.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm ci
npm run dev                     # http://localhost:5173, проксирует /api на :8000
```

### Проверки

```bash
# Backend
cd backend
python -m ruff check .
DEBUG=true JWT_SECRET_KEY=test-secret-key-that-is-long-enough-123456 python -m pytest -q

# Frontend
cd frontend
npm run typecheck
npm run build
```

На Windows переменные задаются так:

```powershell
$env:DEBUG='true'
$env:JWT_SECRET_KEY='test-secret-key-that-is-long-enough-123456'
python -m pytest -q
```

## Переменные окружения

Шаблон — `.env.example`. Рабочий файл — `.env` (в git не попадает).

Ключевое:

| Переменная | Назначение |
| --- | --- |
| `DATABASE_URL` | подключение к PostgreSQL (asyncpg) |
| `REDIS_URL` | Redis для rate limit |
| `JWT_SECRET_KEY` | секрет подписи токенов, **минимум 32 символа** |
| `DEBUG` | `true` только локально; в production `false` |
| `DEBUG_BYPASS_EMAIL_AUTH` | `true` — регистрация и вход без писем (только при `DEBUG=true`) |
| `ENABLE_DOCS` | Swagger/ReDoc; в production `false` |
| `CORS_ORIGINS` | явные Origin'ы через запятую, без `*` |
| `REFRESH_COOKIE_SECURE` | `true` при работе по HTTPS |
| `SMTP_*` | отправка писем (подтверждение, 2FA) |
| `ADMIN_2FA_ENABLED` | обязательный код на email для админов |
| `UPLOAD_DIR` | директория загруженных изображений |

## Production-чеклист

1. **Секреты.** Сгенерируйте `JWT_SECRET_KEY` (32+ случайных символа) и
   сильный `POSTGRES_PASSWORD`. Не используйте значения из `.env.example`.
2. **Режим.** `DEBUG=false`, `ENABLE_DOCS=false`, `CORS_ORIGINS=https://ваш-домен`.
3. **HTTPS.** `REFRESH_COOKIE_SECURE=true`. `nginx/default.conf` слушает
   `:80`; готовый HTTPS-конфиг — `nginx/https.conf.example` (certbot,
   автопродление настраиваются на сервере).
4. **Почта.** Настройте `SMTP_*`, иначе регистрация/2FA не смогут отправлять коды.
5. **Миграции.** Проверьте `alembic upgrade head` перед выкладкой. Откат:
   `alembic downgrade -1`.
6. **Данные.** Тома `pgdata`, `redisdata` и каталог `storage/uploads/` —
   единственные источники состояния. При пересоздании контейнеров они
   сохраняются; удаляет их только `docker compose down -v`.
7. **Запуск.**
   ```bash
   docker compose up -d --build
   docker compose ps
   curl -f http://localhost/health
   ```

## Структура

```
backend/            FastAPI, миграции, тесты
frontend/           Vue 3 SPA
nginx/              конфигурация reverse proxy
storage/            загруженные пользователями файлы (gitignored)
docker-compose.yml  production-подобная сборка
```
