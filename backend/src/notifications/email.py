"""
Email-сервис для отправки писем через SMTP (smtplib).

Обёртка над стандартной библиотекой — работает асинхронно через asyncio.to_thread.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger("cityboost.email")


class EmailService:
    """
    Простой email-сервис, отправляющий письма через SMTP.

    Потокобезопасен — каждый вызов открывает/закрывает соединение.
    В production рекомендуется использовать пул соединений.
    """

    def __init__(
        self,
        host: str = "",
        port: int = 587,
        user: str = "",
        password: str = "",
        use_tls: bool = True,
        from_addr: str = "noreply@cityboost.ru",
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.use_tls = use_tls
        self.from_addr = from_addr
        self._enabled = bool(host and user)

    @property
    def enabled(self) -> bool:
        """Доступен ли SMTP для отправки."""
        return self._enabled

    def _send_sync(self, to: str, subject: str, html: str) -> bool:
        """
        Синхронная отправка письма (вызывается внутри to_thread).
        Возвращает True при успехе.
        """
        if not self.enabled:
            logger.warning("SMTP не настроен, письмо не отправлено: %s", to)
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                if self.use_tls:
                    server.starttls()
                if self.user:
                    server.login(self.user, self.password)
                server.sendmail(self.from_addr, [to], msg.as_string())
            logger.info("Письмо отправлено на %s: %s", to, subject)
            return True
        except smtplib.SMTPException as exc:
            logger.error("Ошибка SMTP при отправке на %s: %s", to, exc)
            return False
        except OSError as exc:
            logger.error("Ошибка сети SMTP (%s): %s", to, exc)
            return False

    async def send_email(self, to: str, subject: str, html: str) -> bool:
        """
        Асинхронная отправка email.
        Блокирующий SMTP-вызов выносится в поток через asyncio.to_thread.
        """
        return await asyncio.to_thread(self._send_sync, to, subject, html)

    async def send_password_reset(
        self, email: str, token: str, name: str, base_url: str = ""
    ) -> bool:
        """Отправить письмо для сброса пароля."""
        reset_link = f"{base_url}#/reset-password?token={token}"
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; background: #f4f4f6; padding: 40px 20px;">
  <div style="max-width: 480px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    <div style="text-align: center; font-size: 40px; margin-bottom: 16px;">🏙️</div>
    <h2 style="text-align: center; color: #1e1e2f; margin: 0 0 8px;">Сброс пароля</h2>
    <p style="color: #6b7280; font-size: 14px; text-align: center;">Здравствуйте, <strong>{name}</strong>!</p>
    <p style="color: #6b7280; font-size: 14px; text-align: center;">
      Вы запросили сброс пароля в CityBoost. Нажмите на кнопку ниже:
    </p>
    <div style="text-align: center; margin: 24px 0;">
      <a href="{reset_link}"
         style="display: inline-block; background: #4f46e5; color: #fff; font-size: 16px; font-weight: 600;
                padding: 12px 32px; border-radius: 8px; text-decoration: none;">
        Сбросить пароль
      </a>
    </div>
    <p style="color: #9ca3af; font-size: 12px; text-align: center;">
      Ссылка действительна 1 час. Если вы не запрашивали сброс, проигнорируйте это письмо.
    </p>
  </div>
</body>
</html>"""
        return await self.send_email(email, "CityBoost — Сброс пароля", html)


# Экземпляр по умолчанию, инициализируется настройками
default_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Получить или создать EmailService из глобальных настроек."""
    global default_email_service
    if default_email_service is None:
        from src.config import settings

        default_email_service = EmailService(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            user=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
            from_addr=settings.SMTP_FROM,
        )
    return default_email_service


# Импорт asyncio внизу, чтобы не мешал TYPE_CHECKING
import asyncio  # noqa: E402
