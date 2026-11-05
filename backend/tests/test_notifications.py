"""Тесты email-уведомлений по заявкам."""

from __future__ import annotations

import struct
import zlib
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.auth.service import AuthService
from src.tickets.models import Ticket, TicketStatus

pytestmark = pytest.mark.asyncio

PASSWORD = "StrongPass1"


def _mini_png() -> bytes:
    """Минимальный валидный PNG (1×1, красный)."""
    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        raw = chunk_type + data
        return (
            struct.pack(">I", len(data))
            + raw
            + struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\x00\x00")
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", idat)
        + _chunk(b"IEND", b"")
    )


async def _create_user(
    db_session: AsyncSession,
    *,
    email: str,
    role: UserRole = UserRole.USER,
    name: str = "Пользователь",
) -> User:
    user = User(
        name=name,
        email=email,
        password_hash=AuthService.hash_password(PASSWORD),
        role=role,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


def _auth(user: User) -> dict[str, str]:
    token = AuthService.create_access_token(
        {"sub": str(user.id)},
        token_version=user.token_version,
    )
    return {"Authorization": f"Bearer {token}"}


async def _create_ticket(
    db_session: AsyncSession,
    author: User,
    *,
    title: str = "Тестовая заявка",
    status: TicketStatus = TicketStatus.NEW,
    assignee: User | None = None,
    notify_author: bool = True,
) -> Ticket:
    ticket = Ticket(
        user_id=author.id,
        title=title,
        description="Описание заявки",
        status=status,
        assigned_to=assignee.id if assignee else None,
        notify_author=notify_author,
    )
    db_session.add(ticket)
    await db_session.flush()
    return ticket


class TestCreateNotification:
    async def test_create_ticket_notifies_author(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch,
    ):
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        send_created = AsyncMock()
        monkeypatch.setattr("src.tickets.router.send_ticket_created", send_created)

        response = await client.post(
            "/api/v1/tickets",
            data={
                "title": "Яма во дворе",
                "description": "Нужно заделать",
                "address": "ул. Ленина, 1",
            },
            files=[("files", ("test.png", _mini_png(), "image/png"))],
            headers=_auth(author),
        )

        assert response.status_code == 201, response.text
        send_created.assert_awaited_once()
        kwargs = send_created.await_args.kwargs
        assert kwargs["to"] == author.email
        assert kwargs["ticket_title"] == "Яма во дворе"


class TestStatusNotification:
    async def test_status_change_notifies_author(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch,
    ):
        admin = await _create_user(
            db_session, email="admin@test.com", role=UserRole.ADMIN, name="Админ",
        )
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        ticket = await _create_ticket(db_session, author)
        send_status = AsyncMock()
        monkeypatch.setattr(
            "src.tickets.admin.send_ticket_status_changed", send_status,
        )

        response = await client.patch(
            f"/api/v1/admin/tickets/{ticket.id}/status",
            json={"new_status": "IN_WORK"},
            headers=_auth(admin),
        )

        assert response.status_code == 200, response.text
        send_status.assert_awaited_once()
        kwargs = send_status.await_args.kwargs
        assert kwargs["to"] == author.email
        assert kwargs["old_status"] == "NEW"
        assert kwargs["new_status"] == "IN_WORK"

    async def test_repeated_status_does_not_notify(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch,
    ):
        admin = await _create_user(
            db_session, email="admin@test.com", role=UserRole.ADMIN, name="Админ",
        )
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        ticket = await _create_ticket(
            db_session, author, status=TicketStatus.IN_WORK,
        )
        send_status = AsyncMock()
        monkeypatch.setattr(
            "src.tickets.admin.send_ticket_status_changed", send_status,
        )

        response = await client.patch(
            f"/api/v1/admin/tickets/{ticket.id}/status",
            json={"new_status": "IN_WORK"},
            headers=_auth(admin),
        )

        assert response.status_code == 200, response.text
        send_status.assert_not_awaited()


class TestAssignNotification:
    async def test_assign_notifies_author_about_new_status(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch,
    ):
        admin = await _create_user(
            db_session, email="admin@test.com", role=UserRole.ADMIN, name="Админ",
        )
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        ticket = await _create_ticket(db_session, author)
        send_status = AsyncMock()
        monkeypatch.setattr(
            "src.tickets.admin.send_ticket_status_changed", send_status,
        )

        response = await client.patch(
            f"/api/v1/admin/tickets/{ticket.id}/assign",
            headers=_auth(admin),
        )

        assert response.status_code == 200, response.text
        send_status.assert_awaited_once()
        assert send_status.await_args.kwargs["to"] == author.email
        assert send_status.await_args.kwargs["new_status"] == "IN_WORK"


class TestCommentNotification:
    async def test_admin_comment_notifies_author(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch,
    ):
        admin = await _create_user(
            db_session, email="admin@test.com", role=UserRole.ADMIN, name="Админ",
        )
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        ticket = await _create_ticket(db_session, author, assignee=admin)
        send_comment = AsyncMock()
        monkeypatch.setattr("src.tickets.admin.send_ticket_comment", send_comment)

        response = await client.post(
            f"/api/v1/admin/tickets/{ticket.id}/comments",
            json={"comment_text": "Выехали на место"},
            headers=_auth(admin),
        )

        assert response.status_code == 201, response.text
        send_comment.assert_awaited_once()
        kwargs = send_comment.await_args.kwargs
        assert kwargs["to"] == author.email
        assert kwargs["admin_link"] is False
        assert kwargs["author_name"] == "Админ"

    async def test_user_comment_does_not_notify_assignee(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch,
    ):
        admin = await _create_user(
            db_session, email="admin@test.com", role=UserRole.ADMIN, name="Админ",
        )
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        ticket = await _create_ticket(
            db_session, author, status=TicketStatus.IN_WORK, assignee=admin,
        )
        send_comment = AsyncMock()
        monkeypatch.setattr("src.tickets.router.send_ticket_comment", send_comment)

        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/comments",
            json={"comment_text": "Когда приедете?"},
            headers=_auth(author),
        )

        assert response.status_code == 201, response.text
        # Автор — сам комментатор, а исполнителя не уведомляем.
        send_comment.assert_not_awaited()

    async def test_admin_comment_via_user_route_notifies_author(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch,
    ):
        admin = await _create_user(
            db_session, email="admin@test.com", role=UserRole.ADMIN, name="Админ",
        )
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        ticket = await _create_ticket(
            db_session, author, status=TicketStatus.IN_WORK, assignee=admin,
        )
        send_comment = AsyncMock()
        monkeypatch.setattr("src.tickets.router.send_ticket_comment", send_comment)

        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/comments",
            json={"comment_text": "Выехали на место"},
            headers=_auth(admin),
        )

        assert response.status_code == 201, response.text
        send_comment.assert_awaited_once()
        kwargs = send_comment.await_args.kwargs
        assert kwargs["to"] == author.email
        assert kwargs["admin_link"] is False
        assert kwargs["author_name"] == "Админ"

    async def test_comment_does_not_notify_commenter(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch,
    ):
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        ticket = await _create_ticket(db_session, author)
        send_comment = AsyncMock()
        monkeypatch.setattr("src.tickets.router.send_ticket_comment", send_comment)

        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/comments",
            json={"comment_text": "Добавляю детали"},
            headers=_auth(author),
        )

        assert response.status_code == 201, response.text
        send_comment.assert_not_awaited()


