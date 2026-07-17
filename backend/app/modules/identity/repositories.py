"""Concurrency-safe development adapters; PostgreSQL replaces these in Phase 3."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from app.modules.identity.domain import Session, User


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, User] = {}
        self._by_email: dict[str, UUID] = {}
        self._lock = asyncio.Lock()

    async def add(self, user: User) -> None:
        async with self._lock:
            if user.email in self._by_email:
                raise ValueError("email already registered")
            self._by_id[user.id] = user
            self._by_email[user.email] = user.id

    async def get_by_email(self, email: str) -> User | None:
        user_id = self._by_email.get(email)
        return self._by_id.get(user_id) if user_id else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)

    async def mark_verified(self, user_id: UUID) -> User | None:
        async with self._lock:
            user = self._by_id.get(user_id)
            if user is None:
                return None
            verified = replace(user, is_verified=True)
            self._by_id[user_id] = verified
            return verified

    async def update_password(self, user_id: UUID, password_hash: str) -> User | None:
        async with self._lock:
            user = self._by_id.get(user_id)
            if user is None:
                return None
            updated = replace(user, password_hash=password_hash)
            self._by_id[user_id] = updated
            return updated

    async def set_mfa(self, user_id: UUID, secret: str, enabled: bool) -> User | None:
        async with self._lock:
            user = self._by_id.get(user_id)
            if user is None:
                return None
            updated = replace(user, mfa_secret=secret, mfa_enabled=enabled)
            self._by_id[user_id] = updated
            return updated


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[UUID, Session] = {}
        self._lock = asyncio.Lock()

    async def add(self, token_id: UUID, user_id: UUID, expires_at: datetime) -> None:
        async with self._lock:
            self._sessions[token_id] = Session(token_id, user_id, datetime.now(UTC), expires_at)

    async def consume(self, token_id: UUID) -> UUID | None:
        async with self._lock:
            session = self._sessions.pop(token_id, None)
            if session is None or session.expires_at <= datetime.now(UTC):
                return None
            return session.user_id

    async def revoke(self, token_id: UUID) -> None:
        async with self._lock:
            self._sessions.pop(token_id, None)

    async def revoke_all(self, user_id: UUID) -> None:
        async with self._lock:
            self._sessions = {
                token_id: session
                for token_id, session in self._sessions.items()
                if session.user_id != user_id
            }

    async def list_for_user(self, user_id: UUID) -> tuple[Session, ...]:
        now = datetime.now(UTC)
        async with self._lock:
            return tuple(
                session
                for session in self._sessions.values()
                if session.user_id == user_id and session.expires_at > now
            )

    async def revoke_for_user(self, token_id: UUID, user_id: UUID) -> bool:
        async with self._lock:
            session = self._sessions.get(token_id)
            if session is None or session.user_id != user_id:
                return False
            self._sessions.pop(token_id)
            return True


class InMemoryVerificationNotifier:
    """Test/development outbox; a mail provider adapter replaces it before production."""

    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}
        self._password_reset_tokens: dict[str, str] = {}

    async def send_email_verification(self, email: str, token: str) -> None:
        self._tokens[email] = token

    def token_for(self, email: str) -> str:
        return self._tokens[email]

    async def send_password_reset(self, email: str, token: str) -> None:
        self._password_reset_tokens[email] = token

    def password_reset_token_for(self, email: str) -> str:
        return self._password_reset_tokens[email]
