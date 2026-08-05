# CityBoost — Production Deployment Guide

> Полное руководство по развёртыванию CityBoost в production-окружении.
> Версия: 1.0.0

---

## 📋 Содержание

1. [Требования к серверу](#1-требования-к-серверу)
2. [Подготовка окружения](#2-подготовка-окружения)
3. [Настройка .env для production](#3-настройка-env-для-production)
4. [Сборка фронтенда](#4-сборка-фронтенда)
5. [SSL-сертификаты (Let's Encrypt)](#5-ssl-сертификаты-lets-encrypt)
6. [Запуск через Docker Compose](#6-запуск-через-docker-compose)
7. [Первый запуск и проверка](#7-первый-запуск-и-проверка)
8. [Настройка домена и DNS](#8-настройка-домена-и-dns)
9. [Резервное копирование](#9-резервное-копирование)
10. [Мониторинг и обслуживание](#10-мониторинг-и-обслуживание)
11. [Обновление (деплой новой версии)](#11-обновление-деплой-новой-версии)
12. [Устранение неполадок](#12-устранение-неполадок)
13. [Security checklist](#13-security-checklist)
14. [Справочник команд](#14-справочник-команд)

---

## 1. Требования к серверу

### Минимальные
| Ресурс | Требование |
|---|---|
| CPU | 2 ядра (x86_64) |
| RAM | 2 GB |
| Диск | 20 GB SSD |
| ОС | Ubuntu 22.04 / Debian 12 |
| Docker | 24+ |
| Docker Compose | 2.21+ |
| Git | любая актуальная |

### Рекомендуемые
| Ресурс | Значение |
|---|---|
| CPU | 4 ядра |
| RAM | 4 GB |
| Диск | 50 GB SSD (NVMe желательно) |

### Сеть
- Открытые порты: `80` (HTTP), `443` (HTTPS), `5433` (опционально, для внешнего доступа к БД)
- DNS A-запись: ваш-домен.ru → IP сервера

### Установка Docker

```bash
# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Выйти и зайти заново (или newgrp docker)

# Docker Compose (обычно уже в составе Docker)
docker compose version
```

---

## 2. Подготовка окружения

### 2.1 Клонирование репозитория

```bash
mkdir -p /opt/cityboost
cd /opt/cityboost
git clone <ваш-репозиторий> .
```

### 2.2 Директории для данных

```bash
mkdir -p storage/uploads/tickets
mkdir -p nginx/ssl
mkdir -p certbot/www certbot/conf
mkdir -p backups/postgres backups/storage
```

### 2.3 Проверка структуры

```bash
/opt/cityboost/
├── backend/
├── frontend/
├── nginx/
│   ├── default.conf         # HTTP (dev/redirect)
│   └── ssl.conf             # HTTPS (шаблон)
├── storage/
│   └── uploads/
│       └── tickets/
├── certbot/
│   ├── www/
│   └── conf/
├── backups/
│   ├── postgres/
│   └── storage/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env
└── prod.md
```

---

## 3. Настройка .env для production

Скопируйте и отредактируйте `.env`. **Обязательно смените секреты!**

```bash
cp .env .env.prod
nano .env.prod
```

Минимальный production-конфиг:

```ini
# ===== PostgreSQL =====
POSTGRES_USER=cityboost
POSTGRES_PASSWORD=<сгенерировать: openssl rand -base64 32>
POSTGRES_DB=cityboost
DATABASE_URL=postgresql+asyncpg://cityboost:<пароль>@db:5432/cityboost

# ===== Redis =====
REDIS_URL=redis://redis:6379/0

# ===== JWT =====
JWT_SECRET_KEY=<сгенерировать: openssl rand -base64 64>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ===== App =====
APP_NAME=CityBoost
DEBUG=false                            # !!! Обязательно false
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=https://ваш-домен.ru     # !!! Никаких *

# ===== Storage =====
UPLOAD_DIR=storage/uploads/tickets
MAX_FILE_SIZE_MB=10                    # Увеличено для прода
MAX_FILES_PER_TICKET=5

# ===== SMTP (Email) =====
SMTP_HOST=smtp.yandex.ru              # или ваш SMTP-сервер
SMTP_PORT=587
SMTP_USER=noreply@cityboost.ru
SMTP_PASSWORD=<пароль приложения>
SMTP_FROM=noreply@cityboost.ru
SMTP_USE_TLS=true

# ===== Sentry (опционально) =====
SENTRY_DSN=https://<key>@o<org>.ingest.sentry.io/<project>

# ===== Geocoding =====
GEOCODING_API_URL=https://nominatim.openstreetmap.org
GEOCODING_TIMEOUT_SECONDS=2
```

**Генерация секретов:**

```bash
# JWT Secret Key (64 байта base64)
openssl rand -base64 64

# Пароль БД
openssl rand -base64 32

# Проверка сложности пароля
echo "<пароль>" | python3 -c "import sys; p=sys.stdin.read().strip(); print('OK' if len(p)>=16 and any(c.isupper() for c in p) and any(c.islower() for c in p) and any(c.isdigit() for c in p) else 'WEAK')"
```

После редактирования:

```bash
mv .env .env.backup
mv .env.prod .env
```

---

## 4. Сборка фронтенда

### 4.1 Установка зависимостей

```bash
cd /opt/cityboost/frontend

# Требуется Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt install -y nodejs

npm ci --omit=dev
```

### 4.2 Сборка

```bash
npm run build
```

Проверьте результат:

```bash
ls -la dist/
# index.html, assets/ (с хешами в именах)
```

Если сборка завершилась ошибкой:

```bash
# Очистить кеш и пересобрать
rm -rf node_modules dist
npm ci
npm run build
```

> **Важно:** Сборка фронтенда делается на сервере перед запуском контейнеров, либо в CI перед деплоем. После сборки `dist/` монтируется в nginx-контейнер через `docker-compose.yml` (строка `./frontend/dist:/usr/share/nginx/html:ro`).

---

## 5. SSL-сертификаты (Let's Encrypt)

### 5.1 Временный запуск nginx для подтверждения домена

Сначала запустите nginx в режиме HTTP (без SSL):

```bash
# Убедитесь, что default.conf не содержит ssl-директив
# и listen 80 активен
docker compose up -d nginx
```

### 5.2 Получение сертификата

```bash
DOMAIN="ваш-домен.ru"
EMAIL="admin@ваш-домен.ru"

docker compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email $EMAIL \
  --domain $DOMAIN \
  --agree-tos \
  --non-interactive
```

### 5.3 Настройка ssl.conf

Отредактируйте `nginx/ssl.conf`, заменив `ваш-домен.ru` на реальный домен:

```nginx
server {
    listen 443 ssl http2;
    server_name ваш-домен.ru;

    ssl_certificate /etc/letsencrypt/live/ваш-домен.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ваш-домен.ru/privkey.pem;
    # ... остальная конфигурация
```

**Важно:** Все пути к сертификатам в `ssl.conf` указаны относительно certbot-контейнера:
- `/etc/letsencrypt/live/...` — реальный путь внутри контейнера certbot
- В nginx эти же пути видны благодаря `volumes: ./certbot/conf:/etc/letsencrypt`

### 5.4 Редирект HTTP → HTTPS (опционально)

Добавьте в `nginx/default.conf` перед server-блоком:

```nginx
server {
    listen 80;
    server_name ваш-домен.ru;
    return 301 https://$server_name$request_uri;
}
```

### 5.5 Включение HTTPS

Отредактируйте `docker-compose.yml` — добавьте монтирование ssl.conf в nginx:

```yaml
nginx:
  ...
  volumes:
    - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    - ./nginx/ssl.conf:/etc/nginx/conf.d/ssl.conf:ro  # раскомментировать
    - ./certbot/conf:/etc/letsencrypt:ro               # добавить
    - ./certbot/www:/var/www/certbot:ro                # добавить
    - ./frontend/dist:/usr/share/nginx/html:ro
    - ./storage:/app/storage:ro
```

### 5.6 Автообновление сертификатов

 certbot в `docker-compose.yml` уже настроен на проверку каждые 12 часов (`sleep 12h`). Для принудительного обновления:

```bash
docker compose run --rm certbot renew
```

Для автоматического обновления с перезагрузкой nginx добавьте в crontab:

```bash
sudo crontab -e
# Строка:
0 3 * * * cd /opt/cityboost && docker compose run --rm certbot renew && docker compose exec nginx nginx -s reload
```

---

## 6. Запуск через Docker Compose

### 6.1 Production-запуск

```bash
cd /opt/cityboost

# Сборка образов
docker compose build

# Запуск всех сервисов с production-конфигом
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Проверка
docker compose ps
```

### 6.2 Проверка логов

```bash
# Все сервисы
docker compose logs -f --tail=100

# Конкретный сервис
docker compose logs -f --tail=100 backend
docker compose logs -f --tail=100 nginx

# Ошибки
docker compose logs backend | grep ERROR
docker compose logs backend | grep -i error
```

### 6.3 Перезапуск отдельных сервисов

```bash
# Рестарт конкретного сервиса
docker compose restart backend

# Рестарт с пересборкой
docker compose up -d --build backend
```

---

## 7. Первый запуск и проверка

### 7.1 Проверка миграций БД

При запуске entrypoint автоматически применяет миграции (`alembic upgrade head`). Проверьте:

```bash
docker compose logs backend | grep "Migrations applied"
# Ожидаемый вывод:
# >>> Applying database migrations...
# >>> Migrations applied successfully.
# >>> Starting: uvicorn src.main:app ...
```

### 7.2 Healthcheck

```bash
# Через nginx
curl http://localhost/health
# → {"status":"ok","app":"CityBoost"}

# Через HTTPS
curl https://ваш-домен.ru/health
# → {"status":"ok","app":"CityBoost"}

# Напрямую к API (без nginx)
curl http://localhost:8000/health
```

### 7.3 Проверка API

```bash
# Регистрация
curl -X POST https://ваш-домен.ru/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Тест","email":"test@test.ru","password":"TestPass1"}'

# Вход
TOKEN=$(curl -s -X POST https://ваш-домен.ru/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.ru","password":"TestPass1"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Профиль
curl -H "Authorization: Bearer $TOKEN" https://ваш-домен.ru/api/v1/auth/me
```

### 7.4 Проверка карты (Leaflet/OSM)

Откройте сайт в браузере, создайте заявку — проверьте:
- Отображается ли карта на странице создания заявки
- Работает ли поиск адреса
- Отображается ли карта на странице заявки
- Загружаются ли тайлы OpenStreetMap

> Если карта не отображается — проверьте, что `Content-Security-Policy` в `security.py` разрешает `img-src` для tile.openstreetmap.org.

---

## 8. Настройка домена и DNS

### 8.1 DNS-записи

| Тип | Имя | Значение |
|---|---|---|
| A | @ | <IP сервера> |
| AAAA | @ | <IPv6 сервера> (опционально) |
| CNAME | www | @ |

### 8.2 Nginx Server Name

В `nginx/ssl.conf` замените `server_name _;` на:

```nginx
server_name ваш-домен.ru www.ваш-домен.ru;
```

### 8.3 CORS

В `.env` обязательно укажите конкретный домен:

```ini
CORS_ORIGINS=https://ваш-домен.ru,https://www.ваш-домен.ru
```

---

## 9. Резервное копирование

### 9.1 База данных (PostgreSQL)

```bash
#!/bin/bash
# /opt/cityboost/backup-db.sh

BACKUP_DIR="/opt/cityboost/backups/postgres"
DATE=$(date +%Y-%m-%d_%H-%M)
DB_USER="cityboost"
DB_NAME="cityboost"

# Создание дампа из контейнера
docker compose exec -T db pg_dump -U $DB_USER $DB_NAME \
  --no-owner \
  --no-acl \
  --format=custom \
  > "$BACKUP_DIR/cityboost_$DATE.dump"

# Сжатие
gzip "$BACKUP_DIR/cityboost_$DATE.dump"

# Удаление бэкапов старше 30 дней
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

echo "Backup created: cityboost_$DATE.dump.gz"
```

```bash
chmod +x backup-db.sh
# Ежедневно в 3:00
crontab -e
0 3 * * * /opt/cityboost/backup-db.sh >> /var/log/cityboost-backup.log 2>&1
```

### 9.2 Загруженные файлы

```bash
#!/bin/bash
# /opt/cityboost/backup-storage.sh

BACKUP_DIR="/opt/cityboost/backups/storage"
DATE=$(date +%Y-%m-%d)

tar czf "$BACKUP_DIR/uploads_$DATE.tar.gz" -C /opt/cityboost storage/uploads
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

### 9.3 Восстановление из бэкапа

```bash
# Восстановление БД (осторожно — перезаписывает данные!)
docker compose exec -T db pg_restore \
  -U $DB_USER -d $DB_NAME \
  --no-owner --clean \
  < backup.dump

# Восстановление файлов
tar xzf uploads_YYYY-MM-DD.tar.gz -C /opt/cityboost
```

---

## 10. Мониторинг и обслуживание

### 10.1 Базовый мониторинг

```bash
# Состояние контейнеров
docker compose ps

# Использование ресурсов
docker stats --no-stream

# Логи ошибок
docker compose logs --tail=50 --since=5m backend | grep -i "error\|exception\|traceback"

# Размер БД
docker compose exec db psql -U cityboost -d cityboost -c "
  SELECT pg_database_size('cityboost')/1024/1024 AS size_mb;
"

# Количество заявок
docker compose exec db psql -U cityboost -d cityboost -c "
  SELECT status, COUNT(*) FROM tickets GROUP BY status ORDER BY status;
"
```

### 10.2 Логи nginx

```bash
# Access log
docker compose exec nginx tail -f /var/log/nginx/access.log

# Error log
docker compose exec nginx tail -f /var/log/nginx/error.log

# IP-адреса с наибольшим количеством запросов
docker compose exec nginx sh -c "awk '{print \$1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20"
```

### 10.3 Redis

```bash
# Проверка
docker compose exec redis redis-cli ping
# → PONG

# Использование памяти
docker compose exec redis redis-cli info memory | grep used_memory_human

# Текущие rate limit ключи
docker compose exec redis redis-cli keys 'ratelimit:*'
docker compose exec redis redis-cli keys 'bruteforce:*'

# Сброс rate limit (если кого-то случайно заблокировали)
docker compose exec redis redis-cli del "bruteforce:ban:<IP>"
```

### 10.4 Sentry (если настроен)

- Дашборд: https://sentry.io
- Отслеживание ошибок в реальном времени
- Performance tracing (sample rate: 0.1)

### 10.5 Системный мониторинг

```bash
# Диск
df -h /opt/cityboost

# CPU/RAM
htop

# Swap
free -h
```

---

## 11. Обновление (деплой новой версии)

### 11.1 Процедура обновления

```bash
cd /opt/cityboost

# 1. Скачать новую версию
git pull origin main

# 2. Обновить зависимости (если requirements.txt изменился)
docker compose build --no-cache backend

# 3. Пересобрать фронтенд (если изменился)
cd frontend
npm ci
npm run build
cd ..

# 4. Бэкап перед обновлением
./backup-db.sh
./backup-storage.sh

# 5. Перезапустить
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 6. Проверить миграции
docker compose logs backend | grep "Migrations applied"

# 7. Healthcheck
curl -f https://ваш-домен.ru/health

# 8. Проверить логи
docker compose logs --tail=30 backend
```

### 11.2 Откат

```bash
# Откат до предыдущего коммита
git revert HEAD
git push origin main

# Пересобрать и перезапустить
docker compose build --no-cache backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Восстановить БД (если миграции навредили)
# Сначала убейте контейнеры, восстановите БД, запустите заново
docker compose down
docker compose exec -T db pg_restore -U cityboost -d cityboost \
  --no-owner --clean < backups/postgres/cityboost_*.dump
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 12. Устранение неполадок

### 12.1 Контейнер не стартует

```bash
# Проверить логи
docker compose logs <service>

# Типичные ошибки:
# — "port is already allocated" — порт занят, поменяйте в docker-compose.yml
# — "Cannot connect to the Docker daemon" — Docker не запущен: sudo systemctl start docker
# — "permission denied" — проверьте права на монтируемые директории
```

### 12.2 База данных

```bash
# Не применяются миграции
docker compose logs backend | grep alembic
# Вручную:
docker compose run --rm backend alembic upgrade head

# Потеряно соединение с БД
docker compose exec db psql -U cityboost -d cityboost -c "SELECT 1;"

# Сброс пароля БД
docker compose exec db psql -U cityboost -d cityboost -c "ALTER USER cityboost WITH PASSWORD 'новый-пароль';"
# Не забудьте обновить .env и перезапустить backend
```

### 12.3 Фронтенд

```bash
# Страница пустая (белый экран)
# 1. Проверьте, что dist/ не пуст
ls -la frontend/dist/
# 2. Проверьте, что nginx видит файлы
docker compose exec nginx ls -la /usr/share/nginx/html/
# 3. Проверьте консоль браузера (F12) на 404/403
# 4. Проверьте, что API-запросы уходят на правильный URL

# 404 на всех маршрутах
# Убедитесь, что в nginx есть try_files $uri $uri/ /index.html;

# CSS/JS не грузятся (404)
# Проверьте, что assets/ успешно собран и смонтирован
```

### 12.4 Rate limit

```bash
# Кто-то жалуется, что не может зайти
# 1. Проверить, заблокирован ли IP
docker compose exec redis redis-cli keys 'bruteforce:ban:*'
# 2. Снять блокировку
docker compose exec redis redis-cli del "bruteforce:ban:<IP>"
# 3. Проверить активные rate limit ключи
docker compose exec redis redis-cli keys 'ratelimit:*'
```

### 12.5 Ошибки 502/504

```bash
# 502 Bad Gateway — backend недоступен
docker compose ps backend          # должен быть Up
docker compose logs --tail=20 backend

# 504 Gateway Timeout — долгий ответ
# Увеличьте proxy_read_timeout в nginx/default.conf (сейчас 60s)
```

### 12.6 Проблемы с картой (Leaflet)

```bash
# Тайлы не загружаются
# 1. Проверьте Content-Security-Policy
#    В .env при DEBUG=false включается SecurityHeadersMiddleware
#    Убедитесь, что img-src разрешает *.tile.openstreetmap.org
# 2. Проверьте консоль браузера на блокировку CSP
# 3. Альтернатива — переключиться на другой tile-провайдер
```

### 12.7 SSL-проблемы

```bash
# Сертификат истёк
docker compose run --rm certbot renew
docker compose exec nginx nginx -s reload

# Проверка даты сертификата
docker compose exec nginx openssl x509 -in /etc/letsencrypt/live/ваш-домен.ru/fullchain.pem -noout -dates

# Ошибка "certificate has expired"
# Проверьте, что порт 80 открыт (certbot использует его для валидации)
# Если certbot не может обновиться — порт 80 закрыт фаерволом
```

---

## 13. Security Checklist

Перед запуском в production проверьте каждый пункт:

- [ ] **`.env`:** `DEBUG=false`, `CORS_ORIGINS` — конкретный домен, не `*`
- [ ] **JWT Secret Key:** сгенерирован случайно (`openssl rand -base64 64`), длина > 64 байт
- [ ] **Пароль БД:** сгенерирован случайно, не совпадает с дефолтным
- [ ] **Пароль SMTP:** пароль приложения, не основной
- [ ] **nginx rate limiting:** раскомментировать `limit_req_zone` в ssl.conf
- [ ] **HSTS:** включён в ssl.conf (`max-age=31536000; includeSubDomains`)
- [ ] **CSP:** настроен в `backend/src/common/security.py`
- [ ] **frontend dist:** не содержит `.env`, `.git`, исходников
- [ ] **Docker Compose:** production overrides применены (`-f docker-compose.prod.yml`)
- [ ] **Лимиты ресурсов:** CPU/RAM установлены для каждого сервиса
- [ ] **Логирование:** настроено `max-size: 10m`, `max-file: 3`
- [ ] **Перенаправление HTTP→HTTPS:** настроено через nginx
- [ ] **Sentry:** DSN указан (опционально, но рекомендуется)
- [ ] **Бэкапы:** настроены (БД ежедневно, файлы еженедельно)
- [ ] **Фаервол:** открыты только порты 80, 443 (и 5433 если нужен внешний доступ к БД)
- [ ] **Автообновление certbot:** настроено в crontab
- [ ] **Rate limit админских эндпоинтов:** Redis rate limiting активен (проверить через curl-тест)

---

## 14. Справочник команд

### Docker Compose

```bash
# Полный production-запуск
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Пересборка и запуск
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Остановка
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Остановка с удалением томов (все данные будут потеряны!)
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v

# Рестарт одного сервиса
docker compose restart backend

# Логи
docker compose logs -f --tail=100 backend

# Вход в контейнер
docker compose exec backend /bin/sh
docker compose exec db psql -U cityboost -d cityboost

# Просмотр ресурсов
docker compose top

# Список образов
docker compose images
```

### Администрирование БД

```bash
# Подключиться к БД
docker compose exec db psql -U cityboost -d cityboost

# Полезные запросы
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM tickets;
SELECT id, title, status, created_at FROM tickets ORDER BY created_at DESC LIMIT 10;
SELECT u.name, t.title FROM tickets t JOIN users u ON t.user_id = u.id WHERE t.status = 'NEW';
SELECT * FROM admin_action_log ORDER BY created_at DESC LIMIT 20;

# Размер таблиц
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

# Активные соединения
SELECT pid, state, query_start, query FROM pg_stat_activity WHERE state = 'active';
```

### Администрирование Redis

```bash
# Подключиться
docker compose exec redis redis-cli

# Мониторинг команд
redis-cli monitor

# Инфо
redis-cli info

# Очистить всё (осторожно!)
redis-cli flushall
```

### Проверка состояния

```bash
# Полная диагностика
echo "=== Docker ===" && docker compose ps && \
echo "=== Health ===" && curl -f http://localhost/health && \
echo && echo "=== Backend logs (last 5 lines) ===" && docker compose logs --tail=5 backend && \
echo "=== Nginx logs (last 5 lines) ===" && docker compose logs --tail=5 nginx && \
echo "=== Disk ===" && df -h /opt/cityboost && \
echo "=== DB size ===" && docker compose exec db psql -U cityboost -d cityboost -t -c "SELECT pg_size_pretty(pg_database_size('cityboost'));"
```

---

> **Последнее обновление:** 2026-06-29
>
> **Автор:** CityBoost Team