class TestNotificationPreference:
    async def test_create_without_notifications_does_not_send(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch,
    ):
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        send_created = AsyncMock()
        monkeypatch.setattr("src.tickets.router.send_ticket_created", send_created)

        response = await client.post(
            "/api/v1/tickets",
            data={
                "title": "Без уведомлений",
                "description": "Не нужно писать на почту",
                "notify_author": "false",
            },
            files=[("files", ("test.png", _mini_png(), "image/png"))],
            headers=_auth(author),
        )

        assert response.status_code == 201, response.text
        assert response.json()["notify_author"] is False
        send_created.assert_not_awaited()

    async def test_status_change_respects_disabled_notifications(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch,
    ):
        admin = await _create_user(
            db_session, email="admin@test.com", role=UserRole.ADMIN, name="Админ",
        )
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        ticket = await _create_ticket(db_session, author, notify_author=False)
        send_status = AsyncMock()
        monkeypatch.setattr(
            "src.tickets.admin.send_ticket_status_changed", send_status,
        )

        response = await client.patch(
            f"/api/v1/admin/tickets/{ticket.id}/status",
            json={"new_status": "IN_WORK"},
            headers=_auth(admin),
        )

        assert response.status_code == 200, response.text
        send_status.assert_not_awaited()

    async def test_comment_respects_disabled_notifications(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        monkeypatch,
    ):
        admin = await _create_user(
            db_session, email="admin@test.com", role=UserRole.ADMIN, name="Админ",
        )
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        ticket = await _create_ticket(
            db_session, author, assignee=admin, notify_author=False,
        )
        send_comment = AsyncMock()
        monkeypatch.setattr("src.tickets.admin.send_ticket_comment", send_comment)

        response = await client.post(
            f"/api/v1/admin/tickets/{ticket.id}/comments",
            json={"comment_text": "Комментарий без письма"},
            headers=_auth(admin),
        )

        assert response.status_code == 201, response.text
        send_comment.assert_not_awaited()

    async def test_author_can_toggle_notifications(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        ticket = await _create_ticket(db_session, author)

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/notifications",
            json={"notify_author": False},
            headers=_auth(author),
        )

        assert response.status_code == 200, response.text
        assert response.json()["notify_author"] is False

        detail = await client.get(
            f"/api/v1/tickets/{ticket.id}",
            headers=_auth(author),
        )
        assert detail.status_code == 200, detail.text
        assert detail.json()["notify_author"] is False

    async def test_other_user_cannot_toggle_notifications(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        author = await _create_user(db_session, email="author@test.com", name="Автор")
        stranger = await _create_user(db_session, email="stranger@test.com", name="Чужой")
        ticket = await _create_ticket(db_session, author)

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/notifications",
            json={"notify_author": False},
            headers=_auth(stranger),
        )

        assert response.status_code == 403, response.text
