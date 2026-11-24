#!/bin/sh
# Entrypoint nginx: собирает рабочий конфиг из шаблона и генерирует
# include-сниппет для API-документации.
#
# Почему так:
#   * nginx не умеет читать .env, поэтому решение принимается здесь;
#   * rate limiting следует за DEBUG — как backend, который при DEBUG=true
#     не применяет свой RateLimitMiddleware:
#       DEBUG=true  -> директивы limit_req закомментированы;
#       DEBUG=false -> лимиты работают как в конфиге.
#   * docs включены, если DEBUG=true или ENABLE_DOCS=true (так же, как
#     settings.DOCS_ENABLED в backend). Иначе /docs, /redoc и /openapi.json
#     получают обычный 404 и не палят существование ручки.
#
# После правки nginx/default.conf нужен `docker compose restart nginx`,
# а после смены DEBUG/ENABLE_DOCS в .env —
# `docker compose up -d --force-recreate nginx`.
set -e

TEMPLATE=/etc/nginx/templates/default.conf
TARGET=/etc/nginx/conf.d/default.conf
SNIPPET_DIR=/etc/nginx/snippets
DOCS_SNIPPET="$SNIPPET_DIR/docs.conf"

is_true() {
    case "$(printf '%s' "${1:-false}" | tr -d '\r' | tr 'A-Z' 'a-z')" in
        true|1|yes) return 0 ;;
        *) return 1 ;;
    esac
}

mkdir -p "$SNIPPET_DIR"

# --- Rate limiting ---
if is_true "${DEBUG:-false}"; then
    # Комментируем только `limit_req ...`; `limit_req_zone` не трогаем.
    sed -E 's/^([[:space:]]*)(limit_req[[:space:]])/\1# \2/' \
        "$TEMPLATE" > "$TARGET"
    echo ">>> DEBUG=true: rate limiting nginx отключён."
else
    cp "$TEMPLATE" "$TARGET"
    echo ">>> DEBUG=false: rate limiting nginx включён."
fi

# --- API Docs ---
if is_true "${DEBUG:-false}" || is_true "${ENABLE_DOCS:-false}"; then
    cat > "$DOCS_SNIPPET" <<'EOF'
# Docs включены (DEBUG=true или ENABLE_DOCS=true): проксируем на backend.
location ~ ^/(docs|redoc|openapi\.json)(/.*)?$ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Request-ID $request_id;
    proxy_hide_header X-Powered-By;
}
EOF
    echo ">>> docs включены (DEBUG/ENABLE_DOCS)."
else
    cat > "$DOCS_SNIPPET" <<'EOF'
# Docs выключены: тот же 404, что и для любого несуществующего пути.
location ~ ^/(docs|redoc|openapi\.json)(/.*)?$ {
    return 404;
}
EOF
    echo ">>> docs выключены: отдаём 404."
fi

# Проверяем конфиг до запуска: при ошибке контейнер сразу остановится,
# а причина будет видна в `docker compose logs nginx`.
nginx -t

# Docker может не передать CMD при переопределённом entrypoint,
# поэтому запускаем nginx сами, если аргументов нет.
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

exec nginx -g 'daemon off;'
