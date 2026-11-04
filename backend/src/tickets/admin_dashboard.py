"""
Личный кабинет администратора: персональная статистика и сводка.

Эндпоинт собирает данные для страницы /admin одним запросом.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.dependencies import get_current_user, require_role
from src.auth.models import User, UserRole
from src.common.audit import AdminLogRepository
from src.database import get_db
from src.tickets.constants import OVERDUE_DAYS
from src.tickets.models import Ticket, TicketStatus
from src.tickets.schemas import TicketOutShort

admin_dashboard_router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Администрирование — кабинет"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)

# Сколько последних заявок/действий показывать в кабинете.
ASSIGNED_LIMIT = 20
QUEUE_LIMIT = 10
ACTIVITY_LIMIT = 8


class AssignedStats(BaseModel):
    """Статистика заявок, назначенных на текущего администратора."""

    total: int
    new: int
    in_work: int
    done: int
    closed: int


class ActivityOut(BaseModel):
    """Последнее действие администратора из аудит-лога."""

    id: uuid.UUID
    action: str
    target_type: str
    target_id: uuid.UUID | None = None
    target_name: str | None = None
    details: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminDashboardOut(BaseModel):
    """Сводка личного кабинета администратора."""

    assigned: AssignedStats
    queue: int
    overdue: int
    recent_assigned: list[TicketOutShort]
    queue_tickets: list[TicketOutShort]
    recent_activity: list[ActivityOut]


@admin_dashboard_router.get(
    "/dashboard",
    response_model=AdminDashboardOut,
    summary="Кабинет администратора",
    description="Персональная статистика, назначенные заявки, очередь и последняя активность.",
)
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> AdminDashboardOut:
    """Собрать сводку для личного кабинета администратора."""
    # Заявки, назначенные на меня, по статусам.
    rows = (
        await db.execute(
            select(Ticket.status, func.count())
            .where(Ticket.assigned_to == admin.id)
            .group_by(Ticket.status)
        )
    ).all()
    counts = {status: 0 for status in TicketStatus}
    for ticket_status, count in rows:
        if ticket_status is not None:
            counts[ticket_status] = count

    assigned = AssignedStats(
        total=sum(counts.values()),
        new=counts[TicketStatus.NEW],
        in_work=counts[TicketStatus.IN_WORK],
        done=counts[TicketStatus.DONE],
        closed=counts[TicketStatus.CLOSED],
    )

    # Новые заявки без исполнителя.
    queue = (
        await db.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(
                Ticket.status == TicketStatus.NEW,
                Ticket.assigned_to.is_(None),
            )
        )
    ) or 0

    # Просроченные: в работе на мне дольше OVERDUE_DAYS.
    overdue_cutoff = datetime.now(UTC) - timedelta(days=OVERDUE_DAYS)
    overdue = (
        await db.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(
                Ticket.assigned_to == admin.id,
                Ticket.status == TicketStatus.IN_WORK,
                Ticket.created_at < overdue_cutoff,
            )
        )
    ) or 0

    ticket_options = (
        selectinload(Ticket.user),
        selectinload(Ticket.assignee),
    )

    recent_assigned = list(
        (
            await db.execute(
                select(Ticket)
                .options(*ticket_options)
                .where(Ticket.assigned_to == admin.id)
                .order_by(Ticket.created_at.desc())
                .limit(ASSIGNED_LIMIT)
            )
        ).scalars().all()
    )

    # Очередь: сначала самые старые, чтобы не копились.
    queue_tickets = list(
        (
            await db.execute(
                select(Ticket)
                .options(*ticket_options)
                .where(
                    Ticket.status == TicketStatus.NEW,
                    Ticket.assigned_to.is_(None),
                )
                .order_by(Ticket.created_at.asc())
                .limit(QUEUE_LIMIT)
            )
        ).scalars().all()
    )

    activity_items, _ = await AdminLogRepository.list(
        db, page=1, page_size=ACTIVITY_LIMIT, admin_id=admin.id,
    )

    return AdminDashboardOut(
        assigned=assigned,
        queue=queue,
        overdue=overdue,
        recent_assigned=recent_assigned,
        queue_tickets=queue_tickets,
        recent_activity=activity_items,
    )
