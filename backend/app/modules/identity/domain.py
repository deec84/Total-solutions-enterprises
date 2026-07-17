"""Identity domain entities and ports."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class Role(StrEnum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    email: str
    password_hash: str
    role: Role
    is_active: bool
    is_verified: bool
    created_at: datetime
    mfa_secret: str | None = None
    mfa_enabled: bool = False


@dataclass(frozen=True, slots=True)
class Session:
    id: UUID
    user_id: UUID
    created_at: datetime
    expires_at: datetime


class UserRepository(Protocol):
    async def add(self, user: User) -> None: ...
    async def get_by_email(self, email: str) -> User | None: ...
    async def get_by_id(self, user_id: UUID) -> User | None: ...
    async def mark_verified(self, user_id: UUID) -> User | None: ...
    async def update_password(self, user_id: UUID, password_hash: str) -> User | None: ...
    async def set_mfa(self, user_id: UUID, secret: str, enabled: bool) -> User | None: ...


class SessionRepository(Protocol):
    async def add(self, token_id: UUID, user_id: UUID, expires_at: datetime) -> None: ...
    async def consume(self, token_id: UUID) -> UUID | None: ...
    async def revoke(self, token_id: UUID) -> None: ...
    async def revoke_all(self, user_id: UUID) -> None: ...
    async def list_for_user(self, user_id: UUID) -> tuple[Session, ...]: ...
    async def revoke_for_user(self, token_id: UUID, user_id: UUID) -> bool: ...


class VerificationNotifier(Protocol):
    async def send_email_verification(self, email: str, token: str) -> None: ...
    async def send_password_reset(self, email: str, token: str) -> None: ...
