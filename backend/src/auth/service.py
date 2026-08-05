"""
Сервисный слой для аутентификации и JWT.
"""

from __future__ import annotations

import logging
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
logger = logging.getLogger(__name__)


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
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def create_raw_refresh_token(user_id: uuid.UUID) -> str:
        """Создать refresh token (JWT с долгим сроком)."""
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_refresh_token(token: str) -> dict | None:
        """Декодировать refresh token. Возвращает payload или None."""
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM],
            )
            if payload.get("type") != "refresh":
                return None
            return payload
        except JWTError:
            return None

    @staticmethod
    def hash_refresh_token(token: str) -> str:
        """Захешировать refresh token для хранения в БД."""
        return pwd_context.hash(token)

    @staticmethod
    def verify_refresh_token_hash(token: str, hashed: str) -> bool:
        """Проверить refresh token против хеша в БД."""
        return pwd_context.verify(token, hashed)

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

    @staticmethod
    def _generate_verification_code() -> str:
        """Сгенерировать 6-значный код подтверждения."""
        import random
        return str(random.randint(100000, 999999))

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

        # Генерируем код подтверждения
        code = self._generate_verification_code()
        user.verification_code = code
        user.verification_code_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        await self.db.flush()

        # Отправляем письмо
        from src.notifications.email import get_email_service
        email_service = get_email_service()
        await email_service.send_verification_code(
            email=data.email,
            code=code,
            name=data.name,
        )
        if settings.DEBUG:
            logger.info("DEBUG: Verification code for %s → %s", data.email, code)

        return user

    async def verify_email(self, email: str, code: str) -> User | None:
        """Подтвердить email по коду. Возвращает пользователя или None."""
        user = await self.repo.get_by_email(self.db, email)
        if user is None:
            return None
        if user.is_verified:
            return user  # уже подтверждён
        if user.verification_code is None or user.verification_code_expires is None:
            return None
        if user.verification_code_expires < datetime.now(timezone.utc):
            return None
        if user.verification_code != code:
            return None

        user.is_verified = True
        user.verification_code = None
        user.verification_code_expires = None
        await self.db.flush()
        return user

    async def resend_verification_code(self, email: str) -> bool:
        """Отправить новый код подтверждения на email."""
        user = await self.repo.get_by_email(self.db, email)
        if user is None:
            return True  # не раскрываем
        if user.is_verified:
            return True

        code = self._generate_verification_code()
        user.verification_code = code
        user.verification_code_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        await self.db.flush()

        from src.notifications.email import get_email_service
        email_service = get_email_service()
        await email_service.send_verification_code(
            email=email,
            code=code,
            name=user.name,
        )
        if settings.DEBUG:
            logger.info("DEBUG: New verification code for %s → %s", email, code)

        return True

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

        from src.config import settings

        email_service = get_email_service()
        await email_service.send_password_reset(
            email=email,
            token=token,
            name=user.name,
            base_url=settings.FRONTEND_URL,
        )

        if settings.DEBUG:
            logger.info(
                "DEBUG: Reset link for %s → %s/#/reset-password?token=%s",
                email, settings.FRONTEND_URL, token,
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
