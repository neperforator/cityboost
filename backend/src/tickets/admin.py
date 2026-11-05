"""
Admin API-роуты для управления заявками.

Все эндпоинты защищены require_role('admin').
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_role
from src.auth.models import User, UserRole
from src.common.audit import log_admin_action
from src.database import get_db
from src.tickets.constants import OVERDUE_DAYS
from src.tickets.models import TicketStatus
from src.tickets.schemas import (
    PaginatedTickets,
    TicketCommentCreate,
    TicketCommentOut,
    TicketHistoryOut,
    TicketMapOut,
    TicketMapPoint,
    TicketOut,
    TicketOutDetail,
    TicketStats,
    TicketStatusChangeRequest,
)
from src.tickets.service import TicketService, _status_label

admin_router = APIRouter(
    prefix="/api/v1/admin/tickets",
    tags=["Администрирование заявок"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


@admin_router.get(
    "",
    response_model=PaginatedTickets,
    summary="Список всех заявок (админ)",
    description="Фильтрация по статусу, диапазону дат и поиск по заявителю, названию, описанию, адресу и ID. Пагинация.",
)
async def admin_list_tickets(
    status: TicketStatus | None = Query(None, description="Фильтр по статусу"),
    date_from: datetime | None = Query(None, description="Начальная дата (ISO 8601)"),
    date_to: datetime | None = Query(None, description="Конечная дата (ISO 8601)"),
    q: str | None = Query(
        None,
        min_length=1,
        max_length=200,
        description="Поиск: заявитель, название, описание, адрес, ID заявки",
    ),
    assignee: Literal["me", "unassigned", "all"] | None = Query(
        None,
        description="Фильтр по исполнителю: me — на мне, unassigned — без исполнителя",
    ),
    overdue: bool = Query(
        False,
        description=f"Только просроченные заявки в работе (старше {OVERDUE_DAYS} дней)",
    ),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> PaginatedTickets:
    """Получить список всех заявок с фильтрацией, поиском и пагинацией."""
    service = TicketService(db)
    overdue_before = (
        datetime.now(UTC) - timedelta(days=OVERDUE_DAYS)
        if overdue
        else None
    )
    items, total = await service.repo.list_by_status_and_date(
        db,
        status,
        date_from,
        date_to,
        page,
        page_size,
        q,
        assignee_id=admin.id if assignee == "me" else None,
        unassigned_only=assignee == "unassigned",
        overdue_before=overdue_before,
    )
    return PaginatedTickets(items=items, total=total, page=page, page_size=page_size)


@admin_router.get(
    "/stats",
    response_model=TicketStats,
    summary="Статистика всех заявок",
    description="Количество заявок по статусам (глобально).",
)
async def admin_ticket_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_user),
) -> TicketStats:
    """Получить глобальную статистику заявок."""
    service = TicketService(db)
    counts = await service.repo.get_status_counts(db)
    return TicketStats(
        total=counts.get("total", 0),
        new=counts.get("NEW", 0),
        in_work=counts.get("IN_WORK", 0),
        done=counts.get("DONE", 0),
        closed=counts.get("CLOSED", 0),
    )


@admin_router.get(
    "/map",
    response_model=TicketMapOut,
    summary="Точки заявок для карты (админ)",
    description="Лёгкий список заявок с координатами. Поддерживает те же фильтры, "
    "что и список заявок, плюс ограничение количества точек.",
)
async def admin_tickets_map(
    status: TicketStatus | None = Query(None, description="Фильтр по статусу"),
    days: int | None = Query(
        None,
        ge=1,
        le=3650,
        description="Только заявки за последние N дней (по умолчанию все)",
    ),
    q: str | None = Query(
        None,
        max_length=255,
        description="Поиск по названию, описанию, адресу, заявителю, исполнителю",
    ),
    assignee: Literal["me", "unassigned"] | None = Query(
        None,
        description="Фильтр по исполнителю: me — на мне, unassigned — без исполнителя",
    ),
    overdue: bool = Query(
        False,
        description=f"Только просроченные заявки в работе (старше {OVERDUE_DAYS} дней)",
    ),
    limit: int = Query(
        1000,
        ge=1,
        le=2000,
        description="Максимум точек на карте",
    ),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> TicketMapOut:
    """Получить точки заявок с координатами для админской карты."""
    service = TicketService(db)
    date_from = (
        datetime.now(UTC) - timedelta(days=days)
        if days is not None
        else None
    )
    overdue_before = (
        datetime.now(UTC) - timedelta(days=OVERDUE_DAYS)
        if overdue
        else None
    )
    rows, total = await service.repo.list_map_points(
        db,
        status=status,
        date_from=date_from,
        limit=limit,
        search=q,
        assignee_id=admin.id if assignee == "me" else None,
        unassigned_only=assignee == "unassigned",
        overdue_before=overdue_before,
    )
    items = [
        TicketMapPoint(
            id=row.id,
            title=row.title,
            status=row.status,
            latitude=row.latitude,
            longitude=row.longitude,
            address=row.address,
            assigned_to_name=row.assignee_name,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return TicketMapOut(items=items, total=total, limit=limit)


@admin_router.get(
    "/{ticket_id}",
    response_model=TicketOutDetail,
    summary="Детали заявки (админ)",
    description="Полная информация о заявке с историей изменений, файлами и комментариями.",
)
async def admin_get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_user),
) -> TicketOutDetail:
    """Получить детальную информацию о заявке."""
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    return TicketOutDetail(
        id=ticket.id,
        user_id=ticket.user_id,
        assigned_to=ticket.assigned_to,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        latitude=ticket.latitude,
        longitude=ticket.longitude,
        address=ticket.address,
        user_name=ticket.user.name if ticket.user else "",
        assigned_to_name=ticket.assignee.name if ticket.assignee else None,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        files=ticket.files,
        comments=ticket.comments,
    )


@admin_router.patch(
    "/{ticket_id}/status",
    response_model=TicketOut,
    summary="Изменить статус заявки",
    description="Меняет статус заявки и автоматически логирует изменение в TicketHistory. "
    "При статусе CLOSED требуется указать причину закрытия (close_reason).",
)
async def admin_change_status(
    ticket_id: uuid.UUID,
    data: TicketStatusChangeRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> TicketOut:
    """Изменить статус заявки с логированием."""
    service = TicketService(db)
    try:
        ticket = await service.change_status(
            ticket_id, data.new_status, admin.id, close_reason=data.close_reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    # Аудит
    details = f"Статус заявки «{ticket.title}» изменён на {_status_label(data.new_status.value)}"
    if data.new_status == TicketStatus.CLOSED:
        details += f". Причина: {ticket.close_reason}"
    await log_admin_action(
        db, admin.id, "change_ticket_status", "ticket", ticket_id,
        ticket.title, details,
    )

    return ticket


@admin_router.patch(
    "/{ticket_id}/assign",
    response_model=TicketOut,
    summary="Назначить заявку администратору",
    description="Назначает ответственного администратора и переводит статус в IN_WORK.",
)
async def admin_assign_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> TicketOut:
    """Назначить заявку на текущего администратора."""
    service = TicketService(db)
    ticket = await service.assign_ticket(ticket_id, admin.id, admin.name)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    # Аудит
    await log_admin_action(
        db, admin.id, "assign_ticket", "ticket", ticket_id,
        ticket.title,
        f"Заявка «{ticket.title}» назначена на администратора {admin.name}",
    )

    return ticket


@admin_router.post(
    "/{ticket_id}/comments",
    response_model=TicketCommentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить комментарий (админ)",
    description="Добавить внутренний комментарий к заявке от имени администратора.",
)
async def admin_add_comment(
    ticket_id: uuid.UUID,
    data: TicketCommentCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> TicketCommentOut:
    """Добавить комментарий к заявке."""
    service = TicketService(db)
    try:
        comment = await service.add_comment(ticket_id, admin.id, data.comment_text)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
    return TicketCommentOut(
        id=comment.id,
        ticket_id=comment.ticket_id,
        author_id=comment.author_id,
        author_name=admin.name,
        author_role=admin.role.value,
        comment_text=comment.comment_text,
        created_at=comment.created_at,
    )


@admin_router.get(
    "/{ticket_id}/history",
    response_model=list[TicketHistoryOut],
    summary="История изменений заявки",
    description="Получить историю изменения статусов заявки.",
)
async def admin_get_history(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_user),
) -> list[TicketHistoryOut]:
    """Получить историю изменений статуса заявки."""
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
    return ticket.history
