#!/bin/sh
# Nginx читает этот шаблон при старте контейнера и собирает рабочий конфиг
# в /etc/nginx/conf.d/default.conf.
#
# Rate limiting следует за DEBUG — так же, как backend пропускает свой
# RateLimitMiddleware при DEBUG=true:
#   DEBUG=true  -> директивы limit_req закомментированы (лимитов нет);
#   DEBUG=false -> лимиты работают как в конфиге.
#
# Зоны limit_req_zone остаются объявленными: это безвредно и позволяет
# не держать два разных конфига.
#
# После правки nginx/default.conf нужен `docker compose restart nginx`,
# а после смены DEBUG в .env — `docker compose up -d --force-recreate nginx`.
set -e

TEMPLATE=/etc/nginx/templates/default.conf
TARGET=/etc/nginx/conf.d/default.conf

case "$(printf '%s' "${DEBUG:-false}" | tr -d '\r' | tr 'A-Z' 'a-z')" in
    true|1|yes)
        # Комментируем только `limit_req ...`; `limit_req_zone` не трогаем.
        sed -E 's/^([[:space:]]*)(limit_req[[:space:]])/\1# \2/' \
            "$TEMPLATE" > "$TARGET"
        echo ">>> DEBUG=true: rate limiting nginx отключён."
        ;;
    *)
        cp "$TEMPLATE" "$TARGET"
        echo ">>> DEBUG=false: rate limiting nginx включён."
        ;;
esac

# Проверяем конфиг до запуска: при ошибке контейнер сразу остановится,
# а причина будет видна в `docker compose logs nginx`.
nginx -t

# Docker передаёт сюда CMD образа: nginx -g 'daemon off;'
exec "$@"

