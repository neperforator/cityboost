"""
Репозиторий для работы с заявками (Ticket) и связанными сущностями.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from src.auth.models import User
from src.tickets.models import Ticket, TicketComment, TicketFile, TicketHistory, TicketStatus


class TicketRepository:
    """Репозиторий CRUD-операций для заявок."""

    @staticmethod
    async def get_by_id(db: AsyncSession, ticket_id: uuid.UUID) -> Ticket | None:
        """Получить заявку по ID с загрузкой связей."""
        result = await db.execute(
            select(Ticket)
            .options(
                selectinload(Ticket.user),
                selectinload(Ticket.assignee),
                selectinload(Ticket.files),
                selectinload(Ticket.comments).selectinload(TicketComment.author),
                selectinload(Ticket.history).selectinload(TicketHistory.changed_by_user),
            )
            .where(Ticket.id == ticket_id),
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id_simple(db: AsyncSession, ticket_id: uuid.UUID) -> Ticket | None:
        """Получить заявку по ID без загрузки связей."""
        return await db.get(Ticket, ticket_id)

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: uuid.UUID,
        title: str,
        description: str,
        latitude: float | None = None,
        longitude: float | None = None,
        address: str | None = None,
    ) -> Ticket:
        """Создать новую заявку."""
        ticket = Ticket(
            user_id=user_id,
            title=title,
            description=description,
            latitude=latitude,
            longitude=longitude,
            address=address,
        )
        db.add(ticket)
        await db.flush()
        await db.refresh(ticket)
        return ticket

    @staticmethod
    async def update_status(
        db: AsyncSession,
        ticket_id: uuid.UUID,
        new_status: TicketStatus,
        close_reason: str | None = None,
    ) -> Ticket | None:
        """Обновить статус заявки."""
        ticket = await TicketRepository.get_by_id_simple(db, ticket_id)
        if ticket is None:
            return None
        ticket.status = new_status
        if new_status == TicketStatus.CLOSED:
            ticket.close_reason = close_reason
        else:
            ticket.close_reason = None
        await db.flush()
        # Перезагружаем со связями, чтобы не было MissingGreenlet при сериализации
        return await TicketRepository.get_by_id(db, ticket_id)

    @staticmethod
    async def assign(
        db: AsyncSession, ticket_id: uuid.UUID, admin_id: uuid.UUID,
    ) -> Ticket | None:
        """Назначить заявку на администратора."""
        ticket = await TicketRepository.get_by_id_simple(db, ticket_id)
        if ticket is None:
            return None
        ticket.assigned_to = admin_id
        if ticket.status == TicketStatus.NEW:
            ticket.status = TicketStatus.IN_WORK
        await db.flush()
        # Перезагружаем со связями, чтобы не было MissingGreenlet при сериализации
        return await TicketRepository.get_by_id(db, ticket_id)

    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: TicketStatus | None = None,
    ) -> tuple[list[Ticket], int]:
        """Получить заявки пользователя с пагинацией и опциональным фильтром по статусу."""
        query = (
            select(Ticket)
            .options(
                selectinload(Ticket.user),
                selectinload(Ticket.assignee),
            )
            .where(Ticket.user_id == user_id)
            .order_by(Ticket.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_query = select(func.count()).select_from(Ticket).where(Ticket.user_id == user_id)

        if status is not None:
            query = query.where(Ticket.status == status)
            count_query = count_query.where(Ticket.status == status)

        result = await db.execute(query)
        items = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return items, total

    @staticmethod
    async def list_by_status_and_date(
        db: AsyncSession,
        status: TicketStatus | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        assignee_id: uuid.UUID | None = None,
        unassigned_only: bool = False,
        overdue_before: datetime | None = None,
    ) -> tuple[list[Ticket], int]:
        """Фильтрация заявок по статусу, дате, поиску, исполнителю (для админа)."""
        query = select(Ticket).options(
            selectinload(Ticket.user),
            selectinload(Ticket.assignee),
        ).order_by(Ticket.created_at.desc())

        count_query = select(func.count()).select_from(Ticket)

        # Поиск по всем текстовым полям заявки, заявителю и исполнителю.
        term = search.strip() if search else ""
        if term:
            pattern = f"%{term}%"
            assignee = aliased(User)
            query = (
                query
                .join(User, Ticket.user_id == User.id)
                .outerjoin(assignee, Ticket.assigned_to == assignee.id)
            )
            count_query = (
                count_query
                .join(User, Ticket.user_id == User.id)
                .outerjoin(assignee, Ticket.assigned_to == assignee.id)
            )
            search_filter = or_(
                Ticket.title.ilike(pattern),
                Ticket.description.ilike(pattern),
                Ticket.address.ilike(pattern),
                Ticket.close_reason.ilike(pattern),
                cast(Ticket.id, Text).ilike(pattern),
                User.name.ilike(pattern),
                User.email.ilike(pattern),
                assignee.name.ilike(pattern),
                assignee.email.ilike(pattern),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if status is not None:
            query = query.where(Ticket.status == status)
            count_query = count_query.where(Ticket.status == status)
        if assignee_id is not None:
            query = query.where(Ticket.assigned_to == assignee_id)
            count_query = count_query.where(Ticket.assigned_to == assignee_id)
        if unassigned_only:
            query = query.where(Ticket.assigned_to.is_(None))
            count_query = count_query.where(Ticket.assigned_to.is_(None))
        if overdue_before is not None:
            query = query.where(
                Ticket.status == TicketStatus.IN_WORK,
                Ticket.created_at < overdue_before,
            )
            count_query = count_query.where(
                Ticket.status == TicketStatus.IN_WORK,
                Ticket.created_at < overdue_before,
            )
        if date_from is not None:
            query = query.where(Ticket.created_at >= date_from)
            count_query = count_query.where(Ticket.created_at >= date_from)
        if date_to is not None:
            query = query.where(Ticket.created_at <= date_to)
            count_query = count_query.where(Ticket.created_at <= date_to)

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return items, total


    @staticmethod
    async def get_status_counts(
        db: AsyncSession,
        user_id: uuid.UUID | None = None,
    ) -> dict[str, int]:
        """Получить количество заявок по каждому статусу."""
        query = select(Ticket.status, func.count()).select_from(Ticket).group_by(Ticket.status)
        if user_id is not None:
            query = query.where(Ticket.user_id == user_id)

        result = await db.execute(query)
        rows = result.all()

        counts: dict[str, int] = {s.value: 0 for s in TicketStatus}
        for status_val, cnt in rows:
            if status_val is not None:
                counts[status_val.value] = cnt
        counts["total"] = sum(counts.values())
        return counts


class TicketFileRepository:
    """Репозиторий для файлов заявок."""

    @staticmethod
    async def count_by_ticket(db: AsyncSession, ticket_id: uuid.UUID) -> int:
        """Количество файлов у заявки."""
        result = await db.execute(
            select(func.count()).select_from(TicketFile).where(TicketFile.ticket_id == ticket_id),
        )
        return result.scalar() or 0

    @staticmethod
    async def create(
        db: AsyncSession,
        ticket_id: uuid.UUID,
        file_path: str,
        file_size: int,
        mime_type: str,
    ) -> TicketFile:
        """Создать запись о файле."""
        tf = TicketFile(
            ticket_id=ticket_id,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
        )
        db.add(tf)
        await db.flush()
        await db.refresh(tf)
        return tf


class TicketHistoryRepository:
    """Репозиторий для истории изменений заявки."""

    @staticmethod
    async def create(
        db: AsyncSession,
        ticket_id: uuid.UUID,
        changed_by: uuid.UUID,
        action: str,
        old_status: str | None,
        new_status: str,
        details: str | None = None,
    ) -> TicketHistory:
        """Создать запись в истории."""
        entry = TicketHistory(
            ticket_id=ticket_id,
            changed_by=changed_by,
            action=action,
            old_status=old_status,
            new_status=new_status,
            details=details,
        )
        db.add(entry)
        await db.flush()
        await db.refresh(entry)
        return entry


class TicketCommentRepository:
    """Репозиторий для комментариев."""

    @staticmethod
    async def create(
        db: AsyncSession,
        ticket_id: uuid.UUID,
        author_id: uuid.UUID,
        comment_text: str,
    ) -> TicketComment:
        """Создать комментарий."""
        comment = TicketComment(
            ticket_id=ticket_id,
            author_id=author_id,
            comment_text=comment_text,
        )
        db.add(comment)
        await db.flush()
        await db.refresh(comment)
        return comment
