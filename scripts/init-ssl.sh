#!/bin/bash
# ============================================================
# init-ssl.sh — Первоначальная генерация SSL-сертификата
# через Let's Encrypt (Certbot) + Docker Compose
#
# Использование:
#   1. Укажите DOMAIN (реальный домен,指向ющий на сервер)
#   2. Укажите EMAIL для уведомлений Let's Encrypt
#   3. Запустите: bash scripts/init-ssl.sh
#
# Порядок:
#   1. Запускает nginx (на 80 порту для ACME challenge)
#   2. Запускает certbot для получения сертификата
#   3. Перезапускает nginx с SSL-конфигурацией
# ============================================================

set -euo pipefail

# ===== Конфигурация — ЗАМЕНИТЕ НА СВОИ ЗНАЧЕНИЯ =====
DOMAIN="${1:-ваш-домен.ru}"
EMAIL="${2:-admin@${DOMAIN}}"

echo "=========================================="
echo "  CityBoost — SSL Init"
echo "  Domain:  $DOMAIN"
echo "  Email:   $EMAIL"
echo "=========================================="

# Убедимся, что папки для certbot существуют
mkdir -p certbot/www certbot/conf

# 1. Запускаем nginx (только HTTP — ACME challenge)
echo
echo "[1/4] Запуск nginx для ACME challenge..."
docker compose up -d nginx
echo "      Ожидание готовности nginx..."
sleep 3

# 2. Получаем сертификат через certbot
echo
echo "[2/4] Запрос сертификата Let's Encrypt..."
docker compose run --rm certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --domain "$DOMAIN" \
    --agree-tos \
    --no-eff-email \
    --force-renewal

echo "      Сертификат получен!"

# 3. Редактируем ssl.conf — подставляем домен
echo
echo "[3/4] Обновление ssl.conf..."
if [[ -f nginx/ssl.conf ]]; then
    # Заменяем placeholder домена на реальный
    sed -i "s/ваш-домен\.ru/$DOMAIN/g" nginx/ssl.conf
    echo "      ssl.conf обновлён для домена $DOMAIN"
fi

# 4. Перезапускаем nginx с SSL
echo
echo "[4/4] Перезапуск nginx с SSL..."
docker compose up -d nginx

echo
echo "=========================================="
echo "  Готово! HTTPS работает: https://$DOMAIN"
echo "=========================================="
echo
echo "Авто-обновление сертификата:"
echo "  Сертификат обновляется автоматически"
echo "  каждые 12 часов через certbot контейнер."
echo
echo "Ручное обновление:"
echo "  docker compose run --rm certbot renew"
echo "  docker compose exec nginx nginx -s reload"
echo
