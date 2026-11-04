"""
Аналитика по заявкам для админки.

Эндпоинт ``GET /api/v1/admin/analytics`` отдаёт периодные метрики:
поток заявок, сравнение с предыдущим периодом, накопительную очередь,
распределение по статусам и эффективность исполнителей.

Все агрегаты считаются на стороне БД; тяжёлые выборки ограничены периодом.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_role
from src.auth.models import User, UserRole
from src.database import get_db
from src.tickets.constants import OVERDUE_DAYS
from src.tickets.models import Ticket, TicketStatus
from src.tickets.service import STATUS_LABELS

analytics_router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Администрирование — аналитика"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)

# Статусы, которые считаются завершёнными.
RESOLVED_STATUSES = (TicketStatus.DONE, TicketStatus.CLOSED)
# Статусы, которые считаются «в работе» (ещё не завершены).
OPEN_STATUSES = (TicketStatus.NEW, TicketStatus.IN_WORK)

# Сколько исполнителей отдавать в аналитике. Список всегда ограничен,
# чтобы при тысячах администраторов ответ и интерфейс оставались компактными.
ASSIGNEE_LIMIT = 10

_STATUS_ORDER = (
    TicketStatus.NEW,
    TicketStatus.IN_WORK,
    TicketStatus.DONE,
    TicketStatus.CLOSED,
)


class AnalyticsSummary(BaseModel):
    """Ключевые показатели за период и сравнение с предыдущим."""

    created_in_period: int
    resolved_in_period: int
    resolved_from_period: int
    open_now: int
    overdue_now: int
    backlog_start: int
    backlog_end: int
    resolution_rate: float
    avg_resolution_hours: float | None
    median_resolution_hours: float | None
    created_prev_period: int
    resolved_prev_period: int
    avg_resolution_prev_hours: float | None
    created_delta_pct: float | None
    resolved_delta_pct: float | None
    avg_resolution_delta_pct: float | None


class DayPoint(BaseModel):
    """Точка дневного графика."""

    date: date
    created: int
    resolved: int
    backlog: int


class StatusPoint(BaseModel):
    """Распределение заявок, созданных за период, по текущему статусу."""

    status: str
    label: str
    count: int
    percent: float


class AssigneePoint(BaseModel):
    """Эффективность и текущая нагрузка администратора."""

    admin_id: uuid.UUID
    name: str
    created_in_period: int
    resolved_in_period: int
    open_now: int
    overdue: int
    avg_resolution_hours: float | None


class AnalyticsOut(BaseModel):
    """Ответ эндпоинта аналитики."""

    period_days: int
    generated_at: datetime
    summary: AnalyticsSummary
    by_day: list[DayPoint]
    by_status: list[StatusPoint]
    by_assignee: list[AssigneePoint]
    assignees_total: int


def _status_key(value: object) -> str:
    """Привести статус из БД (enum или строка) к строке."""
    if isinstance(value, TicketStatus):
        return value.value
    return str(value)


def _as_utc(value: datetime) -> datetime:
    """Гарантировать timezone-aware datetime (SQLite отдаёт naive)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _percent(part: int, whole: int) -> float:
    """Процент с защитой от деления на ноль."""
    if not whole:
        return 0.0
    return round(part / whole * 100, 1)


def _delta_pct(current: float, previous: float) -> float | None:
    """Изменение в процентах к предыдущему периоду."""
    if not previous:
        return None
    return round((current - previous) / previous * 100, 1)


def _duration_stats(
    rows: list[tuple[datetime, datetime]],
) -> tuple[float | None, float | None]:
    """Среднее и медианное время решения в часах."""
    if not rows:
        return None, None
    durations = sorted(
        max(0.0, (_as_utc(updated) - _as_utc(created)).total_seconds() / 3600)
        for created, updated in rows
    )
    average = round(sum(durations) / len(durations), 1)
    middle = len(durations) // 2
    median = (
        durations[middle]
        if len(durations) % 2
        else (durations[middle - 1] + durations[middle]) / 2
    )
    return average, round(median, 1)


async def _count(db: AsyncSession, *conditions) -> int:
    """Посчитать заявки по условиям."""
    query = select(func.count()).select_from(Ticket)
    if conditions:
        query = query.where(*conditions)
    return int(await db.scalar(query) or 0)


