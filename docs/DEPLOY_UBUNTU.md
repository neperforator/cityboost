
## 1. Подготовка сервера

```bash
apt update && apt upgrade -y
```

Что делает:

- `apt update` — обновляет список доступных пакетов.
- `apt upgrade -y` — устанавливает обновления без вопросов.

```bash
apt install -y curl ca-certificates gnupg git
```

Что делает:

- `curl` — скачивает GPG-ключ Docker.
- `ca-certificates` — доверенные корневые сертификаты (нужны для HTTPS).
- `gnupg` — проверяет подпись репозитория Docker.
- `git` — клонирует код проекта.

Если UFW уже включён и порты 80/443 закрыты — откройте их
(правила SSH не меняем):

```bash
ufw allow 80/tcp
ufw allow 443/tcp
```

Что делает:

- `ufw allow 80/tcp` — разрешает HTTP (нужен для выпуска сертификата и редиректа).
- `ufw allow 443/tcp` — разрешает HTTPS.
- Правила для SSH не добавляются и не меняются.

Часовой пояс (необязательно, влияет только на системные логи):

```bash
timedatectl set-timezone Europe/Minsk
```

---

## 2. Docker

```bash
install -m 0755 -d /etc/apt/keyrings
```

Что делает: создаёт каталог для ключей репозиториев с правами `0755`.

```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

Что делает: скачивает официальный GPG-ключ Docker и сохраняет его в
бинарном формате, чтобы `apt` мог проверять подпись пакетов.

```bash
chmod a+r /etc/apt/keyrings/docker.gpg
```

Что делает: разрешает чтение ключа всем пользователям (нужно `apt`).

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Что делает: добавляет репозиторий Docker для вашей архитектуры и версии
Ubuntu (`22.04` → `jammy`, `24.04` → `noble`).

```bash
apt update
apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
```

Что делает:

- `apt update` — подхватывает новый репозиторий.
- `docker-ce` — сам Docker.
- `docker-ce-cli` — команда `docker`.
- `containerd.io` — движок контейнеров.
- `docker-buildx-plugin` — современная сборка образов.
- `docker-compose-plugin` — команда `docker compose`.

Проверка:

```bash
docker --version
docker compose version
```

---

## 3. Домен

В панели домена создайте A-запись:

| Тип | Имя | Значение |
| --- | --- | --- |
| A | `cityboost` (или `@`) | IP сервера |

Что делает A-запись: связывает домен с IP сервера, чтобы браузер и
Let's Encrypt попадали именно на эту машину.

Проверка (должен вернуться IP сервера):

```bash
getent hosts your-domain.tld
```

Что делает: спрашивает системный DNS-резолвер, какой IP соответствует
домену. Если IP не тот — подождите обновления DNS.

---

## 4. Код проекта

```bash
mkdir -p /opt/cityboost
```

Что делает: создаёт каталог для проекта. `-p` не ругается, если он уже есть.

```bash
git clone <URL_РЕПОЗИТОРИЯ> /opt/cityboost
```

Что делает: скачивает код в `/opt/cityboost`. Замените `<URL_РЕПОЗИТОРИЯ>`
на ссылку вашего репозитория.

```bash
cd /opt/cityboost
mkdir -p storage/uploads/tickets
```

Что делает: переходит в каталог проекта и создаёт папку для фото заявок.
При старте backend сам выставит правильного владельца.

---

## 5. Настройка `.env`

```bash
cp .env.example .env
```

Что делает: создаёт рабочий конфиг из шаблона. `.env` в git не попадает.

```bash
chmod 600 .env
```

Что делает: оставляет чтение и запись только root — в файле пароли и секреты.

```bash
openssl rand -hex 32      # JWT_SECRET_KEY
openssl rand -hex 24      # POSTGRES_PASSWORD
```

Что делает:

- первая команда генерирует 64-символьный случайный секрет для подписи токенов;
- вторая — 48-символьный пароль для PostgreSQL. Hex безопасен для URL,
  поэтому его можно без изменений вставить в `DATABASE_URL`.

```bash
nano .env
```

Что делает: открывает конфиг для редактирования. Сохранить — `Ctrl+O`,
`Enter`, выйти — `Ctrl+X`.

Приведите ключевые строки к такому виду (подставьте свои значения):

```env
POSTGRES_USER=cityboost
POSTGRES_PASSWORD=ВАШ_СЛУЧАЙНЫЙ_ПАРОЛЬ
POSTGRES_DB=cityboost
DATABASE_URL=postgresql+asyncpg://cityboost:ВАШ_СЛУЧАЙНЫЙ_ПАРОЛЬ@db:5432/cityboost

