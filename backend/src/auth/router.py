"""
API-роуты для аутентификации.
Регистрация, вход, получение профиля.
Refresh токен — в httpOnly cookie (безопасно от XSS).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User, UserRole
from src.auth.schemas import (
    Admin2FAResendRequest,
    Admin2FAResendResponse,
    Admin2FAVerifyRequest,
    ForgotPasswordRequest,
    LoginResponse,
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
from src.auth.service import AuthService, ensure_utc
from src.config import settings
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
        secure=settings.refresh_cookie_secure,
        samesite="lax",
        path=settings.REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Удалить refresh cookie."""
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
    )


def _no_store(response: Response) -> None:
    """Запретить кэширование ответов с токенами."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


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
        ) from None
    return user


@auth_router.post(
    "/login",
    response_model=LoginResponse,
    summary="Вход в систему",
    description="Аутентификация по email и паролю. "
    "Для администраторов возвращает requires_2fa=true и challenge_token: "
    "access/refresh токены выдаются только после проверки кода с email. "
    "Access токен — в теле ответа, refresh токен — в httpOnly cookie.",
)
async def login(
    data: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Аутентифицировать пользователя и вернуть access токен или запрос 2FA."""
    service = AuthService(db)
    user = await service.authenticate(data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email, пароль или аккаунт заблокирован",
        )

    if not user.is_verified and not settings.email_auth_bypassed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Подтвердите email. Код отправлен на {user.email}",
        )

    # Администраторы проходят обязательную проверку кода на email.
    # В DEBUG-режиме с DEBUG_BYPASS_EMAIL_AUTH вход выполняется без кода.
    if (
        user.role == UserRole.ADMIN
        and settings.ADMIN_2FA_ENABLED
        and not settings.email_auth_bypassed
    ):
        try:
            challenge_token = await service.create_admin_2fa_challenge(user)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from None
        _no_store(response)
        return LoginResponse(requires_2fa=True, challenge_token=challenge_token)

    access_token, refresh_token = await service.issue_tokens(user)
    _set_refresh_cookie(response, refresh_token)
    _no_store(response)
    return LoginResponse(access_token=access_token)


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
        ) from None

    # Находим пользователя с блокировкой строки, чтобы ротация была атомарной.
    from src.auth.repository import UserRepository
    repo = UserRepository()
    user = await repo.get_by_id_for_update(db, uid)
    if user is None:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )

    # Забаненный/неподтверждённый пользователь не может обновлять токены.
    if user.is_banned or (not user.is_verified and not settings.email_auth_bypassed):
        service.revoke_sessions(user)
        await db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия недействительна",
        )

    # Токен должен быть выдан для актуальной версии сессии.
    if payload.get("ver", 0) != user.token_version:
        service.revoke_sessions(user)
        await db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия недействительна",
        )

    # Для администраторов refresh разрешён только для сессии, прошедшей 2FA.
    two_factor_verified = payload.get("amr") == "2fa"
    if (
        user.role == UserRole.ADMIN
        and settings.ADMIN_2FA_ENABLED
        and not settings.email_auth_bypassed
        and not two_factor_verified
    ):
        service.revoke_sessions(user)
        await db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется повторный вход с подтверждением по email",
        )

    # Проверяем хеш refresh токена в БД
    if user.refresh_token_hash is None:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh токен не найден в системе",
        )

    if not service.verify_refresh_token_hash(refresh_token, user.refresh_token_hash):
        # Несовпадение — возможна кража токена → аннулируем все refresh токены пользователя
        service.revoke_sessions(user)
        await db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh токен (возможна кража токена)",
        )

    # Проверяем срок действия в БД
    if user.refresh_token_expires is None or ensure_utc(
        user.refresh_token_expires,
    ) < datetime.now(UTC):
        service.revoke_sessions(user)
        await db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh токен истёк",
        )

    # Ротируем: создаём новую пару, старый хеш заменяем.
    new_access_token, new_refresh_token = await service.issue_tokens(
        user,
        two_factor_verified=two_factor_verified,
    )
    await db.commit()

    _set_refresh_cookie(response, new_refresh_token)
    _no_store(response)
    return TokenResponse(access_token=new_access_token)


