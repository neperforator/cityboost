"""
Модель пользователя (User).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, String, func
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
    reset_token: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True,
    )
    reset_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    avatar_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
    )

    # Связи
    tickets = relationship(
        "Ticket", back_populates="user",
        foreign_keys="Ticket.user_id",
        lazy="selectin",
    )
    assigned_tickets = relationship(
        "Ticket", back_populates="assignee",
        foreign_keys="Ticket.assigned_to",
        lazy="selectin",
    )
    comments = relationship("TicketComment", back_populates="author", lazy="selectin")
    history_changes = relationship("TicketHistory", back_populates="changed_by_user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