REDIS_URL=redis://redis:6379/0

JWT_SECRET_KEY=ВАШ_СЛУЧАЙНЫЙ_СЕКРЕТ_32_СИМВОЛА
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

APP_NAME=CityBoost
DEBUG=false
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=https://your-domain.tld
ENABLE_DOCS=false

REFRESH_COOKIE_NAME=refresh_token
REFRESH_COOKIE_PATH=/api/v1/auth
REFRESH_COOKIE_SECURE=true
TRUST_PROXY_HEADERS=true

UPLOAD_DIR=storage/uploads/tickets
MAX_FILE_SIZE_MB=5
MAX_FILES_PER_TICKET=5

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@your-domain.tld
SMTP_PASSWORD=ПАРОЛЬ_ПРИЛОЖЕНИЯ
SMTP_FROM=CityBoost <noreply@your-domain.tld>
SMTP_USE_TLS=true

FRONTEND_URL=https://your-domain.tld

HEALTH_ALERT_ENABLED=true
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Что означает главное:

- `DATABASE_URL` — адрес базы **внутри Docker-сети**: хост `db`, порт `5432`.
- `JWT_SECRET_KEY` — подпись токенов. Менять после запуска нельзя без
  разлогина всех пользователей.
- `DEBUG=false` — production-режим и проверки безопасности.
- `ENABLE_DOCS=false` — Swagger/ReDoc отключены.
- `CORS_ORIGINS` — точный адрес сайта, без слэша на конце.
- `REFRESH_COOKIE_SECURE=true` — cookie только по HTTPS.
- `SMTP_*` — письма с кодами подтверждения и 2FA. Порт **587**, порт 465
  не поддерживается.
- `TELEGRAM_*` — опционально, для health-алертов.

Проверка конфигурации:

```bash
docker compose config --quiet && echo OK
```

Что делает: проверяет синтаксис `docker-compose.yml` и подставляет
переменные из `.env`. При успехе печатает `OK`, ничего не запуская.

---

## 6. Запуск

```bash
cd /opt/cityboost
docker compose up -d --build
```

Что делает:

- `--build` — собирает образы backend и frontend из исходников;
- `-d` — запускает в фоне;
- создаёт Docker-сеть и тома `pgdata`, `redisdata`, `frontend-dist`;
- backend при старте применяет миграции БД;
- frontend собирает SPA и завершается — это нормально.

Первая сборка может занять несколько минут.

```bash
docker compose ps -a
```

Что делает: показывает все контейнеры, включая завершившиеся. Флаг `-a`
нужен, чтобы увидеть `frontend` со статусом `Exited (0)`.

Ожидаемо:

- `cityboost-backend` — `Up (healthy)`
- `cityboost-db` — `Up (healthy)`
- `cityboost-redis` — `Up`
- `cityboost-nginx` — `Up`
- `cityboost-frontend-builder` — `Exited (0)` — **так и должно быть**
- `cityboost-health-alert` — `Up` или `Exited (0)`, если Telegram не настроен

```bash
docker compose logs --tail=100 backend
```

Что делает: показывает последние 100 строк логов backend. Там видно
применение миграций и запуск uvicorn:

```
>>> Applying database migrations...
>>> Migrations applied successfully.
>>> Starting: uvicorn ...
```

```bash
curl -fsS http://127.0.0.1/health
# {"status":"ok","app":"CityBoost"}
```

Что делает: `curl` идёт на локальный nginx, тот проксирует `/health` в
backend. Флаги: `-f` — ошибка при HTTP 4xx/5xx, `-s` — без прогресса,
`-S` — показать ошибку, если она есть.

