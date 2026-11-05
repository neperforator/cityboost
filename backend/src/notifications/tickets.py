"""Email-уведомления по заявкам.

Все письма строятся здесь, а отправка идёт через общий EmailService.
Пользовательские данные экранируются, чтобы их нельзя было использовать
для HTML-инъекций в письме.
"""

from __future__ import annotations

import uuid

from src.config import settings
from src.notifications.email import get_email_service
from src.notifications.layout import (
    esc,
    meta_block,
    note_block,
    quote_block,
    render_email,
    route_block,
    status_badge,
)

STATUS_LABELS: dict[str, str] = {
    "NEW": "Новая",
    "IN_WORK": "В работе",
    "DONE": "Выполнена",
    "CLOSED": "Отклонена",
}

_COMMENT_PREVIEW_LIMIT = 600


def _frontend_url(path: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/#/{path.lstrip('/')}"


def _ticket_url(ticket_id: uuid.UUID | str) -> str:
    return _frontend_url(f"tickets/{ticket_id}")


def _admin_ticket_url(ticket_id: uuid.UUID | str) -> str:
    return _frontend_url(f"admin/tickets/{ticket_id}")


def _ticket_ref(ticket_id: uuid.UUID | str) -> str:
    """Короткий номер заявки для шапки бланка."""
    return str(ticket_id).replace("-", "")[:8].upper()


def _subject_title(title: str, limit: int = 80) -> str:
    """Заголовок для темы письма: без переносов и лишней длины."""
    cleaned = " ".join((title or "Заявка").split())
    return cleaned if len(cleaned) <= limit else f"{cleaned[: limit - 1]}…"


async def send_ticket_created(
    *,
    to: str,
    name: str,
    ticket_id: uuid.UUID | str,
    ticket_title: str,
    address: str | None = None,
) -> bool:
    """Подтвердить пользователю, что заявка создана."""
    rows: list[tuple[str, str]] = [("Заявка", ticket_title)]
    if address:
        rows.append(("Адрес", address))

    html = render_email(
        preheader=f"Заявка «{ticket_title}» принята.",
        heading="Заявка принята",
        intro=(
            f"Здравствуйте, {esc(name or 'пользователь')}. "
            "Заявка зарегистрирована — уведомим, когда она изменится."
        ),
        blocks=[meta_block(rows), route_block("NEW")],
        cta_text="Открыть заявку",
        cta_url=_ticket_url(ticket_id),
        footer=(
            "Вы получаете письмо, потому что следите за этой заявкой. "
            "Отключить уведомления можно в карточке заявки."
        ),
        reference=_ticket_ref(ticket_id),
    )
    return await get_email_service().send_email(
        to,
        f"CityBoost — заявка «{_subject_title(ticket_title)}» принята",
        html,
    )


async def send_ticket_status_changed(
    *,
    to: str,
    name: str,
    ticket_id: uuid.UUID | str,
    ticket_title: str,
    old_status: str | None,
    new_status: str,
    close_reason: str | None = None,
) -> bool:
    """Сообщить автору заявки о смене статуса."""
    new_label = STATUS_LABELS.get(new_status, new_status)
    rows: list[tuple[str, str]] = [
        ("Заявка", esc(ticket_title)),
        ("Было", status_badge(old_status) if old_status else "—"),
        ("Стало", status_badge(new_status)),
    ]
    blocks = [meta_block(rows, allow_html=True)]

    if new_status == "DONE":
        heading = "Заявка выполнена"
        intro_text = (
            f"Здравствуйте, {esc(name or 'пользователь')}. "
            "Работа по вашей заявке завершена."
        )
        blocks.append(route_block("DONE"))
    elif new_status == "CLOSED":
        # CLOSED — это не этап маршрута, а снятие заявки: спам, дубль,
        # не относится к городу. Поэтому маршрут здесь не рисуем.
        heading = "Заявка отклонена"
        intro_text = (
            f"Здравствуйте, {esc(name or 'пользователь')}. "
            "Заявка снята с рассмотрения и не будет выполнена."
        )
        if close_reason:
            blocks.append(note_block(f"Причина отклонения: {close_reason}"))
    else:
        heading = "Статус изменился"
        intro_text = (
            f"Здравствуйте, {esc(name or 'пользователь')}. "
            "По вашей заявке есть изменения."
        )
        blocks.append(route_block(new_status))

    html = render_email(
        preheader=f"Заявка «{ticket_title}»: {new_label.lower()}.",
        heading=heading,
        intro=intro_text,
        blocks=blocks,
        cta_text="Открыть заявку",
        cta_url=_ticket_url(ticket_id),
        footer=(
            "Вы получаете письмо, потому что следите за этой заявкой. "
            "Отключить уведомления можно в карточке заявки."
        ),
        reference=_ticket_ref(ticket_id),
    )
    return await get_email_service().send_email(
        to,
        f"CityBoost — заявка «{_subject_title(ticket_title)}»: {new_label.lower()}",
        html,
    )


async def send_ticket_comment(
    *,
    to: str,
    name: str,
    ticket_id: uuid.UUID | str,
    ticket_title: str,
    author_name: str,
    comment_text: str,
    admin_link: bool = False,
) -> bool:
    """Сообщить о новом сообщении по заявке."""
    preview = comment_text.strip()
    if len(preview) > _COMMENT_PREVIEW_LIMIT:
        preview = f"{preview[: _COMMENT_PREVIEW_LIMIT - 1]}…"

    html = render_email(
        preheader=f"Новое сообщение от {author_name}.",
        heading="Новое сообщение",
        intro=(
            f"Здравствуйте, {esc(name or 'пользователь')}. "
            "В вашей заявке появилось новое сообщение."
        ),
        blocks=[
            meta_block([("Заявка", ticket_title)]),
            quote_block(author_name or "пользователь", preview),
        ],
        cta_text="Открыть в админ-панели" if admin_link else "Открыть заявку",
        cta_url=(
            _admin_ticket_url(ticket_id)
            if admin_link
            else _ticket_url(ticket_id)
        ),
        footer=(
            "Вы получаете письмо, потому что следите за этой заявкой. "
            "Отключить уведомления можно в карточке заявки."
        ),
        reference=_ticket_ref(ticket_id),
    )
    return await get_email_service().send_email(
        to,
        f"CityBoost — новое сообщение по заявке «{_subject_title(ticket_title)}»",
        html,
    )
