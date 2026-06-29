"""
Сервисный слой для заявок.
"""

from __future__ import annotations

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
from src.tickets.schemas import TicketCreateRequest


class TicketService:
    """Сервис для операций с заявками."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TicketRepository()
        self.file_repo = TicketFileRepository()
        self.history_repo = TicketHistoryRepository()
        self.comment_repo = TicketCommentRepository()

    async def create_ticket(self, user_id: uuid.UUID, data: TicketCreateRequest) -> Ticket:
        """Создать новую заявку."""
        ticket = await self.repo.create(
            db=self.db,
            user_id=user_id,
            title=data.title,
            description=data.description,
            latitude=data.latitude,
            longitude=data.longitude,
            address=data.address,
        )
        return ticket

    async def create_ticket_with_files(
        self,
        user_id: uuid.UUID,
        title: str,
        description: str,
        file_data_list: list[tuple[str, bytes, str]],  # (mime, contents, filename)
        latitude: float | None = None,
        longitude: float | None = None,
        address: str | None = None,
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
        )

        # Сохраняем файлы на диск и в БД
        upload_dir = Path(settings.UPLOAD_PATH) / str(ticket.id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        for mime_type, contents, original_name in file_data_list:
            unique_name = f"{uuid.uuid4()}_{original_name}"
            file_path = upload_dir / unique_name
            file_path.write_bytes(contents)

            relative_path = f"uploads/tickets/{ticket.id}/{unique_name}"
            await self.file_repo.create(
                self.db,
                ticket.id,
                relative_path,
                len(contents),
                mime_type,
            )

        # Обновляем объект, чтобы relations подгрузились
        await self.db.refresh(ticket, ["files"])

        return ticket

    async def get_ticket(self, ticket_id: uuid.UUID) -> Ticket | None:
        """Получить заявку по ID."""
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
    ) -> Ticket | None:
        """Изменить статус заявки с логированием в TicketHistory."""
        ticket = await self.repo.get_by_id_simple(self.db, ticket_id)
        if ticket is None:
            return None
        old_status = ticket.status.value if ticket.status else None
        if old_status == new_status.value:
            return ticket

        updated = await self.repo.update_status(self.db, ticket_id, new_status)
        if updated:
            await self.history_repo.create(
                self.db, ticket_id, changed_by, old_status, new_status.value,
            )
        return updated

    async def assign_ticket(self, ticket_id: uuid.UUID, admin_id: uuid.UUID) -> Ticket | None:
        """Назначить заявку администратору."""
        return await self.repo.assign(self.db, ticket_id, admin_id)

    async def add_comment(
        self,
        ticket_id: uuid.UUID,
        author_id: uuid.UUID,
        text: str,
    ) -> TicketComment | None:
        """Добавить комментарий к заявке."""
        ticket = await self.repo.get_by_id_simple(self.db, ticket_id)
        if ticket is None:
            return None
        return await self.comment_repo.create(self.db, ticket_id, author_id, text)

    async def add_file(
        self,
        ticket_id: uuid.UUID,
        file_path: str,
        file_size: int,
        mime_type: str,
    ) -> TicketFile | None:
        """Прикрепить файл к заявке."""
        ticket = await self.repo.get_by_id_simple(self.db, ticket_id)
        if ticket is None:
            return None
        return await self.file_repo.create(self.db, ticket_id, file_path, file_size, mime_type)

    async def get_file_count(self, ticket_id: uuid.UUID) -> int:
        """Количество файлов у заявки."""
        return await self.file_repo.count_by_ticket(self.db, ticket_id)
