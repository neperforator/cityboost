"""
API-роуты для работы с заявками (пользовательские).
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.config import settings
from src.database import get_db
from src.tickets.schemas import (
    PaginatedTickets,
    TicketCreateRequest,
    TicketFileOut,
    TicketOut,
    TicketOutDetail,
)
from src.tickets.service import TicketService

tickets_router = APIRouter(prefix="/api/v1/tickets", tags=["Заявки"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}


@tickets_router.post(
    "",
    response_model=TicketOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать заявку",
    description="Создаёт новую заявку от имени текущего пользователя."
    " Можно передать координаты (lat/lon) или текстовый адрес.",
)
async def create_ticket(
    data: TicketCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketOut:
    """Создать заявку."""
    service = TicketService(db)
    ticket = await service.create_ticket(current_user.id, data)
    return ticket


@tickets_router.get(
    "",
    response_model=PaginatedTickets,
    summary="Список заявок",
    description="Список заявок текущего пользователя с пагинацией.",
)
async def list_tickets(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedTickets:
    """Получить список своих заявок (пагинированный)."""
    service = TicketService(db)
    items, total = await service.list_user_tickets(current_user.id, page, page_size)
    return PaginatedTickets(items=items, total=total, page=page, page_size=page_size)


@tickets_router.get(
    "/{ticket_id}",
    response_model=TicketOutDetail,
    summary="Детали заявки",
    description="Получить полную информацию о заявке с файлами и комментариями.",
)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketOutDetail:
    """Получить заявку по ID."""
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
    return TicketOutDetail(
        id=ticket.id,
        user_id=ticket.user_id,
        assigned_to=ticket.assigned_to,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        latitude=ticket.latitude,
        longitude=ticket.longitude,
        address=ticket.address,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        files=ticket.files,
        comments=ticket.comments,
    )


@tickets_router.post(
    "/{ticket_id}/files",
    response_model=TicketFileOut,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить файл",
    description="Загрузить файл (JPEG/PNG) к заявке. Макс. 5 МБ, не более 5 файлов на заявку.",
)
async def upload_file(
    ticket_id: uuid.UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketFileOut:
    """Загрузить файл в заявку."""
    # Валидация MIME-типа
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип файла: {file.content_type}. Разрешены: JPEG, PNG",
        )

    # Чтение содержимого для проверки размера и сигнатуры
    contents = await file.read()
    file_size = len(contents)

    # Валидация по magic bytes (реальный тип файла)
    if file_size > 0:
        image_signatures = {
            b"\xff\xd8\xff": "image/jpeg",
            b"\x89PNG\r\n\x1a\n": "image/png",
        }
        is_valid_image = False
        for signature, mime in image_signatures.items():
            if contents[:len(signature)] == signature:
                is_valid_image = True
                break
        if not is_valid_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл не является изображением (проверка по сигнатуре файла не пройдена)",
            )

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл слишком большой. Максимум {settings.MAX_FILE_SIZE_MB} МБ",
        )

    # Проверка количества файлов
    service = TicketService(db)
    existing_files = await service.get_file_count(ticket_id)
    if existing_files >= settings.MAX_FILES_PER_TICKET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Превышен лимит файлов ({settings.MAX_FILES_PER_TICKET})",
        )

    # Сохранение файла на диск
    upload_path = Path(settings.UPLOAD_PATH) / str(ticket_id)
    upload_path.mkdir(parents=True, exist_ok=True)

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_full_path = upload_path / unique_filename
    file_full_path.write_bytes(contents)

    # Сохранение в БД
    relative_path = f"uploads/tickets/{ticket_id}/{unique_filename}"
    file_record = await service.add_file(
        ticket_id=ticket_id,
        file_path=relative_path,
        file_size=file_size,
        mime_type=file.content_type,
    )

    return file_record
