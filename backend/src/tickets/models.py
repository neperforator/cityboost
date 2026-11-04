"""
Модели модуля заявок: Ticket, TicketFile, TicketHistory, TicketComment.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class TicketStatus(PyEnum):
    """Статусы заявки."""
    NEW = "NEW"
    IN_WORK = "IN_WORK"
    DONE = "DONE"
    CLOSED = "CLOSED"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status", create_type=True),
        default=TicketStatus.NEW,
        nullable=False,
    )
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    close_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Причина закрытия заявки (устанавливается при CLOSED)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )

    # Связи
    user = relationship("User", back_populates="tickets", foreign_keys=[user_id])
    assignee = relationship(
        "User", back_populates="assigned_tickets",
        foreign_keys=[assigned_to],
    )
    # Связи загружаются только явно через selectinload, чтобы списки заявок
    # не тянули все файлы/комментарии/историю.
    files = relationship("TicketFile", back_populates="ticket", lazy="raise", cascade="all, delete-orphan")
    history = relationship("TicketHistory", back_populates="ticket", lazy="raise", cascade="all, delete-orphan")
    comments = relationship("TicketComment", back_populates="ticket", lazy="raise", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Ticket {self.id} [{self.status}] {self.title}>"


class TicketFile(Base):
    __tablename__ = "ticket_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    ticket = relationship("Ticket", back_populates="files")

    def __repr__(self) -> str:
        return f"<TicketFile {self.file_path}>"


class TicketHistory(Base):
    __tablename__ = "ticket_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False,
    )
    changed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(30), default="STATUS_CHANGED", nullable=False, index=True,
    )
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    ticket = relationship("Ticket", back_populates="history")
    changed_by_user = relationship("User", back_populates="history_changes")

    def __repr__(self) -> str:
        return f"<TicketHistory {self.action} {self.old_status} -> {self.new_status}>"


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
    )
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User", back_populates="comments")

    def __repr__(self) -> str:
        return f"<TicketComment by {self.author_id}>"
