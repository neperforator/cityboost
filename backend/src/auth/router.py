"""
API-роуты для аутентификации.
Регистрация, вход, получение профиля.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.auth.schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserOut,
    UserRegisterRequest,
    UserUpdateRequest,
)
from src.auth.service import AuthService
from src.database import get_db

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Аутентификация"])


@auth_router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создаёт нового пользователя и возвращает его публичные данные.",
)
async def register(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Зарегистрировать нового пользователя."""
    service = AuthService(db)
    try:
        user = await service.register(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    return user


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход в систему",
    description="Аутентификация по email и паролю. Возвращает JWT access token.",
)
async def login(
    data: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Аутентифицировать пользователя и вернуть JWT токен."""
    service = AuthService(db)
    user = await service.authenticate(data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email, пароль или аккаунт заблокирован",
        )
    token = service.create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
    )
    return TokenResponse(access_token=token)


@auth_router.get(
    "/me",
    response_model=UserOut,
    summary="Текущий пользователь",
    description="Возвращает данные аутентифицированного пользователя.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Получить профиль текущего пользователя."""
    return current_user


@auth_router.patch(
    "/me",
    response_model=UserOut,
    summary="Обновить профиль",
    description="Обновляет имя и/или пароль текущего пользователя.",
)
async def update_me(
    data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Обновить профиль текущего пользователя."""
    service = AuthService(db)
    try:
        user = await service.update_profile(current_user.id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@auth_router.post(
    "/me/avatar",
    response_model=UserOut,
    summary="Загрузить аватар",
    description="Загружает аватар пользователя (JPEG/PNG, макс 1 МБ).",
)
async def upload_avatar(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Загрузить аватар."""
    contents = await file.read()
    service = AuthService(db)
    try:
        user = await service.upload_avatar(
            current_user.id, contents, file.filename or "", file.content_type or "",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@auth_router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Запросить сброс пароля",
    description="Отправляет письмо со ссылкой для сброса пароля. "
    "Всегда возвращает 200 (не раскрывает существование email).",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Запросить сброс пароля."""
    service = AuthService(db)
    await service.generate_reset_token(data.email)
    return {
        "message": "Если email зарегистрирован, вы получите письмо со ссылкой для сброса пароля",
    }


@auth_router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Сбросить пароль по токену",
    description="Устанавливает новый пароль, если токен сброса валиден.",
)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Сбросить пароль по токену из письма."""
    service = AuthService(db)
    try:
        success = await service.reset_password(data.token, data.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или просроченный токен сброса пароля",
        )
    return {"message": "Пароль успешно изменён"}