> Полноценно пользоваться сайтом можно после шага 7 (HTTPS): до этого
> браузер не сохранит refresh-cookie, потому что включён `Secure`.

---

## 7. HTTPS

### 7.1. Подготовить каталоги

```bash
cd /opt/cityboost
mkdir -p certbot/conf certbot/www
```

Что делает:

- `certbot/conf` — здесь будут сертификаты и приватные ключи;
- `certbot/www` — сюда Let's Encrypt кладёт файл проверки домена.

### 7.2. Включить монтирование каталогов

Откройте `docker-compose.yml`, найдите сервис `nginx` и раскомментируйте
две строки в `volumes:`:

```yaml
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
```

Что делает: пробрасывает каталоги с хоста внутрь контейнера nginx, чтобы
он видел сертификаты и отдавал файл проверки Let's Encrypt.

```bash
docker compose up -d --force-recreate nginx
```

Что делает: пересоздаёт контейнер nginx, чтобы применились новые volume'ы.
`--force-recreate` нужен потому, что изменение `volumes` не применяется
обычным рестартом.

### 7.3. Выпустить сертификат

```bash
cd /opt/cityboost
DOMAIN=your-domain.tld

docker run --rm \
  -v /opt/cityboost/certbot/conf:/etc/letsencrypt \
  -v /opt/cityboost/certbot/www:/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email admin@"$DOMAIN" \
  --agree-tos --no-eff-email
```

Что делает:

- запускает одноразовый контейнер Certbot (`--rm` удалит его после);
- монтирует каталоги сертификатов и проверки;
- `certonly` — только выпустить сертификат, ничего не настраивать;
- `--webroot` — доказать владение доменом через файл на вашем сайте;
- `-d` — домен, для которого выпускается сертификат;
- `--agree-tos` — принимает условия Let's Encrypt;
- `--no-eff-email` — не подписывает email на рассылку EFF.

Сертификат появится в `certbot/conf/live/$DOMAIN/`.

### 7.4. Включить HTTPS-конфиг

```bash
cd /opt/cityboost
DOMAIN=your-domain.tld

cp nginx/default.conf nginx/default.conf.http.bak
```

Что делает: сохраняет текущий HTTP-конфиг как резервную копию.

```bash
cp nginx/https.conf.example nginx/default.conf
sed -i "s/your-domain.tld/$DOMAIN/g" nginx/default.conf
```

Что делает: берёт готовый HTTPS-шаблон и заменяет в нём
`your-domain.tld` на ваш домен (в `server_name` и путях к сертификату).

```bash
docker compose exec nginx nginx -t
```

Что делает: проверяет синтаксис конфига внутри уже запущенного nginx.
Должно быть `syntax is ok` и `test is successful`.

```bash
docker compose up -d --force-recreate nginx
```

Что делает: применяет HTTPS-конфиг и перезапускает nginx.

Проверка:

```bash
curl -I https://your-domain.tld/
# HTTP/2 200
```

```bash
curl -I http://your-domain.tld/
# 301 → https://your-domain.tld/
```

Что делает `curl -I`: запрашивает только заголовки ответа. Для HTTPS
ожидаем `200`, для HTTP — `301` с редиректом.

### 7.5. Автопродление сертификата

```bash
tee /etc/cron.d/cityboost-certbot > /dev/null <<'EOF'
0 4 * * * root cd /opt/cityboost && docker run --rm -v /opt/cityboost/certbot/conf:/etc/letsencrypt -v /opt/cityboost/certbot/www:/var/www/certbot certbot/certbot renew --quiet && docker compose exec -T nginx nginx -s reload
EOF
```

Что делает: создаёт задание cron, которое каждый день в 04:00 проверяет
срок сертификата, продлевает его при необходимости и перезагружает nginx.
`renew --quiet` ничего не пишет, если продление не требуется.

Проверка без реального продления:

```bash
docker run --rm \
  -v /opt/cityboost/certbot/conf:/etc/letsencrypt \
  -v /opt/cityboost/certbot/www:/var/www/certbot \
  certbot/certbot renew --dry-run
```

