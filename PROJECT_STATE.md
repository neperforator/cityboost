# CityBoost — полное состояние проекта

> Сгенерировано: 2026-06-28

## Что это
Городской портал заявок (аналог «Добродел»). Модульный монолит на FastAPI + Vue 3.

---

## Архитектура

### Бэкенд (`backend/`)
- **FastAPI** (async) + **SQLAlchemy 2.0** (async, `asyncpg`)
- **PostgreSQL** — UUID primary keys
- **Redis** — rate limiting, brute-force защита
- **JWT** (`python-jose`, HS256) — аутентификация
- **Alembic** — миграции
- **arq** — background worker (фоновые задачи)
- **Pillow** — обработка изображений

### Фронтенд (`frontend/`)
- **Vue 3** (Composition API, `<script setup>`)
- **Pinia** — state management
- **Vue Router 4** — hash-based routing (`createWebHashHistory`)
- **Vite** — сборка
- **Tailwind CSS v3** — стили, кастомные `@layer components`
- **Axios** — HTTP-клиент с JWT-интерцепторами
- **Leaflet 1.9.4** — карты (`attributionControl: false`)

### Инфраструктура (`docker-compose.yml`)
5 сервисов:
1. **backend** — FastAPI приложение (порт 8000)
2. **worker** — arq воркер (фоновые задачи)
3. **db** — PostgreSQL 15
4. **redis** — Redis 7
5. **nginx** — reverse proxy (порт 80) + статика

---

## Текущий статус

### ✅ Реализовано
- Регистрация / логин / профиль (базовый)
- JWT-аутентификация
- CRUD заявок (с гео-координатами, категориями, статусами)
- Загрузка файлов к заявкам (JPEG/PNG, magic byte validation)
- Комментарии к заявкам
- История изменений заявок
- Админка: список пользователей, смена роли, управление заявками
- **Блокировка аккаунтов** (ban/unban)
- **Rate limiting** (Redis middleware):
  - 3 регистрации/час
  - 10 логинов/мин
  - 30 запросов к заявкам/мин
  - Брутфорс-защита: 5 неудачных попыток → бан 15 мин по IP
- **Security headers middleware**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 0`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()`
- **CORS** — ограничен localhost (не `*`)
- **Валидация файлов** — magic bytes, не доверяем Content-Type
- **Пароли** — 8+ символов, заглавная/строчная/цифра, чёрный список простых
- **Запрет самоблокировки** админа
- **Карты OSM** — без Leaflet attribution
- **Tailwind-компоненты** — `.card`, `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.badge-admin`, `.form-input` и т.д.

### 🚧 В процессе — Фаза 1

Начата Фаза 1 (см. план ниже). Прервано на первом пункте.

---

## План мега-апгрейда (утверждён)

### Фаза 1: База — email, профиль, аудит, nginx rate limit
1. **Email-инфраструктура и сброс пароля**
   - SMTP настройки в `config.py`
   - Модуль `backend/src/notifications/` (smtplib)
   - `POST /auth/forgot-password`, `POST /auth/reset-password`
   - `reset_token` на модели User
   - Миграция `0003_add_reset_token.py`
   - `ForgotPasswordView.vue`, `ResetPasswordView.vue`
   - Роуты во фронтенде

2. **Свой профиль (аватар, телефон, смена пароля)**
   - `phone`, `avatar_path` поля на User
   - `UserUpdateRequest`, расширенный `UserOut`
   - `PATCH /auth/me`, `POST /auth/me/avatar`
   - Миграция `0004_add_profile_fields.py`
   - Переписать `ProfileView.vue`

3. **Аудит-лог админов**
   - Модель `AdminActionLog`
   - Хэлпер `log_admin_action()`
   - Логировать ban/unban/changeRole
   - Миграция `0005_add_admin_audit_log.py`
   - `AdminAuditLogView.vue`, роут `/admin/audit`

4. **Rate limiting на nginx**
   - `limit_req_zone` + `limit_req` на `/api/` в `nginx/default.conf`

### Фаза 2: Инфраструктура
5. Production Docker (`docker-compose.yml`, `docker-compose.override.yml`)
6. HTTPS Let's Encrypt
7. Sentry (backend + frontend)
8. Prometheus + Grafana

