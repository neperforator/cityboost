#!/usr/bin/env python3
"""Мониторинг CityBoost с алертами в Telegram.

Изолированный sidecar: не импортирует код приложения и не меняет backend.
Проверяет HTTP-эндпоинты и TCP-порты, при проблеме отправляет сообщение
в Telegram, при восстановлении — сообщение о восстановлении.

Как удалить:
  1. Удалить сервис `health-alert` из docker-compose.yml.
  2. Удалить папку ops/health-alert.
  3. Удалить переменные TELEGRAM_* и HEALTH_ALERT_* из .env.

Запуск вручную (одна проверка):
  HEALTH_ALERT_DRY_RUN=true python monitor.py --once
"""

from __future__ import annotations

import json
import logging
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("cityboost.health_alert")


def _env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Некорректное значение %s=%r, использую %s", name, raw, default)
        return default


def _now(tz_name: str) -> datetime:
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        tz = UTC
    return datetime.now(tz)


@dataclass(slots=True)
class Config:
    """Настройки монитора из переменных окружения."""

    enabled: bool
    dry_run: bool
    token: str
    chat_id: str
    thread_id: int | None
    api_base: str
    interval: int
    timeout: float
    threshold: int
    repeat_seconds: int
    startup_delay: int
    timezone: str
    backend_url: str
    nginx_url: str
    external_url: str
    check_db: bool
    db_host: str
    db_port: int
    check_redis: bool
    redis_host: str
    redis_port: int

    @classmethod
    def from_env(cls) -> Config:
        thread_raw = _env_str("TELEGRAM_MESSAGE_THREAD_ID")
        try:
            thread_id = int(thread_raw) if thread_raw else None
        except ValueError:
            logger.warning("TELEGRAM_MESSAGE_THREAD_ID должен быть числом")
            thread_id = None

        return cls(
            enabled=_env_bool("HEALTH_ALERT_ENABLED", True),
            dry_run=_env_bool("HEALTH_ALERT_DRY_RUN", False),
            token=_env_str("TELEGRAM_BOT_TOKEN"),
            chat_id=_env_str("TELEGRAM_CHAT_ID"),
            thread_id=thread_id,
            api_base=_env_str("TELEGRAM_API_BASE", "https://api.telegram.org"),
            interval=max(10, _env_int("HEALTH_ALERT_INTERVAL_SECONDS", 60)),
            timeout=max(1, _env_int("HEALTH_ALERT_TIMEOUT_SECONDS", 5)),
            threshold=max(1, _env_int("HEALTH_ALERT_FAILURE_THRESHOLD", 2)),
            repeat_seconds=max(
                60,
                _env_int("HEALTH_ALERT_REPEAT_MINUTES", 30) * 60,
            ),
            startup_delay=max(
                0,
                _env_int("HEALTH_ALERT_STARTUP_DELAY_SECONDS", 20),
            ),
            timezone=_env_str("HEALTH_ALERT_TIMEZONE", "Europe/Minsk"),
            backend_url=_env_str(
                "HEALTH_ALERT_BACKEND_URL",
                "http://backend:8000/health",
            ),
            nginx_url=_env_str("HEALTH_ALERT_NGINX_URL", "http://nginx/health"),
            external_url=_env_str("HEALTH_ALERT_EXTERNAL_URL"),
            check_db=_env_bool("HEALTH_ALERT_CHECK_DB", True),
            db_host=_env_str("HEALTH_ALERT_DB_HOST", "db"),
            db_port=_env_int("HEALTH_ALERT_DB_PORT", 5432),
            check_redis=_env_bool("HEALTH_ALERT_CHECK_REDIS", True),
            redis_host=_env_str("HEALTH_ALERT_REDIS_HOST", "redis"),
            redis_port=_env_int("HEALTH_ALERT_REDIS_PORT", 6379),
        )


