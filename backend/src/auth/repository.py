"""
Репозиторий для работы с пользователями (CRUD).
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User


class UserRepository:
    """Репозиторий операций над пользователями."""

    @staticmethod
    async def get_stats(db: AsyncSession) -> dict[str, int]:
        """Получить статистику пользователей (общее, админы, забаненные)."""
        total_q = await db.execute(select(func.count()).select_from(User))
        total = total_q.scalar() or 0

        admins_q = await db.execute(
            select(func.count()).select_from(User).where(User.role == "ADMIN")
        )
        admins = admins_q.scalar() or 0

        users_q = await db.execute(
            select(func.count()).select_from(User).where(User.role == "USER")
        )
        users_count = users_q.scalar() or 0

        banned_q = await db.execute(
            select(func.count()).select_from(User).where(User.is_banned.is_(True))
        )
        banned = banned_q.scalar() or 0

        return {"total": total, "admins": admins, "users": users_count, "banned": banned}

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
        """Получить пользователя по ID."""
        return await db.get(User, user_id)

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """Получить пользователя по email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, name: str, email: str, password_hash: str) -> User:
        """Создать нового пользователя."""
        user = User(name=name, email=email, password_hash=password_hash)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def list_all(db: AsyncSession) -> list[User]:
        """Список всех пользователей (для админа)."""
        result = await db.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def paginated_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        is_banned: bool | None = None,
        role: str | None = None,
    ) -> tuple[list[User], int]:
        """Пагинированный список пользователей с поиском и фильтрацией (для админа)."""
        query = select(User).order_by(User.created_at.desc())
        count_query = select(func.count()).select_from(User)

        if search:
            pattern = f"%{search}%"
            query = query.where(
                User.name.ilike(pattern) | User.email.ilike(pattern)
            )
            count_query = count_query.where(
                User.name.ilike(pattern) | User.email.ilike(pattern)
            )

        if is_banned is not None:
            query = query.where(User.is_banned == is_banned)
            count_query = count_query.where(User.is_banned == is_banned)

        if role is not None:
            query = query.where(User.role == role.upper())
            count_query = count_query.where(User.role == role.upper())

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return items, total