### Фаза 3: Инструменты разработки
9. TypeScript (весь фронтенд)
10. Линтеры (ESLint + Prettier + ruff)
11. Storybook
12. Тесты (pytest + vitest)
13. CI/CD (GitHub Actions)

### Фаза 4: UX-полировка
14. Loading skeletons
15. 404/500 страницы
16. Dark theme auto-detect (`prefers-color-scheme`)
17. Пагинация (номера страниц, бесконечный скролл)

---

## Ключевые файлы

### Бэкенд
| Файл | Назначение |
|------|-----------|
| `backend/src/main.py` | Точка входа, middleware, роуты |
| `backend/src/config.py` | Pydantic Settings (из .env) |
| `backend/src/database.py` | SQLAlchemy async engine + Base |
| `backend/src/auth/models.py` | User, UserRole |
| `backend/src/auth/schemas.py` | Pydantic-схемы (RegisterRequest, LoginRequest, UserOut, TokenResponse) |
| `backend/src/auth/repository.py` | UserRepository (CRUD) |
| `backend/src/auth/service.py` | AuthService (регистрация, логин, JWT, валидация пароля) |
| `backend/src/auth/router.py` | POST /register, /login, GET /me |
| `backend/src/auth/admin.py` | AdminUserRouter (list, role, ban, unban) |
| `backend/src/auth/dependencies.py` | get_current_user, require_role |
| `backend/src/common/security.py` | SecurityHeadersMiddleware |
| `backend/src/common/ratelimit.py` | RateLimitMiddleware + brute force |
| `backend/src/common/exceptions.py` | Exception handlers |
| `backend/src/common/middlewares.py` | RequestLoggingMiddleware |
| `backend/src/tickets/` | Модуль заявок (model, router, admin, schemas) |

### Фронтенд
| Файл | Назначение |
|------|-----------|
| `frontend/src/api/index.js` | Axios + все API-вызовы |
| `frontend/src/stores/auth.js` | Pinia store авторизации |
| `frontend/src/router/index.js` | Все роуты + guards |
| `frontend/src/views/LoginView.vue` | Страница входа |
| `frontend/src/views/RegisterView.vue` | Регистрация |
| `frontend/src/views/DashboardView.vue` | Список заявок (карточки) |
| `frontend/src/views/CreateTicketView.vue` | Создание заявки |
| `frontend/src/views/TicketDetailView.vue` | Просмотр заявки |
| `frontend/src/views/ProfileView.vue` | Профиль |
| `frontend/src/views/AdminDashboardView.vue` | Админка: все заявки |
| `frontend/src/views/AdminTicketDetailView.vue` | Админка: детали заявки |
| `frontend/src/views/AdminUsersView.vue` | Админка: пользователи |
| `frontend/src/components/MapPicker.vue` | Выбор местоположения на карте |
| `frontend/src/components/StatusBadge.vue` | Бейдж статуса |
| `frontend/src/components/AppHeader.vue` | Шапка с навигацией |

### Инфраструктура
| Файл | Назначение |
|------|-----------|
| `docker-compose.yml` | 5 сервисов |
| `nginx/default.conf` | Reverse proxy, статика |
| `backend/.env` | Все переменные окружения |
| `backend/Dockerfile` | Сборка бэкенда |
| `frontend/Dockerfile` | Сборка фронтенда |

---

## Данные для входа
- **Админ:** admin@cityboost.ru / admin123456
- База создана заново после удаления (миграции 0001 + 0002)

## Команды
```bash
docker compose up --build -d       # Полный запуск
docker compose restart nginx        # Рестарт nginx (если 502)
docker compose logs backend -f      # Логи бэкенда
docker compose exec backend alembic upgrade head  # Миграции
docker compose exec worker alembic upgrade head   # Миграции для worker
```

---

## Известные особенности
- `from __future__ import annotations` + Pydantic v2 `@field_validator` — конфликтуют. Валидация паролей вынесена в сервис
- slowapi несовместим с `from __future__ import annotations`. Используется кастомный Redis middleware
- CartoDB Positron tiles были отменены пользователем, используются OSM без Leaflet attribution
- nginx может кешировать DNS → 502 после пересборки контейнера. Лечится `docker compose restart nginx`
- Worker собирается отдельно, может не подхватывать новые миграции → `docker compose build --no-cache worker`
