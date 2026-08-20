"""
Admin API-роуты для просмотра аудит-лога.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_role
from src.auth.models import User, UserRole
from src.common.audit import AdminLogRepository
from src.database import get_db

admin_audit_router = APIRouter(
    prefix="/api/v1/admin/audit-logs",
    tags=["Администрирование — аудит"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


class AuditLogOut(BaseModel):
    """Запись аудит-лога (ответ API)."""
    id: uuid.UUID
    admin_id: uuid.UUID
    admin_name: str = ""
    action: str
    target_type: str
    target_id: uuid.UUID | None
    target_name: str | None = None
    details: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def populate_admin_name(cls, data):
        """Извлекаем имя администратора и цели из связанных ORM объектов."""
        if not isinstance(data, dict):
            admin = getattr(data, 'admin', None)
            return {
                "id": data.id,
                "admin_id": data.admin_id,
                "action": data.action,
                "target_type": data.target_type,
                "target_id": data.target_id,
                "target_name": data.target_name,
                "details": data.details,
                "created_at": data.created_at,
                "admin_name": admin.name if admin else "",
            }
        return data


class PaginatedAuditLogs(BaseModel):
    """Пагинированный список записей аудит-лога."""
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int


@admin_audit_router.get(
    "",
    response_model=PaginatedAuditLogs,
    summary="Аудит-лог действий админов",
    description="Пагинированный список действий администраторов с фильтрацией.",
)
async def list_audit_logs(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=100, description="Размер страницы"),
    action: str | None = Query(None, description="Фильтр по типу действия"),
    admin_id: uuid.UUID | None = Query(None, description="Фильтр по администратору"),
    target_type: str | None = Query(None, description="Фильтр по типу цели (user/ticket)"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_user),
) -> PaginatedAuditLogs:
    """Получить список записей аудит-лога."""
    items, total = await AdminLogRepository.list(
        db, page, page_size, action, admin_id, target_type,
    )
    return PaginatedAuditLogs(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
