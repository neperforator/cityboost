"""
Admin API-роуты для управления заявками.

Все эндпоинты защищены require_role('admin').
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_role
from src.auth.models import User, UserRole
from src.common.audit import log_admin_action
from src.database import get_db
from src.tickets.models import TicketStatus
from src.tickets.schemas import (
    PaginatedTickets,
    TicketCommentCreate,
    TicketCommentOut,
    TicketHistoryOut,
    TicketOut,
    TicketOutDetail,
    TicketStats,
)
from src.tickets.service import TicketService

admin_router = APIRouter(
    prefix="/api/v1/admin/tickets",
    tags=["Администрирование заявок"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


@admin_router.get(
    "",
    response_model=PaginatedTickets,
    summary="Список всех заявок (админ)",
    description="Фильтрация по статусу и диапазону дат. Пагинация.",
)
async def admin_list_tickets(
    status: TicketStatus | None = Query(None, description="Фильтр по статусу"),
    date_from: str | None = Query(None, description="Начальная дата (ISO 8601)"),
    date_to: str | None = Query(None, description="Конечная дата (ISO 8601)"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_user),
) -> PaginatedTickets:
    """Получить список всех заявок с фильтрацией и пагинацией."""
    service = TicketService(db)
    items, total = await service.repo.list_by_status_and_date(
        db, status, date_from, date_to, page, page_size,
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
    description="Меняет статус заявки и автоматически логирует изменение в TicketHistory.",
)
async def admin_change_status(
    ticket_id: uuid.UUID,
    new_status: TicketStatus = Query(..., description="Новый статус"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> TicketOut:
    """Изменить статус заявки с логированием."""
    service = TicketService(db)
    ticket = await service.change_status(ticket_id, new_status, admin.id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    # Аудит
    await log_admin_action(
        db, admin.id, "change_ticket_status", "ticket", ticket_id,
        f"Статус изменён на {new_status.value}",
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
    ticket = await service.assign_ticket(ticket_id, admin.id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    # Аудит
    await log_admin_action(
        db, admin.id, "assign_ticket", "ticket", ticket_id,
        f"Заявка назначена на администратора {admin.name}",
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
    comment = await service.add_comment(ticket_id, admin.id, data.comment_text)
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
