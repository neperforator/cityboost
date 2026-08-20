"""
API-роуты для работы с заявками (пользовательские).
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.config import settings
from src.database import get_db
from src.tickets.models import TicketStatus
from src.tickets.schemas import (
    PaginatedTickets,
    TicketCommentCreate,
    TicketCommentOut,
    TicketCreateRequest,
    TicketFileOut,
    TicketOut,
    TicketOutDetail,
    TicketStats,
)
from src.tickets.service import TicketService

tickets_router = APIRouter(prefix="/api/v1/tickets", tags=["Заявки"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}

# Максимальный размер файла: 10 МБ (стандартный лимит nginx)
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_FILES_PER_TICKET = 5


async def _validate_and_save_image(file: UploadFile) -> tuple[bytes, str]:
    """Проверить файл (тип, сигнатура, размер) и вернуть (содержимое, имя_файла)."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип файла: {file.content_type}. Разрешены: JPEG, PNG",
        )

    contents = await file.read()
    file_size = len(contents)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл пустой",
        )

    # Проверка сигнатуры
    image_signatures = {
        b"\xff\xd8\xff": "image/jpeg",
        b"\x89PNG\r\n\x1a\n": "image/png",
    }
    is_valid = any(
        contents[:len(sig)] == sig for sig in image_signatures
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл не является изображением (проверка по сигнатуре не пройдена)",
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл слишком большой. Максимум 10 МБ",
        )

    return contents, file.filename or "image.jpg"


@tickets_router.post(
    "",
    response_model=TicketOutDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Создать заявку",
    description="Создаёт новую заявку с обязательными фото. "
    "Поля title, description — текстовые. "
    "files — список файлов (JPEG/PNG), минимум 1.",
)
async def create_ticket(
    title: str = Form(..., min_length=1, max_length=255),
    description: str = Form(..., min_length=1),
    address: str | None = Form(None, max_length=500),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    files: list[UploadFile] = File(..., description="Фото (JPEG/PNG, мин. 1 файл)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketOutDetail:
    """Создать заявку с обязательными фото."""
    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо загрузить хотя бы одно фото",
        )
    if len(files) > MAX_FILES_PER_TICKET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Максимум {MAX_FILES_PER_TICKET} файлов за раз",
        )

    # Валидируем и читаем каждый файл
    file_data_list: list[tuple[str, bytes, str]] = []  # (mime, contents, filename)
    for f in files:
        contents, fname = await _validate_and_save_image(f)
        file_data_list.append((f.content_type or "image/jpeg", contents, fname))

    service = TicketService(db)
    ticket = await service.create_ticket_with_files(
        user_id=current_user.id,
        title=title,
        description=description,
        file_data_list=file_data_list,
        latitude=latitude,
        longitude=longitude,
        address=address,
    )
    return ticket


@tickets_router.get(
    "",
    response_model=PaginatedTickets,
    summary="Список заявок",
    description="Список заявок текущего пользователя с пагинацией и фильтром по статусу.",
)
async def list_tickets(
    page: int = 1,
    page_size: int = 20,
    status: TicketStatus | None = Query(None, description="Фильтр по статусу"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedTickets:
    """Получить список своих заявок (пагинированный)."""
    service = TicketService(db)
    items, total = await service.list_user_tickets(current_user.id, page, page_size, status)
    return PaginatedTickets(items=items, total=total, page=page, page_size=page_size)


@tickets_router.get(
    "/stats",
    response_model=TicketStats,
    summary="Статистика заявок",
    description="Количество заявок текущего пользователя по статусам.",
)
async def ticket_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketStats:
    """Получить статистику заявок текущего пользователя."""
    service = TicketService(db)
    counts = await service.repo.get_status_counts(db, current_user.id)
    return TicketStats(
        total=counts.get("total", 0),
        new=counts.get("NEW", 0),
        in_work=counts.get("IN_WORK", 0),
        done=counts.get("DONE", 0),
        closed=counts.get("CLOSED", 0),
    )


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
        user_name=ticket.user.name if ticket.user else "",
        assigned_to_name=ticket.assignee.name if ticket.assignee else None,
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
    try:
        file_record = await service.add_file(
            ticket_id=ticket_id,
            file_path=relative_path,
            file_size=file_size,
            mime_type=file.content_type,
            author_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return file_record


@tickets_router.post(
    "/{ticket_id}/comments",
    response_model=TicketCommentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить комментарий",
    description="Добавить комментарий к заявке (автор заявки или администратор).",
)
async def add_comment(
    ticket_id: uuid.UUID,
    data: TicketCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketCommentOut:
    """Добавить комментарий к заявке."""
    service = TicketService(db)
    # Проверяем, что заявка существует и пользователь — автор или админ
    ticket = await service.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
    if ticket.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только автор заявки или администратор может добавлять комментарии",
        )
    try:
        comment = await service.add_comment(ticket_id, current_user.id, data.comment_text)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return TicketCommentOut(
        id=comment.id,
        ticket_id=comment.ticket_id,
        author_id=comment.author_id,
        author_name=current_user.name,
        author_role=current_user.role.value,
        comment_text=comment.comment_text,
        created_at=comment.created_at,
    )
