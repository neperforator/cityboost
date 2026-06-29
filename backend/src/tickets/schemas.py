"""
Pydantic схемы (DTO) для модуля заявок.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from src.tickets.models import TicketStatus


# ---------- Ticket ----------

class TicketCreateRequest(BaseModel):
    """Создание новой заявки."""
    title: str = Field(..., min_length=1, max_length=255, description="Заголовок заявки")
    description: str = Field(..., min_length=1, description="Описание проблемы")
    latitude: float | None = Field(None, ge=-90, le=90, description="Широта")
    longitude: float | None = Field(None, ge=-180, le=180, description="Долгота")
    address: str | None = Field(None, max_length=500, description="Текстовый адрес")


class TicketUpdateRequest(BaseModel):
    """Обновление заявки (для пользователя)."""
    title: str | None = Field(None, max_length=255)
    description: str | None = None


class TicketOut(BaseModel):
    """Ответ API с данными заявки."""
    id: uuid.UUID
    user_id: uuid.UUID
    assigned_to: uuid.UUID | None
    title: str
    description: str
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
            user = getattr(data, 'user', None)
            assignee = getattr(data, 'assignee', None)
            return {
                "id": data.id,
                "user_id": data.user_id,
                "assigned_to": data.assigned_to,
                "title": data.title,
                "description": data.description,
                "status": data.status,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "address": data.address,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "user_name": user.name if user else "",
                "assigned_to_name": assignee.name if assignee else None,
            }
        return data


class TicketOutDetail(TicketOut):
    """Полная информация о заявке (со связями)."""
    files: list["TicketFileOut"] = []
    comments: list["TicketCommentOut"] = []


class PaginatedTickets(BaseModel):
    """Пагинированный ответ со списком заявок."""
    items: list[TicketOut]
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
    """Запись истории изменения статуса заявки."""
    id: uuid.UUID
    ticket_id: uuid.UUID
    changed_by: uuid.UUID
    changed_by_name: str = ""
    old_status: str | None
    new_status: str
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
                "old_status": data.old_status,
                "new_status": data.new_status,
                "created_at": data.created_at,
                "changed_by_name": user.name if user else "",
            }
        return data