@dataclass(slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


@dataclass(slots=True)
class MonitorState:
    consecutive_failures: int = 0
    down_since: float | None = None
    last_alert_at: float | None = None
    is_down: bool = False


def check_http(name: str, url: str, timeout: float) -> CheckResult:
    if not url:
        return CheckResult(name, True, "отключено")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CityBoost-HealthAlert/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 0)
            if 200 <= status < 300:
                return CheckResult(name, True, f"HTTP {status}")
            return CheckResult(name, False, f"HTTP {status}")
    except urllib.error.HTTPError as exc:
        return CheckResult(name, False, f"HTTP {exc.code}")
    except Exception as exc:  # noqa: BLE001 — нужен текст любой сетевой ошибки
        return CheckResult(name, False, f"{type(exc).__name__}: {exc}")


def check_tcp(name: str, host: str, port: int, timeout: float) -> CheckResult:
    if not host or port <= 0:
        return CheckResult(name, True, "отключено")
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return CheckResult(name, True, f"{host}:{port}")
    except OSError as exc:
        return CheckResult(name, False, f"{host}:{port} — {exc}")


def run_checks(config: Config) -> list[CheckResult]:
    results = [
        check_http("backend", config.backend_url, config.timeout),
        check_http("nginx", config.nginx_url, config.timeout),
    ]
    if config.external_url:
        results.append(
            check_http("external", config.external_url, config.timeout),
        )
    if config.check_db:
        results.append(
            check_tcp("db", config.db_host, config.db_port, config.timeout),
        )
    if config.check_redis:
        results.append(
            check_tcp(
                "redis",
                config.redis_host,
                config.redis_port,
                config.timeout,
            ),
        )
    return results


def _format_results(results: list[CheckResult]) -> str:
    lines = []
    for result in results:
        icon = "✅" if result.ok else "❌"
        lines.append(f"• {result.name} — {icon} {result.detail}")
    return "\n".join(lines)


def format_alert(config: Config, results: list[CheckResult]) -> str:
    failed = [result.name for result in results if not result.ok]
    return (
        "🚨 CityBoost — проблема\n\n"
        f"Время: {_now(config.timezone):%d.%m.%Y %H:%M} ({config.timezone})\n"
        f"Не прошли проверки: {', '.join(failed)}\n\n"
        f"{_format_results(results)}\n\n"
        f"Повторные уведомления: раз в {config.repeat_seconds // 60} мин."
    )


def _human_duration(seconds: float) -> str:
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours} ч {minutes} мин"
    if minutes:
        return f"{minutes} мин {secs} сек"
    return f"{secs} сек"


def format_recovery(
    config: Config,
    results: list[CheckResult],
    downtime_seconds: float,
) -> str:
    return (
        "✅ CityBoost — восстановлено\n\n"
        f"Время: {_now(config.timezone):%d.%m.%Y %H:%M} ({config.timezone})\n"
        f"Простой: {_human_duration(downtime_seconds)}\n\n"
        f"{_format_results(results)}"
    )


