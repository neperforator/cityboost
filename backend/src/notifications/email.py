"""
Email-сервис для отправки писем через SMTP (smtplib).

Обёртка над стандартной библиотекой — работает асинхронно через asyncio.to_thread.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr
from html import escape as html_escape
from typing import TYPE_CHECKING

from src.notifications.layout import code_block, render_email

if TYPE_CHECKING:
    pass

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

        # В конверте SMTP должен быть чистый адрес: «Имя <адрес>» там недопустимо.
        envelope_from = parseaddr(self.from_addr)[1] or self.from_addr

        try:
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                if self.use_tls:
                    server.starttls()
                if self.user:
                    server.login(self.user, self.password)
                server.sendmail(envelope_from, [to], msg.as_string())
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
        if not base_url:
            from src.config import settings

            base_url = settings.FRONTEND_URL
        reset_link = f"{base_url}#/reset-password?token={token}"
        html = render_email(
            preheader="Ссылка для сброса пароля CityBoost.",
            heading="Сброс пароля",
            intro=(
                f"Здравствуйте, {html_escape(name or 'пользователь')}. "
                "Мы получили запрос на новый пароль для вашего аккаунта."
            ),
            blocks=[],
            cta_text="Задать новый пароль",
            cta_url=reset_link,
            footer=(
                "Ссылка действует 1 час. Если вы не запрашивали сброс, "
                "просто проигнорируйте это письмо."
            ),
        )
        return await self.send_email(email, "CityBoost — Сброс пароля", html)

    async def send_verification_code(self, email: str, code: str, name: str) -> bool:
        """Отправить код подтверждения email."""
        html = render_email(
            preheader="Код подтверждения email CityBoost.",
            heading="Подтвердите email",
            intro=(
                f"Здравствуйте, {html_escape(name or 'пользователь')}. "
                "Введите код ниже в окне подтверждения CityBoost."
            ),
            blocks=[code_block(code)],
            footer=(
                "Код действует 10 минут. Если вы не регистрировались в CityBoost, "
                "проигнорируйте это письмо."
            ),
        )
        return await self.send_email(email, "CityBoost — Код подтверждения", html)

    async def send_admin_2fa_code(
        self,
        email: str,
        code: str,
        name: str,
        expires_minutes: int = 10,
    ) -> bool:
        """Отправить код подтверждения входа для администратора."""
        html = render_email(
            preheader="Код для входа в панель администратора CityBoost.",
            heading="Код для входа",
            intro=(
                f"Здравствуйте, {html_escape(name or 'пользователь')}. "
                "Введите код ниже, чтобы войти в панель администратора."
            ),
            blocks=[code_block(code)],
            footer=(
                f"Код действует {expires_minutes} минут. "
                "Если вы не пытались войти, смените пароль."
            ),
        )
        return await self.send_email(email, "CityBoost — Код подтверждения входа", html)


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
