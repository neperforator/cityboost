"""
Admin API-роуты для управления пользователями.
Все эндпоинты защищены require_role('admin').
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_role
from src.auth.models import User, UserRole
from src.auth.repository import UserRepository
from src.auth.schemas import PaginatedUsers, UserOut
from src.auth.service import AuthService
from src.common.audit import log_admin_action
from src.database import get_db

admin_user_router = APIRouter(
    prefix="/api/v1/admin/users",
    tags=["Администрирование пользователей"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


@admin_user_router.get(
    "",
    response_model=PaginatedUsers,
    summary="Список пользователей (пагинированный)",
    description="Возвращает пользователей с пагинацией и поиском.",
)
async def admin_list_users(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=1000, description="Размер страницы"),
    search: str | None = Query(None, description="Поиск по имени или email"),
    is_banned: bool | None = Query(None, description="Фильтр по блокировке"),
    role: str | None = Query(None, description="Фильтр по роли (user/admin)"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_user),
) -> PaginatedUsers:
    """Получить список пользователей (пагинированный, с фильтрацией)."""
    items, total = await UserRepository.paginated_list(
        db, page, page_size, search, is_banned, role,
    )
    return PaginatedUsers(items=items, total=total, page=page, page_size=page_size)


@admin_user_router.get(
    "/stats",
    summary="Статистика пользователей",
    description="Возвращает общее количество пользователей, админов, обычных пользователей и заблокированных.",
)
async def admin_users_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_user),
) -> dict:
    """Статистика пользователей для карточек фильтров."""
    return await UserRepository.get_stats(db)


@admin_user_router.patch(
    "/{user_id}/role",
    response_model=UserOut,
    summary="Изменить роль пользователя",
    description="Меняет роль пользователя (user → admin или admin → user).",
)
async def admin_change_user_role(
    user_id: uuid.UUID,
    new_role: UserRole,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> User:
    """Изменить роль пользователя."""
    # Нельзя снять админа с самого себя
    if user_id == admin.id and new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя снять права администратора с самого себя",
        )

    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    user.role = new_role
    await db.flush()
    await db.refresh(user)

    # Аудит
    await log_admin_action(
        db, admin.id, "change_role", "user", user_id,
        f"Роль изменена на {new_role.value}",
    )

    return user


@admin_user_router.patch(
    "/{user_id}/ban",
    response_model=UserOut,
    summary="Заблокировать пользователя",
    description="Блокирует пользователя — он не сможет войти в систему.",
)
async def admin_ban_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> User:
    """Заблокировать пользователя."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя заблокировать самого себя",
        )

    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже заблокирован",
        )

    user.is_banned = True
    await db.flush()
    await db.refresh(user)

    # Аудит
    await log_admin_action(db, admin.id, "ban", "user", user_id, f"Заблокирован пользователь {user.name}")

    return user


@admin_user_router.patch(
    "/{user_id}/unban",
    response_model=UserOut,
    summary="Разблокировать пользователя",
    description="Снимает блокировку с пользователя.",
)
async def admin_unban_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
) -> User:
    """Разблокировать пользователя."""
    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    if not user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не заблокирован",
        )

    user.is_banned = False
    await db.flush()
    await db.refresh(user)

    # Аудит
    await log_admin_action(db, admin.id, "unban", "user", user_id, f"Разблокирован пользователь {user.name}")

    return user