def send_telegram(config: Config, text: str) -> bool:
    if config.dry_run:
        logger.info("DRY RUN — сообщение в Telegram:\n%s", text)
        return True

    url = f"{config.api_base.rstrip('/')}/bot{config.token}/sendMessage"
    payload: dict[str, object] = {
        "chat_id": config.chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if config.thread_id is not None:
        payload["message_thread_id"] = config.thread_id

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
        parsed = json.loads(body)
        if parsed.get("ok"):
            return True
        logger.error("Telegram API вернул ошибку: %s", body[:500])
        return False
    except Exception as exc:  # noqa: BLE001 — не роняем монитор из-за сети
        logger.error("Не удалось отправить сообщение в Telegram: %s", exc)
        return False


def print_chat_ids(config: Config) -> int:
    """Показать chat_id из сообщений, которые бот уже получил."""
    url = f"{config.api_base.rstrip('/')}/bot{config.token}/getUpdates"
    try:
        with urllib.request.urlopen(url, timeout=config.timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001 — показываем любую сетевую ошибку
        logger.error("Не удалось получить обновления Telegram: %s", exc)
        return 1

    parsed = json.loads(body)
    if not parsed.get("ok"):
        logger.error("Telegram API вернул ошибку: %s", body[:500])
        return 1

    chats: dict[object, tuple[str, str]] = {}
    for update in parsed.get("result", []):
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            continue
        title = (
            chat.get("title")
            or chat.get("username")
            or chat.get("first_name")
            or ""
        )
        chats[chat_id] = (chat.get("type", ""), title)

    if not chats:
        logger.warning(
            "Сообщений боту ещё нет. Откройте бота в Telegram, нажмите Start "
            "и отправьте любое сообщение, затем повторите команду.",
        )
        return 1

    print("Найденные chat_id:")
    for chat_id, (chat_type, title) in chats.items():
        print(f"  {chat_id}  ({chat_type}) {title}")
    print("\nВпишите нужный в .env: TELEGRAM_CHAT_ID=<id>")
    return 0


def run_once(config: Config) -> list[CheckResult]:
    results = run_checks(config)
    for result in results:
        level = logging.INFO if result.ok else logging.WARNING
        status = "ok" if result.ok else "FAIL"
        logger.log(level, "%s: %s (%s)", result.name, status, result.detail)
    return results


def run_forever(config: Config) -> None:
    if config.startup_delay:
        logger.info("Стартовая задержка: %s сек", config.startup_delay)
        time.sleep(config.startup_delay)

    state = MonitorState()
    logger.info(
        "Мониторинг запущен: интервал %s сек, порог %s, повтор %s мин",
        config.interval,
        config.threshold,
        config.repeat_seconds // 60,
    )

    while True:
        results = run_once(config)
        failed = [result for result in results if not result.ok]
        now = time.monotonic()

        if failed:
            state.consecutive_failures += 1
            if state.consecutive_failures >= config.threshold:
                alert_due = (
                    not state.is_down
                    or state.last_alert_at is None
                    or now - state.last_alert_at >= config.repeat_seconds
                )
                if alert_due:
                    if not state.is_down:
                        state.down_since = time.time()
                        state.is_down = True
                    if send_telegram(config, format_alert(config, results)):
                        state.last_alert_at = now
                    else:
                        logger.warning(
                            "Алерт не отправлен — повторю на следующей проверке",
                        )
        else:
            if state.is_down:
                downtime = time.time() - (state.down_since or time.time())
                send_telegram(
                    config,
                    format_recovery(config, results, downtime),
                )
            state = MonitorState()

        time.sleep(config.interval)


def main() -> int:
    config = Config.from_env()

    if not config.enabled:
        logger.info("HEALTH_ALERT_ENABLED=false — мониторинг отключён")
        return 0

    if "--chat-id" in sys.argv:
        if not config.token:
            logger.error("TELEGRAM_BOT_TOKEN не задан в .env")
            return 1
        return print_chat_ids(config)

    if not config.dry_run and (not config.token or not config.chat_id):
        logger.warning(
            "TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID не заданы — "
            "мониторинг отключён. Заполните их в .env и перезапустите сервис.",
        )
        return 0

    if "--test" in sys.argv:
        ok = send_telegram(
            config,
            "✅ CityBoost — тестовое сообщение. Health-алерты настроены.",
        )
        if ok:
            logger.info("Тестовое сообщение отправлено в Telegram")
        return 0 if ok else 1

    if "--once" in sys.argv:
        results = run_once(config)
        if any(not result.ok for result in results):
            send_telegram(config, format_alert(config, results))
        else:
            logger.info("Все проверки в норме")
        return 0

    try:
        run_forever(config)
    except KeyboardInterrupt:
        logger.info("Остановлено пользователем")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