@analytics_router.get(
    "/analytics",
    response_model=AnalyticsOut,
    summary="Аналитика по заявкам",
    description="Периодные метрики: поток заявок, сравнение с предыдущим периодом, "
    "накопительная очередь, статусы и эффективность исполнителей.",
)
async def admin_analytics(
    days: int = Query(30, ge=1, le=365, description="Период в днях"),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOut:
    """Собрать аналитику по заявкам за период."""
    now = datetime.now(UTC)
    since = (now - timedelta(days=days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    prev_since = since - timedelta(days=days)
    overdue_cutoff = now - timedelta(days=OVERDUE_DAYS)

    # ---- Базовые счётчики ----
    created_in_period = await _count(db, Ticket.created_at >= since)
    resolved_in_period = await _count(
        db,
        Ticket.status.in_(RESOLVED_STATUSES),
        Ticket.updated_at >= since,
    )
    created_prev_period = await _count(
        db,
        Ticket.created_at >= prev_since,
        Ticket.created_at < since,
    )
    resolved_prev_period = await _count(
        db,
        Ticket.status.in_(RESOLVED_STATUSES),
        Ticket.updated_at >= prev_since,
        Ticket.updated_at < since,
    )
    open_now = await _count(db, Ticket.status.in_(OPEN_STATUSES))
    overdue_now = await _count(
        db,
        Ticket.status == TicketStatus.IN_WORK,
        Ticket.created_at < overdue_cutoff,
    )

    # Заявки, которые были открыты на начало периода.
    backlog_start = await _count(
        db,
        Ticket.created_at < since,
        or_(Ticket.status.in_(OPEN_STATUSES), Ticket.updated_at >= since),
    )

    # ---- Распределение по статусам (только созданные за период) ----
    status_rows = (
        await db.execute(
            select(Ticket.status, func.count())
            .where(Ticket.created_at >= since)
            .group_by(Ticket.status),
        )
    ).all()
    status_counts = {_status_key(status): int(count) for status, count in status_rows}
    by_status = [
        StatusPoint(
            status=status.value,
            label=STATUS_LABELS.get(status.value, status.value),
            count=status_counts.get(status.value, 0),
            percent=_percent(status_counts.get(status.value, 0), created_in_period),
        )
        for status in _STATUS_ORDER
    ]
    resolved_from_period = (
        status_counts.get(TicketStatus.DONE.value, 0)
        + status_counts.get(TicketStatus.CLOSED.value, 0)
    )

    # ---- Динамика по дням и накопительная очередь ----
    created_rows = (
        await db.execute(
            select(func.date(Ticket.created_at), func.count())
            .where(Ticket.created_at >= since)
            .group_by(func.date(Ticket.created_at)),
        )
    ).all()
    resolved_rows = (
        await db.execute(
            select(func.date(Ticket.updated_at), func.count())
            .where(
                Ticket.status.in_(RESOLVED_STATUSES),
                Ticket.updated_at >= since,
            )
            .group_by(func.date(Ticket.updated_at)),
        )
    ).all()

    created_by_day = {str(day): int(count) for day, count in created_rows}
    resolved_by_day = {str(day): int(count) for day, count in resolved_rows}

    by_day: list[DayPoint] = []
    backlog = backlog_start
    first_day = since.date()
    for offset in range(days):
        current = first_day + timedelta(days=offset)
        key = current.isoformat()
        created = created_by_day.get(key, 0)
        resolved = resolved_by_day.get(key, 0)
        backlog += created - resolved
        by_day.append(
            DayPoint(
                date=current,
                created=created,
                resolved=resolved,
                backlog=backlog,
            ),
        )

    # ---- Время решения ----
    resolution_rows = (
        await db.execute(
            select(Ticket.created_at, Ticket.updated_at).where(
                Ticket.status.in_(RESOLVED_STATUSES),
                Ticket.updated_at >= since,
            ),
        )
    ).all()
    avg_hours, median_hours = _duration_stats(
        [(created, updated) for created, updated in resolution_rows],
    )

    prev_resolution_rows = (
        await db.execute(
            select(Ticket.created_at, Ticket.updated_at).where(
                Ticket.status.in_(RESOLVED_STATUSES),
                Ticket.updated_at >= prev_since,
                Ticket.updated_at < since,
            ),
        )
    ).all()
    avg_prev_hours, _ = _duration_stats(
        [(created, updated) for created, updated in prev_resolution_rows],
    )

    # ---- Эффективность исполнителей ----
    assignee_rows = (
        await db.execute(
            select(
                User.id,
                User.name,
                func.sum(
                    case((Ticket.created_at >= since, 1), else_=0),
                ).label("created_in_period"),
                func.sum(
                    case(
                        (
                            Ticket.status.in_(RESOLVED_STATUSES)
                            & (Ticket.updated_at >= since),
                            1,
                        ),
                        else_=0,
                    ),
                ).label("resolved_in_period"),
                func.sum(
                    case((Ticket.status.in_(OPEN_STATUSES), 1), else_=0),
                ).label("open_now"),
                func.sum(
                    case(
                        (
                            (Ticket.status == TicketStatus.IN_WORK)
                            & (Ticket.created_at < overdue_cutoff),
                            1,
                        ),
                        else_=0,
                    ),
                ).label("overdue"),
            )
            .select_from(Ticket)
            .join(User, Ticket.assigned_to == User.id)
            .group_by(User.id, User.name),
        )
    ).all()

    by_assignee: list[AssigneePoint] = []
    for admin_id, name, in_period, resolved, open_count, overdue in assignee_rows:
        # Не показываем админов, у которых нет активности и текущей нагрузки.
        if not (in_period or resolved or open_count or overdue):
            continue
        by_assignee.append(
            AssigneePoint(
                admin_id=admin_id,
                name=str(name),
                created_in_period=int(in_period or 0),
                resolved_in_period=int(resolved or 0),
                open_now=int(open_count or 0),
                overdue=int(overdue or 0),
                avg_resolution_hours=None,
            ),
        )
    by_assignee.sort(
        key=lambda item: (
            item.resolved_in_period,
            item.created_in_period,
            item.open_now,
        ),
        reverse=True,
    )
    assignees_total = len(by_assignee)
    by_assignee = by_assignee[:ASSIGNEE_LIMIT]

    # Среднее время решения считаем только для показанных исполнителей,
    # чтобы не выгружать все решённые заявки при большом штате.
    if by_assignee:
        duration_rows = (
            await db.execute(
                select(
                    Ticket.assigned_to,
                    Ticket.created_at,
                    Ticket.updated_at,
                ).where(
                    Ticket.assigned_to.in_([item.admin_id for item in by_assignee]),
                    Ticket.status.in_(RESOLVED_STATUSES),
                    Ticket.updated_at >= since,
                ),
            )
        ).all()
        durations_by_admin: dict[uuid.UUID, list[tuple[datetime, datetime]]] = {}
        for admin_id, created, updated in duration_rows:
            if admin_id is not None:
                durations_by_admin.setdefault(admin_id, []).append(
                    (created, updated),
                )
        for item in by_assignee:
            assignee_avg, _ = _duration_stats(
                durations_by_admin.get(item.admin_id, []),
            )
            item.avg_resolution_hours = assignee_avg

    return AnalyticsOut(
        period_days=days,
        generated_at=now,
        summary=AnalyticsSummary(
            created_in_period=created_in_period,
            resolved_in_period=resolved_in_period,
            resolved_from_period=resolved_from_period,
            open_now=open_now,
            overdue_now=overdue_now,
            backlog_start=backlog_start,
            backlog_end=backlog,
            resolution_rate=_percent(resolved_from_period, created_in_period),
            avg_resolution_hours=avg_hours,
            median_resolution_hours=median_hours,
            created_prev_period=created_prev_period,
            resolved_prev_period=resolved_prev_period,
            avg_resolution_prev_hours=avg_prev_hours,
            created_delta_pct=_delta_pct(created_in_period, created_prev_period),
            resolved_delta_pct=_delta_pct(resolved_in_period, resolved_prev_period),
            avg_resolution_delta_pct=(
                _delta_pct(avg_hours, avg_prev_hours)
                if avg_hours is not None and avg_prev_hours is not None
                else None
            ),
        ),
        by_day=by_day,
        by_status=by_status,
        by_assignee=by_assignee,
        assignees_total=assignees_total,
    )
