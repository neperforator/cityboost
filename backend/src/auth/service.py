"""
Сервисный слой для аутентификации и JWT.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.auth.repository import UserRepository
from src.auth.schemas import UserRegisterRequest, UserUpdateRequest
from src.config import settings

# bcrypt_sha256 предварительно хеширует пароль, поэтому длинные пароли
# (>72 байт) не обрезаются. Старые bcrypt-хеши продолжают проверяться.
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
)
logger = logging.getLogger(__name__)

# Фиктивный хеш для выравнивания времени ответа при неизвестном email.
_DUMMY_PASSWORD_HASH = pwd_context.hash("cityboost-dummy-password")


def ensure_utc(value: datetime) -> datetime:
    """Привести datetime из БД к aware UTC (SQLite возвращает naive)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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
    def _encode(payload: dict) -> str:
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def _decode(token: str) -> dict | None:
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )
        except JWTError:
            return None

    @staticmethod
    def _base_payload(
        user_id: uuid.UUID,
        token_type: str,
        expires_delta: timedelta,
        token_version: int = 0,
    ) -> dict:
        now = datetime.now(UTC)
        return {
            "sub": str(user_id),
            "type": token_type,
            "ver": token_version,
            "iat": now,
            "exp": now + expires_delta,
            "jti": uuid.uuid4().hex,
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
        }

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: timedelta | None = None,
        token_version: int = 0,
    ) -> str:
        """Создать JWT access token."""
        payload = AuthService._base_payload(
            uuid.UUID(data["sub"]),
            "access",
            expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            token_version,
        )
        payload.update({k: v for k, v in data.items() if k not in payload})
        return AuthService._encode(payload)

    @staticmethod
    def create_raw_refresh_token(
        user_id: uuid.UUID,
        two_factor_verified: bool = False,
        token_version: int = 0,
    ) -> str:
        """Создать refresh token (JWT с долгим сроком)."""
        payload = AuthService._base_payload(
            user_id,
            "refresh",
            timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
            token_version,
        )
        if two_factor_verified:
            payload["amr"] = "2fa"
        return AuthService._encode(payload)

    @staticmethod
    def decode_refresh_token(token: str) -> dict | None:
        """Декодировать refresh token. Возвращает payload или None."""
        payload = AuthService._decode(token)
        if payload is None or payload.get("type") != "refresh":
            return None
        return payload

    @staticmethod
    def create_two_factor_token(user_id: uuid.UUID, token_version: int = 0) -> str:
        """Создать короткоживущий токен-приглашение для ввода кода 2FA."""
        payload = AuthService._base_payload(
            user_id,
            "2fa",
            timedelta(minutes=settings.ADMIN_2FA_CHALLENGE_TTL_MINUTES),
            token_version,
        )
        return AuthService._encode(payload)

    @staticmethod
    def decode_two_factor_token(token: str) -> dict | None:
        """Декодировать токен-приглашение 2FA. Возвращает payload или None."""
        payload = AuthService._decode(token)
        if payload is None or payload.get("type") != "2fa":
            return None
        return payload

    @staticmethod
    def _digest(value: str) -> str:
        """HMAC-SHA256 для токенов и одноразовых кодов."""
        return hmac.new(
            settings.JWT_SECRET_KEY.encode(),
            value.encode(),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def hash_refresh_token(token: str) -> str:
        """Захешировать refresh token для хранения в БД."""
        return AuthService._digest(token)

    @staticmethod
    def verify_refresh_token_hash(token: str, hashed: str) -> bool:
        """Проверить refresh token против хеша в БД (constant-time)."""
        return hmac.compare_digest(AuthService._digest(token), hashed)

    @staticmethod
    def hash_verification_code(user_id: uuid.UUID, code: str) -> str:
        """Захешировать 6-значный код подтверждения email."""
        return AuthService._digest(f"verify:{user_id}:{code}")

    @staticmethod
    def verify_verification_code(user_id: uuid.UUID, code: str, hashed: str) -> bool:
        return hmac.compare_digest(
            AuthService.hash_verification_code(user_id, code),
            hashed,
        )

    @staticmethod
    def hash_reset_token(token: str) -> str:
        return AuthService._digest(f"reset:{token}")

    @staticmethod
    def decode_access_token(token: str) -> dict | None:
        """Декодировать JWT access-токен. Возвращает payload или None."""
        payload = AuthService._decode(token)
        # Важно: refresh/2FA-токены не должны приниматься как access-токены.
        if payload is None or payload.get("type") != "access":
            return None
        return payload

    # ---- Бизнес-логика ----

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def _validate_password(password: str) -> None:
        """Проверка сложности пароля (общая для регистрации/смены/сброса)."""
        if len(password) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if not re.search(r"[A-ZА-Я]", password):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-zа-я]", password):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"\d", password):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        common_passwords = {
            "password", "password123", "qwerty123", "12345678", "admin123",
            "qwerty12345", "letmein123", "welcome123", "cityboost123",
        }
        if password.lower() in common_passwords:
            raise ValueError("Слишком простой пароль")

    @staticmethod
    def _generate_verification_code() -> str:
        """Сгенерировать криптостойкий 6-значный код подтверждения."""
        return f"{secrets.randbelow(1_000_000):06d}"

    async def register(self, data: UserRegisterRequest) -> User:
        """Регистрация нового пользователя."""
        email = self._normalize_email(data.email)
        existing = await self.repo.get_by_email(self.db, email)
        if existing:
            raise ValueError("Пользователь с таким email уже существует")

        self._validate_password(data.password)
        password_hash = self.hash_password(data.password)
        user = await self.repo.create(self.db, data.name, email, password_hash)

        # DEBUG-режим: не отправляем письмо и сразу считаем аккаунт подтверждённым.
        if settings.email_auth_bypassed:
            user.is_verified = True
            await self.db.flush()
            return user

        # Генерируем код подтверждения: в БД храним только хеш.
        code = self._generate_verification_code()
        now = datetime.now(UTC)
        user.verification_code = self.hash_verification_code(user.id, code)
        user.verification_code_expires = now + timedelta(
            minutes=settings.VERIFICATION_CODE_TTL_MINUTES,
        )
        user.verification_attempts = 0
        user.verification_last_sent_at = now
        await self.db.flush()

        from src.notifications.email import get_email_service
        email_service = get_email_service()
        await email_service.send_verification_code(
            email=email,
            code=code,
            name=data.name,
        )

        return user

    async def verify_email(self, email: str, code: str) -> User | None:
        """Подтвердить email по коду. Возвращает пользователя или None."""
        user = await self.repo.get_by_email(self.db, self._normalize_email(email))
        if user is None or user.is_verified:
            return None
        if user.verification_code is None or user.verification_code_expires is None:
            return None

        now = datetime.now(UTC)
        if ensure_utc(user.verification_code_expires) < now:
            user.verification_code = None
            user.verification_code_expires = None
            user.verification_attempts = 0
            await self.db.commit()
            return None

        if user.verification_attempts >= settings.VERIFICATION_MAX_ATTEMPTS:
            user.verification_code = None
            user.verification_code_expires = None
            user.verification_attempts = 0
            await self.db.commit()
            return None

        if not self.verify_verification_code(user.id, code, user.verification_code):
            user.verification_attempts += 1
            if user.verification_attempts >= settings.VERIFICATION_MAX_ATTEMPTS:
                user.verification_code = None
                user.verification_code_expires = None
            # Важно: коммитим до выброса HTTPException в роутере,
            # иначе get_db откатит счётчик попыток.
            await self.db.commit()
            return None

        user.is_verified = True
        user.verification_code = None
        user.verification_code_expires = None
        user.verification_attempts = 0
        user.verification_last_sent_at = None
        await self.db.flush()
        return user

    async def resend_verification_code(self, email: str) -> bool:
        """Отправить новый код подтверждения на email."""
        user = await self.repo.get_by_email(self.db, self._normalize_email(email))
        if user is None or user.is_verified:
            return True  # не раскрываем существование/статус

        now = datetime.now(UTC)
        if user.verification_last_sent_at is not None:
            elapsed = (now - ensure_utc(user.verification_last_sent_at)).total_seconds()
            if elapsed < settings.VERIFICATION_RESEND_COOLDOWN_SECONDS:
                return False

        code = self._generate_verification_code()
        user.verification_code = self.hash_verification_code(user.id, code)
        user.verification_code_expires = now + timedelta(
            minutes=settings.VERIFICATION_CODE_TTL_MINUTES,
        )
        user.verification_attempts = 0
        user.verification_last_sent_at = now
        await self.db.flush()

        from src.notifications.email import get_email_service
        email_service = get_email_service()
        await email_service.send_verification_code(
            email=user.email,
            code=code,
            name=user.name,
        )
        return True

    async def authenticate(self, email: str, password: str) -> User | None:
        """Аутентификация по email и паролю."""
        user = await self.repo.get_by_email(self.db, self._normalize_email(email))
        # Выравниваем время ответа, чтобы нельзя было перечислять email.
        password_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
        password_ok = self.verify_password(password, password_hash)
        if user is None or not password_ok or user.is_banned:
            return None
        return user

    # ---- Сессии и токены ----

    async def issue_tokens(
        self,
        user: User,
        *,
        two_factor_verified: bool = False,
    ) -> tuple[str, str]:
        """Выдать access/refresh токены и сохранить хеш refresh в БД."""
        access_token = self.create_access_token(
            data={"sub": str(user.id), "role": user.role.value},
            token_version=user.token_version,
        )
        refresh_token = self.create_raw_refresh_token(
            user.id,
            two_factor_verified=two_factor_verified,
            token_version=user.token_version,
        )
        user.refresh_token_hash = self.hash_refresh_token(refresh_token)
        user.refresh_token_expires = datetime.now(UTC) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        )
        await self.db.flush()
        return access_token, refresh_token

    @staticmethod
    def revoke_sessions(user: User) -> None:
        """Аннулировать все access/refresh сессии и незавершённый 2FA-вход."""
        user.refresh_token_hash = None
        user.refresh_token_expires = None
        user.token_version = (user.token_version or 0) + 1
        AuthService.clear_two_factor(user)

    # ---- Двухфакторная аутентификация администраторов ----

    @staticmethod
    def _generate_two_factor_code() -> str:
        """Сгенерировать криптостойкий 6-значный код."""
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def clear_two_factor(user: User) -> None:
        """Очистить код и состояние 2FA."""
        user.two_factor_code_hash = None
        user.two_factor_expires = None
        user.two_factor_attempts = 0
        user.two_factor_last_sent_at = None

    async def _send_two_factor_code(self, user: User, code: str) -> bool:
        """Отправить код на email. В DEBUG при отсутствии SMTP пишет код в лог."""
        from src.notifications.email import get_email_service

        email_service = get_email_service()
        sent = await email_service.send_admin_2fa_code(
            email=user.email,
            code=code,
            name=user.name,
            expires_minutes=settings.ADMIN_2FA_CODE_TTL_MINUTES,
        )
        if sent:
            return True
        if settings.DEBUG:
            # Не логируем сам код даже в DEBUG.
            logger.warning("DEBUG: admin 2FA email не отправлен для %s", user.email)
            return True
        return False

    async def create_admin_2fa_challenge(self, user: User) -> str:
        """Создать код, отправить его на email и вернуть challenge-токен."""
        code = self._generate_two_factor_code()
        now = datetime.now(UTC)
        user.two_factor_code_hash = self.hash_password(code)
        user.two_factor_expires = now + timedelta(
            minutes=settings.ADMIN_2FA_CODE_TTL_MINUTES,
        )
        user.two_factor_attempts = 0
        user.two_factor_last_sent_at = now
        await self.db.flush()

        if not await self._send_two_factor_code(user, code):
            self.clear_two_factor(user)
            await self.db.commit()
            raise RuntimeError("Не удалось отправить код подтверждения на email")

        return self.create_two_factor_token(user.id, user.token_version)

    async def verify_admin_2fa(
        self,
        challenge_token: str,
        code: str,
    ) -> User | None:
        """Проверить код 2FA и вернуть администратора при успехе."""
        payload = self.decode_two_factor_token(challenge_token)
        if payload is None:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        try:
            uid = uuid.UUID(user_id)
        except (ValueError, TypeError):
            return None

        user = await self.repo.get_by_id(self.db, uid)
        if (
            user is None
            or user.role != UserRole.ADMIN
            or user.is_banned
            or not user.is_verified
            or payload.get("ver", 0) != user.token_version
        ):
            return None

        now = datetime.now(UTC)
        if not user.two_factor_code_hash or not user.two_factor_expires:
            return None
        if ensure_utc(user.two_factor_expires) < now:
            self.clear_two_factor(user)
            await self.db.commit()
            return None
        if user.two_factor_attempts >= settings.ADMIN_2FA_MAX_ATTEMPTS:
            self.clear_two_factor(user)
            await self.db.commit()
            return None

        if not self.verify_password(code, user.two_factor_code_hash):
            user.two_factor_attempts += 1
            if user.two_factor_attempts >= settings.ADMIN_2FA_MAX_ATTEMPTS:
                self.clear_two_factor(user)
            # Коммитим до HTTPException в роутере, иначе попытки откатятся.
            await self.db.commit()
            return None

        self.clear_two_factor(user)
        await self.db.flush()
        return user

    async def resend_admin_2fa(self, challenge_token: str) -> str:
        """
        Повторно отправить код 2FA.

        Возвращает: sent / invalid / cooldown / email_failed.
        """
        payload = self.decode_two_factor_token(challenge_token)
        if payload is None:
            return "invalid"
        user_id = payload.get("sub")
        if not user_id:
            return "invalid"
        try:
            uid = uuid.UUID(user_id)
        except (ValueError, TypeError):
            return "invalid"

        user = await self.repo.get_by_id(self.db, uid)
        if (
            user is None
            or user.role != UserRole.ADMIN
            or user.is_banned
            or not user.is_verified
            or payload.get("ver", 0) != user.token_version
            # Успешно использованный challenge нельзя переиспользовать для resend.
            or not user.two_factor_code_hash
        ):
            return "invalid"

        now = datetime.now(UTC)
        if user.two_factor_last_sent_at is not None:
            elapsed = (now - ensure_utc(user.two_factor_last_sent_at)).total_seconds()
            if elapsed < settings.ADMIN_2FA_RESEND_COOLDOWN_SECONDS:
                return "cooldown"

        code = self._generate_two_factor_code()
        user.two_factor_code_hash = self.hash_password(code)
        user.two_factor_expires = now + timedelta(
            minutes=settings.ADMIN_2FA_CODE_TTL_MINUTES,
        )
        user.two_factor_attempts = 0
        user.two_factor_last_sent_at = now
        await self.db.flush()

        if not await self._send_two_factor_code(user, code):
            self.clear_two_factor(user)
            await self.db.commit()
            return "email_failed"
        return "sent"

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
        user = await self.repo.get_by_id(self.db, uid)
        if (
            user is None
            or user.is_banned
            or (not user.is_verified and not settings.email_auth_bypassed)
        ):
            return None
        # Токен должен быть выдан для актуальной версии сессии.
        if payload.get("ver", 0) != user.token_version:
            return None
        return user

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
            self._validate_password(data.new_password)

            user.password_hash = self.hash_password(data.new_password)
            # Смена пароля должна завершать все активные сессии и 2FA-входы.
            self.revoke_sessions(user)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    # ---- Сброс пароля ----

    async def generate_reset_token(self, email: str) -> bool:
        """
        Сгенерировать токен сброса пароля и отправить письмо.

        Всегда возвращает True (не раскрываем, существует ли email).
        """
        user = await self.repo.get_by_email(self.db, self._normalize_email(email))
        if user is None:
            return True  # не раскрываем

        from src.notifications.email import get_email_service

        # В БД храним только HMAC-хеш токена.
        token = secrets.token_urlsafe(32)
        user.reset_token = self.hash_reset_token(token)
        user.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
        await self.db.flush()

        email_service = get_email_service()
        await email_service.send_password_reset(
            email=user.email,
            token=token,
            name=user.name,
            base_url=settings.FRONTEND_URL,
        )
        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Сбросить пароль по токену.

        Returns:
            True при успехе, False если токен недействителен или истёк.
        """
        token_hash = self.hash_reset_token(token)
        result = await self.db.execute(
            select(User).where(User.reset_token == token_hash),
        )
        user = result.scalar_one_or_none()
        if user is None:
            return False

        now = datetime.now(UTC)
        if user.reset_token_expires is None or ensure_utc(user.reset_token_expires) < now:
            # Просроченный токен — очищаем.
            user.reset_token = None
            user.reset_token_expires = None
            await self.db.commit()
            return False

        self._validate_password(new_password)

        user.password_hash = self.hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        # Сброс пароля завершает все активные сессии и незавершённые 2FA-входы.
        self.revoke_sessions(user)
        await self.db.flush()
        return True
