"""
Модель пользователя (User).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class UserRole(PyEnum):
    """Роли пользователей."""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_type=True),
        default=UserRole.USER,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    is_banned: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    verification_code: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )
    verification_code_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    verification_attempts: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False,
    )
    verification_last_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    reset_token: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True,
    )
    reset_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    refresh_token_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )
    refresh_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    # Версия токенов: увеличивается при logout/смене пароля/бане,
    # чтобы немедленно инвалидировать выданные access/refresh токены.
    token_version: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False,
    )

    # --- Двухфакторная аутентификация администраторов (код на email) ---
    two_factor_code_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )
    two_factor_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    two_factor_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )
    two_factor_last_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Связи — lazy="select" (загружаются только при обращении)
    tickets = relationship(
        "Ticket", back_populates="user",
        foreign_keys="Ticket.user_id",
        lazy="select",
    )
    assigned_tickets = relationship(
        "Ticket", back_populates="assignee",
        foreign_keys="Ticket.assigned_to",
        lazy="select",
    )
    comments = relationship("TicketComment", back_populates="author", lazy="select")
    history_changes = relationship("TicketHistory", back_populates="changed_by_user", lazy="select")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
