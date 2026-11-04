"""
API-роуты для работы с заявками (пользовательские).
"""

from __future__ import annotations

import uuid
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User, UserRole
from src.config import settings
from src.database import get_db
from src.tickets.models import Ticket, TicketStatus
from src.tickets.schemas import (
    PaginatedTickets,
    TicketCommentCreate,
    TicketCommentOut,
    TicketFileOut,
    TicketOutDetail,
    TicketStats,
)
from src.tickets.service import TicketService

tickets_router = APIRouter(prefix="/api/v1/tickets", tags=["Заявки"])

# Соответствие формата Pillow → MIME и безопасное расширение.
_IMAGE_FORMATS: dict[str, tuple[str, str]] = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
}


async def _read_upload(file: UploadFile) -> bytes:
    """Прочитать файл с ограничением размера, не загружая лишнее в память."""
    contents = await file.read(settings.MAX_FILE_SIZE_BYTES + 1)
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл пустой",
        )
    if len(contents) > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл слишком большой. Максимум {settings.MAX_FILE_SIZE_MB} МБ",
        )
    return contents


def _detect_image(contents: bytes) -> tuple[str, str]:
    """Проверить изображение через Pillow и вернуть (mime, расширение)."""
    try:
        # verify() проверяет целостность, но после него объект нужно открыть заново.
        with Image.open(BytesIO(contents)) as image:
            image.verify()
        with Image.open(BytesIO(contents)) as image:
            image_format = image.format
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл не является корректным изображением",
        ) from None

    if image_format not in _IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Разрешены только изображения JPEG и PNG",
        )
    return _IMAGE_FORMATS[image_format]


async def _validate_image(file: UploadFile) -> tuple[str, bytes, str]:
    """Проверить загруженный файл и вернуть (mime, содержимое, расширение)."""
    contents = await _read_upload(file)
    mime_type, extension = _detect_image(contents)
    return mime_type, contents, extension


def _can_access_ticket(ticket: Ticket, user: User) -> bool:
    """Автор заявки или администратор."""
    return ticket.user_id == user.id or user.role == UserRole.ADMIN


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
    if len(files) > settings.MAX_FILES_PER_TICKET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Максимум {settings.MAX_FILES_PER_TICKET} файлов за раз",
        )

    # Сначала валидируем все файлы, чтобы не создавать заявку с частичным набором.
    file_data_list: list[tuple[str, bytes, str]] = []  # (mime, contents, extension)
    for file in files:
        mime_type, contents, extension = await _validate_image(file)
        file_data_list.append((mime_type, contents, extension))

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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
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
    if not _can_access_ticket(ticket, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только автор заявки или администратор может просматривать заявку",
        )
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
    description="Загрузить файл (JPEG/PNG) к заявке. "
    "Максимум 5 МБ, не более 5 файлов на заявку.",
)
async def upload_file(
    ticket_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketFileOut:
    """Загрузить файл в заявку."""
    mime_type, contents, extension = await _validate_image(file)

    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
    if not _can_access_ticket(ticket, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только автор заявки или администратор может загружать файлы",
        )
    if ticket.status in (TicketStatus.DONE, TicketStatus.CLOSED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя загрузить файл к заявке со статусом «Выполнена» или «Закрыта»",
        )

    existing_files = await service.get_file_count(ticket_id)
    if existing_files >= settings.MAX_FILES_PER_TICKET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Превышен лимит файлов ({settings.MAX_FILES_PER_TICKET})",
        )

    try:
        file_record = await service.save_file(
            ticket=ticket,
            contents=contents,
            extension=extension,
            mime_type=mime_type,
            author_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None

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
    if not _can_access_ticket(ticket, current_user):
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
        ) from None
    return TicketCommentOut(
        id=comment.id,
        ticket_id=comment.ticket_id,
        author_id=comment.author_id,
        author_name=current_user.name,
        author_role=current_user.role.value,
        comment_text=comment.comment_text,
        created_at=comment.created_at,
    )
