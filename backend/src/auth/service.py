"""
Сервисный слой для аутентификации и JWT.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.auth.repository import UserRepository
from src.auth.schemas import UserRegisterRequest, UserUpdateRequest
from src.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Сервис для регистрации, входа и JWT."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository()

    # ---- Хэширование паролей ----

    @staticmethod
    def hash_password(password: str) -> str:
        """Хэшировать пароль."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверить пароль."""
        return pwd_context.verify(plain_password, hashed_password)

    # ---- JWT ----

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """Создать JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> dict | None:
        """Декодировать JWT токен. Возвращает payload или None."""
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except JWTError:
            return None

    # ---- Бизнес-логика ----

    async def register(self, data: UserRegisterRequest) -> User:
        """Регистрация нового пользователя."""
        existing = await self.repo.get_by_email(self.db, data.email)
        if existing:
            raise ValueError("Пользователь с таким email уже существует")

        # Проверка сложности пароля
        password = data.password
        if len(password) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if not re.search(r"[A-ZА-Я]", password):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-zа-я]", password):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"\d", password):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        common_passwords = {"password", "password123", "qwerty123", "12345678", "admin123"}
        if password.lower() in common_passwords:
            raise ValueError("Слишком простой пароль")

        password_hash = self.hash_password(password)
        user = await self.repo.create(self.db, data.name, data.email, password_hash)
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        """Аутентификация по email и паролю."""
        user = await self.repo.get_by_email(self.db, email)
        if not user or not self.verify_password(password, user.password_hash):
            return None
        if user.is_banned:
            return None
        return user

    async def get_current_user(self, token: str) -> User | None:
        """Получить пользователя по JWT токену."""
        payload = self.decode_access_token(token)
        if payload is None:
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return None
        return await self.repo.get_by_id(self.db, uid)

    async def require_admin(self, user: User) -> bool:
        """Проверить, что пользователь — администратор."""
        return user.role == UserRole.ADMIN

    # ---- Профиль ----

    async def update_profile(self, user_id: uuid.UUID, data: UserUpdateRequest) -> User | None:
        """Обновить профиль пользователя (имя, пароль)."""
        user = await self.repo.get_by_id(self.db, user_id)
        if user is None:
            return None

        if data.name is not None:
            user.name = data.name

        if data.new_password:
            if not data.current_password:
                raise ValueError("Для смены пароля укажите текущий пароль")
            if not self.verify_password(data.current_password, user.password_hash):
                raise ValueError("Неверный текущий пароль")
            # Валидация сложности
            pwd = data.new_password
            if len(pwd) < 8:
                raise ValueError("Пароль должен содержать минимум 8 символов")
            if not re.search(r"[A-ZА-Я]", pwd):
                raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
            if not re.search(r"[a-zа-я]", pwd):
                raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
            if not re.search(r"\d", pwd):
                raise ValueError("Пароль должен содержать хотя бы одну цифру")

            user.password_hash = self.hash_password(pwd)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def upload_avatar(
        self, user_id: uuid.UUID, file_bytes: bytes, filename: str, content_type: str,
    ) -> User | None:
        """Загрузить аватар пользователя."""
        import os

        from pathlib import Path

        user = await self.repo.get_by_id(self.db, user_id)
        if user is None:
            return None

        # Валидация типа
        allowed = {"image/jpeg", "image/png"}
        if content_type not in allowed:
            raise ValueError("Допустимы только JPEG и PNG")

        # Валидация размера (макс 1 МБ)
        MAX_AVATAR_BYTES = 1 * 1024 * 1024
        if len(file_bytes) > MAX_AVATAR_BYTES:
            raise ValueError("Аватар не должен превышать 1 МБ")

        # Magic bytes проверка
        image_signatures = {
            b"\xff\xd8\xff": "image/jpeg",
            b"\x89PNG\r\n\x1a\n": "image/png",
        }
        is_valid = any(
            file_bytes[:len(sig)] == sig for sig in image_signatures
        )
        if not is_valid:
            raise ValueError("Файл не является изображением")

        # Сохраняем файл
        ext = ".jpg" if content_type == "image/jpeg" else ".png"
        avatar_filename = f"avatar{ext}"
        avatar_dir = settings.UPLOAD_PATH.parent / "avatars" / str(user_id)
        avatar_dir.mkdir(parents=True, exist_ok=True)

        # Удаляем старый аватар
        if user.avatar_path:
            old_path = settings.UPLOAD_PATH.parent.parent / user.avatar_path
            if old_path.exists():
                os.remove(old_path)

        file_path = avatar_dir / avatar_filename
        file_path.write_bytes(file_bytes)

        relative_path = f"uploads/avatars/{user_id}/{avatar_filename}"
        user.avatar_path = relative_path
        await self.db.flush()
        await self.db.refresh(user)
        return user

    # ---- Сброс пароля ----

    async def generate_reset_token(self, email: str) -> bool:
        """
        Сгенерировать токен сброса пароля и отправить письмо.

        Всегда возвращает True (не раскрываем, существует ли email).
        """
        from datetime import datetime, timedelta, timezone

        user = await self.repo.get_by_email(self.db, email)
        if user is None:
            return True  # не раскрываем

        from src.notifications.email import get_email_service

        token = str(uuid.uuid4())
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await self.db.flush()

        email_service = get_email_service()
        await email_service.send_password_reset(
            email=email,
            token=token,
            name=user.name,
            base_url="",
        )
        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Сбросить пароль по токену.

        Returns:
            True при успехе, False если токен недействителен или истёк.
        """
        from datetime import datetime, timezone

        result = await self.db.execute(
            select(User).where(User.reset_token == token),
        )
        user = result.scalar_one_or_none()
        if user is None:
            return False

        now = datetime.now(timezone.utc)
        if user.reset_token_expires and user.reset_token_expires < now:
            # Просроченный токен — очищаем
            user.reset_token = None
            user.reset_token_expires = None
            await self.db.flush()
            return False

        # Проверка сложности пароля
        password = new_password
        if len(password) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if not re.search(r"[A-ZА-Я]", password):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-zа-я]", password):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"\d", password):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")

        # Смена пароля
        user.password_hash = self.hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        await self.db.flush()
        return True