@auth_router.post(
    "/verify-email",
    response_model=VerifyCodeResponse,
    summary="Подтвердить email",
    description="Подтверждает email 6-значным кодом из письма. "
    "Для обычных пользователей сразу возвращает access токен. "
    "Для администратора возвращает только requires_2fa=true: "
    "после подтверждения email нужно войти с паролем и пройти 2FA. "
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

    # Администратору после подтверждения email всё равно нужен вход по паролю + 2FA.
    # Токены здесь не выдаём и 2FA-код не отправляем: пароль ещё не проверен.
    if user.role == UserRole.ADMIN and settings.ADMIN_2FA_ENABLED:
        await db.refresh(user)
        _no_store(response)
        return VerifyCodeResponse(user=user, requires_2fa=True)

    access_token, refresh_token = await service.issue_tokens(user)

    # Обновляем объект для сериализации
    await db.refresh(user)

    _set_refresh_cookie(response, refresh_token)
    _no_store(response)
    return VerifyCodeResponse(access_token=access_token, user=user)


@auth_router.post(
    "/admin-2fa/verify",
    response_model=TokenResponse,
    summary="Подтвердить вход администратора",
    description="Проверяет 6-значный код из письма и только при успехе "
    "выдаёт access/refresh токены.",
)
async def verify_admin_2fa(
    data: Admin2FAVerifyRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Завершить вход администратора после проверки кода 2FA."""
    service = AuthService(db)
    user = await service.verify_admin_2fa(data.challenge_token, data.code)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный код подтверждения. Запросите новый код.",
        )

    access_token, refresh_token = await service.issue_tokens(
        user,
        two_factor_verified=True,
    )
    _set_refresh_cookie(response, refresh_token)
    _no_store(response)
    return TokenResponse(access_token=access_token)


@auth_router.post(
    "/admin-2fa/resend",
    response_model=Admin2FAResendResponse,
    summary="Отправить код 2FA повторно",
    description="Генерирует новый код и отправляет его на email администратора. "
    "Между отправками действует задержка.",
)
async def resend_admin_2fa(
    data: Admin2FAResendRequest,
    db: AsyncSession = Depends(get_db),
) -> Admin2FAResendResponse:
    """Повторно отправить код подтверждения администратора."""
    service = AuthService(db)
    result = await service.resend_admin_2fa(data.challenge_token)
    if result == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия подтверждения истекла. Войдите заново.",
        )
    if result == "cooldown":
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Код уже отправлен. Повторите попытку через "
                f"{settings.ADMIN_2FA_RESEND_COOLDOWN_SECONDS} секунд."
            ),
        )
    if result == "email_failed":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Не удалось отправить код на email. Попробуйте позже.",
        )
    return Admin2FAResendResponse()


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
        AuthService.revoke_sessions(user)
        await db.commit()
    _clear_refresh_cookie(response)
    _no_store(response)
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
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Отправить новый код подтверждения на email."""
    service = AuthService(db)
    sent = await service.resend_verification_code(data.email)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Код уже отправлен. Повторите попытку через "
                f"{settings.VERIFICATION_RESEND_COOLDOWN_SECONDS} секунд."
            ),
        )
    _no_store(response)
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
    response: Response,
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
        ) from None
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if data.new_password:
        # Смена пароля инвалидировала сессии — удаляем cookie.
        _clear_refresh_cookie(response)
    _no_store(response)
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
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Запросить сброс пароля."""
    service = AuthService(db)
    await service.generate_reset_token(data.email)
    _no_store(response)
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
    response: Response,
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
        ) from None
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или просроченный токен сброса пароля",
        )
    _clear_refresh_cookie(response)
    _no_store(response)
    return {"message": "Пароль успешно изменён"}
