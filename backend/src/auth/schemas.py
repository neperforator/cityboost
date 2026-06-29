"""
Pydantic схемы (DTO) для модуля аутентификации.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from src.auth.models import UserRole


class UserRegisterRequest(BaseModel):
    """Тело запроса на регистрацию."""
    name: str = Field(..., min_length=1, max_length=150, description="Имя пользователя")
    email: EmailStr = Field(..., description="Электронная почта")
    password: str = Field(..., min_length=8, max_length=128, description="Пароль (мин. 8 символов)")


class UserLoginRequest(BaseModel):
    """Тело запроса на вход."""
    email: EmailStr = Field(..., description="Электронная почта")
    password: str = Field(..., description="Пароль")


class UserUpdateRequest(BaseModel):
    """Обновление профиля."""
    name: str | None = Field(None, max_length=150, description="Новое имя")
    current_password: str | None = Field(None, max_length=128, description="Текущий пароль (для смены)")
    new_password: str | None = Field(None, min_length=8, max_length=128, description="Новый пароль")


class UserOut(BaseModel):
    """Публичные данные пользователя (ответ API)."""
    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    is_banned: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Ответ с JWT токеном."""
    access_token: str
    token_type: str = "bearer"


class PaginatedUsers(BaseModel):
    """Пагинированный ответ со списком пользователей."""
    items: list[UserOut]
    total: int
    page: int
    page_size: int


class ForgotPasswordRequest(BaseModel):
    """Запрос на сброс пароля."""
    email: EmailStr = Field(..., description="Электронная почта")


class ResetPasswordRequest(BaseModel):
    """Сброс пароля по токену."""
    token: str = Field(..., description="Токен сброса из письма")
    password: str = Field(..., min_length=8, max_length=128, description="Новый пароль")
