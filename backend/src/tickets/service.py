"""
Сервисный слой для заявок.
"""

from __future__ import annotations

import contextlib
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.tickets.models import Ticket, TicketComment, TicketFile, TicketStatus
from src.tickets.repository import (
    TicketCommentRepository,
    TicketFileRepository,
    TicketHistoryRepository,
    TicketRepository,
)

STATUS_LABELS: dict[str, str] = {
    "NEW": "Новая",
    "IN_WORK": "В работе",
    "DONE": "Выполнена",
    "CLOSED": "Отклонена",
}


def _status_label(status: str | None) -> str:
    return STATUS_LABELS.get(status or "", status or "—")


class TicketService:
    """Сервис для операций с заявками."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TicketRepository()
        self.file_repo = TicketFileRepository()
        self.history_repo = TicketHistoryRepository()
        self.comment_repo = TicketCommentRepository()

    async def create_ticket_with_files(
        self,
        user_id: uuid.UUID,
        title: str,
        description: str,
        file_data_list: list[tuple[str, bytes, str]],  # (mime, contents, extension)
        latitude: float | None = None,
        longitude: float | None = None,
        address: str | None = None,
        notify_author: bool = True,
    ) -> Ticket:
        """Создать заявку с файлами — всё в одной транзакции."""
        # Создаём заявку
        ticket = await self.repo.create(
            db=self.db,
            user_id=user_id,
            title=title,
            description=description,
            latitude=latitude,
            longitude=longitude,
            address=address,
            notify_author=notify_author,
        )

        upload_dir = Path(settings.UPLOAD_PATH) / str(ticket.id)
        created_files: list[Path] = []
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
            for mime_type, contents, extension in file_data_list:
                # Имя и расширение генерируем сами: оригинальное имя не используется.
                unique_name = f"{uuid.uuid4().hex}{extension}"
                file_path = upload_dir / unique_name
                file_path.write_bytes(contents)
                created_files.append(file_path)

                relative_path = f"uploads/tickets/{ticket.id}/{unique_name}"
                await self.file_repo.create(
                    self.db,
                    ticket.id,
                    relative_path,
                    len(contents),
                    mime_type,
                )

            await self.history_repo.create(
                self.db, ticket.id, user_id, "CREATED", None, ticket.status.value,
                f"Заявка создана с {len(file_data_list)} фото",
            )
        except Exception:
            # Не оставляем «осиротевшие» файлы при ошибке записи/БД.
            for path in created_files:
                path.unlink(missing_ok=True)
            with contextlib.suppress(OSError):
                upload_dir.rmdir()
            raise

        # Загружаем связи, чтобы сериализация не делала lazy-load в async-контексте.
        loaded = await self.repo.get_by_id(self.db, ticket.id)
        return loaded or ticket

    async def save_file(
        self,
        *,
        ticket: Ticket,
        contents: bytes,
        extension: str,
        mime_type: str,
        author_id: uuid.UUID,
    ) -> TicketFile:
        """Сохранить файл на диск и в БД с очисткой при ошибке."""
        upload_dir = Path(settings.UPLOAD_PATH) / str(ticket.id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        unique_name = f"{uuid.uuid4().hex}{extension}"
        file_path = upload_dir / unique_name
        relative_path = f"uploads/tickets/{ticket.id}/{unique_name}"

        file_path.write_bytes(contents)
        try:
            file_record = await self.file_repo.create(
                self.db, ticket.id, relative_path, len(contents), mime_type,
            )
            await self.history_repo.create(
                self.db,
                ticket.id,
                author_id,
                "FILE_ADDED",
                None,
                ticket.status.value,
                f"Прикреплён файл {unique_name}",
            )
        except Exception:
            file_path.unlink(missing_ok=True)
            raise

        return file_record

    async def get_ticket(self, ticket_id: uuid.UUID) -> Ticket | None:
        """Получить заявку по ID."""
        return await self.repo.get_by_id(self.db, ticket_id)

    async def set_notify_author(
        self,
        ticket_id: uuid.UUID,
        notify_author: bool,
    ) -> Ticket | None:
        """Включить или выключить email-уведомления по заявке."""
        ticket = await self.repo.get_by_id_simple(self.db, ticket_id)
        if ticket is None:
            return None
        ticket.notify_author = notify_author
        await self.db.flush()
        return await self.repo.get_by_id(self.db, ticket_id)

    async def list_user_tickets(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: TicketStatus | None = None,
    ) -> tuple[list[Ticket], int]:
        """Список заявок пользователя с пагинацией и фильтром."""
        return await self.repo.list_by_user(self.db, user_id, page, page_size, status)

    async def change_status(
        self,
        ticket_id: uuid.UUID,
        new_status: TicketStatus,
        changed_by: uuid.UUID,
        close_reason: str | None = None,
    ) -> Ticket | None:
        """Изменить статус заявки с логированием в TicketHistory."""
        ticket = await self.repo.get_by_id_simple(self.db, ticket_id)
        if ticket is None:
            return None
        old_status = ticket.status.value if ticket.status else None
        if old_status == new_status.value:
            return ticket
        if new_status == TicketStatus.CLOSED and not (close_reason or "").strip():
            raise ValueError("Необходимо указать причину отклонения заявки")

        updated = await self.repo.update_status(
            self.db, ticket_id, new_status, close_reason=close_reason,
        )
        if updated:
            details = f"Статус изменён с «{_status_label(old_status)}» на «{_status_label(new_status.value)}»"
            if new_status == TicketStatus.CLOSED:
                details += f". Причина отклонения: {close_reason}"
            await self.history_repo.create(
                self.db,
                ticket_id,
                changed_by,
                "STATUS_CHANGED",
                old_status,
                new_status.value,
                details,
            )
        return updated

    async def assign_ticket(
        self,
        ticket_id: uuid.UUID,
        admin_id: uuid.UUID,
        admin_name: str = "",
    ) -> Ticket | None:
        """Назначить заявку администратору (с записью в историю)."""
        ticket = await self.repo.get_by_id_simple(self.db, ticket_id)
        if ticket is None:
            return None
        old_status = ticket.status.value if ticket.status else None

        updated = await self.repo.assign(self.db, ticket_id, admin_id)
        if updated:
            await self.history_repo.create(
                self.db,
                ticket_id,
                admin_id,
                "ASSIGNED",
                old_status,
                updated.status.value,
                f"Заявка назначена на администратора {admin_name}".strip(),
            )
        return updated

    async def add_comment(
        self,
        ticket_id: uuid.UUID,
        author_id: uuid.UUID,
        text: str,
    ) -> TicketComment | None:
        """Добавить сообщение к заявке."""
        ticket = await self.repo.get_by_id_simple(self.db, ticket_id)
        if ticket is None:
            return None
        if ticket.status in (TicketStatus.DONE, TicketStatus.CLOSED):
            raise ValueError(
                "Нельзя добавить сообщение к заявке со статусом «Выполнена» или «Отклонена»",
            )
        comment = await self.comment_repo.create(self.db, ticket_id, author_id, text)
        await self.history_repo.create(
            self.db,
            ticket_id,
            author_id,
            "COMMENT_ADDED",
            None,
            ticket.status.value,
            "Добавлено сообщение",
        )
        return comment

    async def add_file(
        self,
        ticket_id: uuid.UUID,
        file_path: str,
        file_size: int,
        mime_type: str,
        author_id: uuid.UUID,
    ) -> TicketFile | None:
        """Прикрепить файл к заявке."""
        ticket = await self.repo.get_by_id_simple(self.db, ticket_id)
        if ticket is None:
            return None
        if ticket.status in (TicketStatus.DONE, TicketStatus.CLOSED):
            raise ValueError(
                "Нельзя загрузить файл к заявке со статусом «Выполнена» или «Отклонена»",
            )
        file_record = await self.file_repo.create(
            self.db, ticket_id, file_path, file_size, mime_type,
        )
        await self.history_repo.create(
            self.db,
            ticket_id,
            author_id,
            "FILE_ADDED",
            None,
            ticket.status.value,
            f"Прикреплён файл {file_path.rsplit('/', 1)[-1]}",
        )
        return file_record

    async def get_file_count(self, ticket_id: uuid.UUID) -> int:
        """Количество файлов у заявки."""
        return await self.file_repo.count_by_ticket(self.db, ticket_id)