Что делает: имитирует продление и показывает, что оно пройдёт успешно.

---

## 8. Первый администратор

1. Откройте `https://your-domain.tld`.
2. Зарегистрируйтесь с email администратора и подтвердите его кодом из письма.
3. Повысьте роль:

```bash
cd /opt/cityboost
docker compose exec -T db psql -U cityboost -d cityboost \
  -c "UPDATE users SET role = 'ADMIN', is_verified = true WHERE email = 'admin@your-domain.tld';"
```

Что делает:

- `docker compose exec -T db psql ...` — выполняет SQL внутри контейнера
  базы (`-T` отключает псевдотерминал, удобно для скриптов);
- `UPDATE users` — меняет пользователя с указанным email;
- `role = 'ADMIN'` — выдаёт роль администратора (значение enum — заглавными);
- `is_verified = true` — подтверждает email.

4. Войдите заново — придёт код 2FA на email.

> Если при входе админа ошибка `503`, значит SMTP не настроен или письмо не
> уходит. Проверьте `docker compose logs backend | grep -i smtp` и настройки
> SMTP, затем `docker compose up -d --force-recreate backend`.

> ⚠️ Не запускайте `backend/scripts/seed_cityboost.py` на production: он
> удаляет все заявки и пользователей и создаёт демо-данные.

---

## 9. Проверка

- [ ] `https://your-domain.tld` открывается
- [ ] `http://` редиректит на `https://`
- [ ] `/health` отдаёт `{"status":"ok"}`
- [ ] Регистрация и письмо с кодом работают
- [ ] Вход/выход работает
- [ ] Админ входит с кодом 2FA
- [ ] Заявка создаётся, фото и карта работают
- [ ] `docker compose ps` — backend и db `healthy`
- [ ] `docker compose logs backend` без ошибок

---

## 10. Обновление

```bash
cd /opt/cityboost
git pull --ff-only
```

Что делает: скачивает изменения из репозитория. `--ff-only` запрещает
создавать merge-коммиты — если ветки разошлись, команда просто остановится.

```bash
docker compose up -d --build
```

Что делает: пересобирает изменившиеся образы и перезапускает контейнеры.
Миграции backend применяет автоматически при старте.

Проверка:

```bash
docker compose ps
docker compose logs --tail=50 backend
curl -fsS https://your-domain.tld/health
```

Если меняли `.env`, пересоздайте backend:

```bash
docker compose up -d --force-recreate backend
```

Что делает: `restart` не перечитывает `.env`, а `--force-recreate` создаёт
контейнер заново с новыми переменными.
---

## 11. Если что-то не работает

| Проблема | Что делать |
| --- | --- |
| `502 Bad Gateway` | `docker compose ps` и `docker compose logs backend` |
| Backend не стартует | проверьте `JWT_SECRET_KEY` (32+ символа) и `DEBUG=false` |
| Письма не приходят | `SMTP_PORT=587`, `SMTP_USE_TLS=true`, пароль приложения |
| Админ: `503` при 2FA | не настроен SMTP, смотрите логи backend |
| CORS-ошибка | `CORS_ORIGINS=https://ваш-домен` без слэша, пересоздать backend |
| `413` при загрузке | поднять `MAX_FILE_SIZE_MB` и `client_max_body_size` |
| Certbot: 404 | DNS на сервер, порт 80 открыт, nginx пересоздан с volume'ами |
| `frontend` `Exited (0)` | это нормально |
| Занят порт 80/443 | `ss -tulpn \| grep -E ':80\|:443'`, остановить чужой nginx |
| После обновления разлогинило | изменился `JWT_SECRET_KEY` — это ожидаемо |

Полезные команды:

```bash
cd /opt/cityboost
docker compose ps -a                 # статус всех контейнеров
docker compose logs -f backend       # логи backend в реальном времени
docker compose up -d --force-recreate backend  # пересоздать backend
docker compose exec nginx nginx -t   # проверить конфиг nginx
docker stats                         # CPU/RAM по контейнерам
df -h                                # свободное место на диске
```
