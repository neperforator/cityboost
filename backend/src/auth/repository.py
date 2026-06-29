"""
Репозиторий для работы с пользователями (CRUD).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User


class UserRepository:
    """Репозиторий операций над пользователями."""

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
