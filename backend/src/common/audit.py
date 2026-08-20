"""
Аудит-лог действий администраторов.

Модель, репозиторий и вспомогательные функции для логирования
действий админов (бан, смена роли, изменение статуса заявки и т.д.).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from src.database import Base


class AdminActionLog(Base):
    """Запись аудит-лога действий администратора."""

    __tablename__ = "admin_action_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True,
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
    )
    target_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    target_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    target_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True,
    )

    # Связи (без FK constraints — колонки созданы без них)
    admin = relationship(
        "User",
        foreign_keys="AdminActionLog.admin_id",
        primaryjoin="AdminActionLog.admin_id == User.id",
    )
    target_user = relationship(
        "User",
        foreign_keys="AdminActionLog.target_id",
        primaryjoin="AdminActionLog.target_id == User.id",
    )

    def __repr__(self) -> str:
        return f"<AdminActionLog {self.admin_id} {self.action}>"


class AdminLogRepository:
    """Репозиторий для аудит-лога."""

    @staticmethod
    async def create(
        db: AsyncSession,
        admin_id: uuid.UUID,
        action: str,
        target_type: str,
        target_id: uuid.UUID | None = None,
        target_name: str | None = None,
        details: str | None = None,
    ) -> AdminActionLog:
        """Создать запись в аудит-логе."""
        entry = AdminActionLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            details=details,
        )
        db.add(entry)
        await db.flush()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        action: str | None = None,
        admin_id: uuid.UUID | None = None,
        target_type: str | None = None,
    ) -> tuple[list[AdminActionLog], int]:
        """Получить пагинированный список записей аудит-лога с фильтрацией."""
        query = select(AdminActionLog).options(
            selectinload(AdminActionLog.admin),
            selectinload(AdminActionLog.target_user),
        ).order_by(AdminActionLog.created_at.desc())
        count_query = select(func.count()).select_from(AdminActionLog)

        if action:
            query = query.where(AdminActionLog.action == action)
            count_query = count_query.where(AdminActionLog.action == action)
        if admin_id:
            query = query.where(AdminActionLog.admin_id == admin_id)
            count_query = count_query.where(AdminActionLog.admin_id == admin_id)
        if target_type:
            query = query.where(AdminActionLog.target_type == target_type)
            count_query = count_query.where(AdminActionLog.target_type == target_type)

        # Пагинация
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return items, total


async def log_admin_action(
    db: AsyncSession,
    admin_id: uuid.UUID,
    action: str,
    target_type: str,
    target_id: uuid.UUID | None = None,
    target_name: str | None = None,
    details: str | None = None,
) -> AdminActionLog:
    """
    Вспомогательная функция для быстрого логирования действий админов.

    Использование:
        await log_admin_action(db, admin.id, "ban", "user", user_id, user.name, "Причина: ...")
    """
    return await AdminLogRepository.create(
        db, admin_id, action, target_type, target_id, target_name, details,
    )
