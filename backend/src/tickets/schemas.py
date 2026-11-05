"""
Pydantic схемы (DTO) для модуля заявок.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, computed_field, model_validator

from src.tickets.models import TicketStatus


class TicketStatusChangeRequest(BaseModel):
    """Смена статуса заявки администратором."""
    new_status: TicketStatus = Field(..., description="Новый статус заявки")
    close_reason: str | None = Field(
        None, max_length=1000,
        description="Причина закрытия (обязательна при статусе CLOSED)",
    )

    @model_validator(mode="after")
    @classmethod
    def validate_close_reason(cls, data):
        if data.new_status == TicketStatus.CLOSED and not (data.close_reason or "").strip():
            raise ValueError("Необходимо указать причину закрытия заявки")
        return data


# ---------- Ticket ----------

class TicketOutBase(BaseModel):
    """Общие поля заявки, которые нужны и в списке, и в деталях."""
    id: uuid.UUID
    user_id: uuid.UUID
    assigned_to: uuid.UUID | None
    title: str
    status: TicketStatus
    latitude: float | None
    longitude: float | None
    address: str | None
    user_name: str = ""
    assigned_to_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def populate_ticket_names(cls, data):
        """Извлекаем имена пользователя и исполнителя из связанных ORM объектов."""
        if not isinstance(data, dict):
            # Берём только уже загруженные связи из __dict__, чтобы не вызвать
            # lazy-load (у связей lazy="raise") при сериализации списка.
            loaded = getattr(data, "__dict__", {})
            user = loaded.get("user")
            assignee = loaded.get("assignee")
            result = {
                "id": data.id,
                "user_id": data.user_id,
                "assigned_to": data.assigned_to,
                "title": data.title,
                "status": data.status,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "address": data.address,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "user_name": user.name if user else "",
                "assigned_to_name": assignee.name if assignee else None,
            }
            # Детальные поля добавляем, только если они реально есть у объекта.
            if hasattr(data, "description"):
                result["description"] = data.description
            if hasattr(data, "close_reason"):
                result["close_reason"] = data.close_reason
            # Для TicketOutDetail связи files/comments передаём, только если они
            # действительно загружены (selectinload), иначе Pydantic возьмёт [].
            if "files" in loaded:
                result["files"] = loaded["files"]
            if "comments" in loaded:
                result["comments"] = loaded["comments"]
            return result
        return data


class TicketOut(TicketOutBase):
    """Полная карточка заявки (без связей)."""
    description: str
    close_reason: str | None = None


class TicketOutShort(TicketOutBase):
    """Короткая карточка заявки для списков: без тяжёлого description."""
    pass


class TicketOutDetail(TicketOut):
    """Полная информация о заявке (со связями)."""
    files: list[TicketFileOut] = []
    comments: list[TicketCommentOut] = []


class PaginatedTickets(BaseModel):
    """Пагинированный ответ со списком заявок."""
    items: list[TicketOutShort]
    total: int
    page: int
    page_size: int
    status_counts: dict[str, int] | None = None


class TicketStats(BaseModel):
    """Статистика по статусам заявок."""
    total: int
    new: int
    in_work: int
    done: int
    closed: int


class TicketMapPoint(BaseModel):
    """Лёгкая точка заявки для карты."""
    id: uuid.UUID
    title: str
    status: TicketStatus
    latitude: float
    longitude: float
    address: str | None = None
    assigned_to_name: str | None = None
    created_at: datetime


class TicketMapOut(BaseModel):
    """Ответ с точками заявок для карты."""
    items: list[TicketMapPoint]
    total: int
    limit: int


# ---------- TicketFile ----------

class TicketFileOut(BaseModel):
    """Информация о прикреплённом файле."""
    id: uuid.UUID
    ticket_id: uuid.UUID
    file_path: str
    file_size: int
    mime_type: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def file_name(self) -> str:
        """Имя файла без пути — удобно для отображения на клиенте."""
        return Path(self.file_path).name


# ---------- TicketComments ----------

class TicketCommentCreate(BaseModel):
    """Создание комментария (публичного)."""
    comment_text: str = Field(..., min_length=1, max_length=2000, description="Текст комментария")


class TicketCommentOut(BaseModel):
    """Комментарий к заявке."""
    id: uuid.UUID
    ticket_id: uuid.UUID
    author_id: uuid.UUID
    author_name: str
    author_role: str = "user"
    comment_text: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def populate_author_name(cls, data):
        """Извлекаем имя и роль автора из связанного User при десериализации из ORM."""
        if not isinstance(data, dict):
            author = getattr(data, 'author', None)
            return {
                "id": data.id,
                "ticket_id": data.ticket_id,
                "author_id": data.author_id,
                "comment_text": data.comment_text,
                "created_at": data.created_at,
                "author_name": author.name if author is not None else "Неизвестно",
                "author_role": author.role.value if author is not None and hasattr(author, 'role') and author.role else "user",
            }
        return data


# ---------- Ticket History ----------

class TicketHistoryOut(BaseModel):
    """Запись истории изменения заявки."""
    id: uuid.UUID
    ticket_id: uuid.UUID
    changed_by: uuid.UUID
    changed_by_name: str = ""
    action: str = "STATUS_CHANGED"
    old_status: str | None
    new_status: str
    details: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def populate_changed_by_name(cls, data):
        """Извлекаем имя администратора из связанного changed_by_user."""
        if not isinstance(data, dict):
            user = getattr(data, 'changed_by_user', None)
            return {
                "id": data.id,
                "ticket_id": data.ticket_id,
                "changed_by": data.changed_by,
                "action": data.action,
                "old_status": data.old_status,
                "new_status": data.new_status,
                "details": data.details,
                "created_at": data.created_at,
                "changed_by_name": user.name if user else "",
            }
        return data
