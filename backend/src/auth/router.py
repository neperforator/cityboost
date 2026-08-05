"""
API-роуты для аутентификации.
Регистрация, вход, получение профиля.
Refresh токен — в httpOnly cookie (безопасно от XSS).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.config import settings
from src.auth.models import User
from src.auth.schemas import (
    ForgotPasswordRequest,
    LogoutResponse,
    ResendCodeRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserOut,
    UserRegisterRequest,
    UserUpdateRequest,
    VerifyCodeResponse,
    VerifyEmailRequest,
)
from src.auth.service import AuthService
from src.database import get_db

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Аутентификация"])


# ─── Cookie helpers ────────────────────────────────────────────────


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Установить refresh token как httpOnly cookie."""
    max_age = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite="lax",
        path=settings.REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Удалить refresh cookie."""
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite="lax",
    )


# ─── Endpoints ─────────────────────────────────────────────────────


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
    description="Аутентификация по email и паролю. "
    "Access токен — в теле ответа, refresh токен — в httpOnly cookie.",
)
async def login(
    data: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Аутентифицировать пользователя и вернуть access токен."""
    service = AuthService(db)
    user = await service.authenticate(data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email, пароль или аккаунт заблокирован",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Подтвердите email. Код отправлен на {user.email}",
        )

    access_token = service.create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
    )
    refresh_token = service.create_raw_refresh_token(user.id)
    user.refresh_token_hash = service.hash_refresh_token(refresh_token)
    user.refresh_token_expires = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    )
    await db.flush()

    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@auth_router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Обновить access токен",
    description="Принимает refresh токен из httpOnly cookie, "
    "проверяет его и возвращает новую пару токенов.",
)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Обновить access токен по refresh токену из cookie (ротация)."""
    service = AuthService(db)

    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Отсутствует refresh токен",
        )

    # Декодируем JWT refresh
    payload = service.decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh токен",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh токен",
        )

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh токен",
        )

    # Находим пользователя
    from src.auth.repository import UserRepository
    repo = UserRepository()
    user = await repo.get_by_id(db, uid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )

    # Проверяем хеш refresh токена в БД
    if user.refresh_token_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh токен не найден в системе",
        )

    if not service.verify_refresh_token_hash(refresh_token, user.refresh_token_hash):
        # Несовпадение — возможна кража токена → аннулируем все refresh токены пользователя
        user.refresh_token_hash = None
        user.refresh_token_expires = None
        await db.flush()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh токен (возможна кража токена)",
        )

    # Проверяем срок действия в БД
    if user.refresh_token_expires and user.refresh_token_expires < datetime.now(timezone.utc):
        user.refresh_token_hash = None
        user.refresh_token_expires = None
        await db.flush()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh токен истёк",
        )

    # Ротируем: создаём новую пару, старый хеш заменяем
    new_access_token = service.create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
    )
    new_refresh_token = service.create_raw_refresh_token(user.id)
    user.refresh_token_hash = service.hash_refresh_token(new_refresh_token)
    user.refresh_token_expires = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    )
    await db.flush()

    _set_refresh_cookie(response, new_refresh_token)
    return TokenResponse(access_token=new_access_token)


@auth_router.post(
    "/verify-email",
    response_model=VerifyCodeResponse,
    summary="Подтвердить email",
    description="Подтверждает email 6-значным кодом из письма. "
    "При успехе возвращает access токен и данные пользователя. "
    "Refresh токен — в httpOnly cookie.",
)
async def verify_email(
    data: VerifyEmailRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> VerifyCodeResponse:
    """Подтвердить email по коду из письма."""
    service = AuthService(db)
    user = await service.verify_email(data.email, data.code)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или просроченный код подтверждения",
        )

    access_token = service.create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
    )
    refresh_token = service.create_raw_refresh_token(user.id)
    user.refresh_token_hash = service.hash_refresh_token(refresh_token)
    user.refresh_token_expires = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    )
    await db.flush()

    # Обновляем объект для сериализации
    await db.refresh(user)

    _set_refresh_cookie(response, refresh_token)
    return VerifyCodeResponse(access_token=access_token, user=user)


@auth_router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Выйти",
    description="Аннулирует refresh токен на сервере и удаляет cookie.",
)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LogoutResponse:
    """Выйти — очистить refresh токен в БД и cookie."""
    from src.auth.repository import UserRepository
    repo = UserRepository()
    user = await repo.get_by_id(db, current_user.id)
    if user:
        user.refresh_token_hash = None
        user.refresh_token_expires = None
        await db.flush()
    _clear_refresh_cookie(response)
    return LogoutResponse()


@auth_router.post(
    "/resend-code",
    status_code=status.HTTP_200_OK,
    summary="Отправить код повторно",
    description="Генерирует новый 6-значный код и отправляет на email. "
    "Всегда возвращает 200 (не раскрывает существование email).",
)
async def resend_code(
    data: ResendCodeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Отправить новый код подтверждения на email."""
    service = AuthService(db)
    await service.resend_verification_code(data.email)
    return {"message": "Новый код отправлен на указанный email"}


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
