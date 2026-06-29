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
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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
    comment_text: str = Field(..., min_length=1, description="Текст комментария")


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
            if author is not None:
                data.author_name = author.name
                data.author_role = author.role.value if hasattr(author, 'role') and author.role else "user"
            else:
                data.author_name = "Неизвестно"
                data.author_role = "user"
        return data


# ---------- Ticket History ----------

class TicketHistoryOut(BaseModel):
    """Запись истории изменения статуса заявки."""
    id: uuid.UUID
    ticket_id: uuid.UUID
    changed_by: uuid.UUID
    old_status: str | None
    new_status: str
    created_at: datetime

    model_config = {"from_attributes": True}
